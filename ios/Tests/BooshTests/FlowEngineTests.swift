//
//  FlowEngineTests.swift
//  BooshTests
//
//  Tests for the deterministic flow engine.
//

import XCTest
@testable import Boosh

final class FlowEngineTests: XCTestCase {
    
    // MARK: - Test Fixtures
    
    func makeLoginPage() -> PageSnapshot {
        PageSnapshot(
            url: "https://www.consumersenergy.com/login",
            elements: [
                .init(selector: "#username", text: nil, value: nil),
                .init(selector: "#password", text: nil, value: nil),
                .init(selector: nil, text: "Sign in", value: nil),
                .init(selector: nil, text: "Email", value: nil),
                .init(selector: nil, text: "Password", value: nil),
            ]
        )
    }
    
    func makeDashboardPage() -> PageSnapshot {
        PageSnapshot(
            url: "https://www.consumersenergy.com/account",
            elements: [
                .init(selector: nil, text: "Account Summary", value: nil),
                .init(selector: nil, text: "Pay Bill", value: nil),
                .init(selector: nil, text: "Amount Due", value: nil),
                .init(selector: ".amount-due", text: nil, value: "$86.90"),
            ]
        )
    }
    
    func makeReviewPage() -> PageSnapshot {
        PageSnapshot(
            url: "https://www.consumersenergy.com/pay",
            elements: [
                .init(selector: nil, text: "Review Payment", value: nil),
                .init(selector: nil, text: "Pay $86.90", value: nil),
                .init(selector: nil, text: "Confirm", value: nil),
            ]
        )
    }
    
    // MARK: - Mock Driver
    
    actor MockDriver: BrowserDriver {
        var currentPage: PageSnapshot
        var filled: [String: String] = [:]
        var clicked: [String] = []
        
        init(initialPage: PageSnapshot) {
            self.currentPage = initialPage
        }
        
        func goto(_ url: String) async throws {
            // Navigation handled by test setup
        }
        
        func snapshot() async throws -> PageSnapshot {
            currentPage
        }
        
        func fill(_ selector: String, value: String) async throws {
            filled[selector] = value
        }
        
        func click(selector: String?, text: String?) async throws {
            clicked.append(selector ?? text ?? "unknown")
        }
        
        func readText(_ selector: String) async throws -> String {
            if selector == ".amount-due" {
                return "$86.90"
            }
            return ""
        }
        
        func setPage(_ page: PageSnapshot) {
            currentPage = page
        }
    }
    
    // MARK: - Tests
    
    func testPageMatching() async throws {
        let flow = try FlowLoader.load(from: """
        {
            "name": "Test Flow",
            "vendor": "Test",
            "entry_url": "https://example.com",
            "version": 1,
            "spends": false,
            "thresholds": {"act": 0.85, "confirm": 0.5},
            "pages": [
                {
                    "name": "login",
                    "match": {
                        "url_host": "www.consumersenergy.com",
                        "url_contains": "/login",
                        "anchors": [
                            {"selector": "#username", "weight": 3},
                            {"selector": "#password", "weight": 3},
                            {"text": "Sign in", "weight": 2}
                        ]
                    },
                    "steps": []
                }
            ]
        }
        """)
        
        let driver = MockDriver(initialPage: makeLoginPage())
        let engine = FlowEngine(driver: driver) { _ in true }
        
        let events = await engine.run(flow)
        
        guard case .pageMatched(let page, let confidence) = events.first else {
            XCTFail("Expected pageMatched event")
            return
        }
        
        XCTAssertEqual(page, "login")
        XCTAssertEqual(confidence, 1.0, accuracy: 0.01)
    }
    
    func testWrongHostAborts() async throws {
        let flow = try FlowLoader.load(from: """
        {
            "name": "Test Flow",
            "vendor": "Test",
            "entry_url": "https://example.com",
            "version": 1,
            "spends": false,
            "thresholds": {"act": 0.85, "confirm": 0.5},
            "pages": [
                {
                    "name": "login",
                    "match": {
                        "url_host": "www.consumersenergy.com",
                        "url_contains": "/login",
                        "anchors": [
                            {"selector": "#username", "weight": 3}
                        ]
                    },
                    "steps": []
                }
            ]
        }
        """)
        
        let phishingPage = PageSnapshot(
            url: "https://consumers-energy-billing.com/login",
            elements: makeLoginPage().elements
        )
        
        let driver = MockDriver(initialPage: phishingPage)
        let engine = FlowEngine(driver: driver) { _ in true }
        
        let events = await engine.run(flow)
        
        guard case .flowAborted(let reason) = events.last else {
            XCTFail("Expected flowAborted event")
            return
        }
        
        XCTAssertEqual(reason, "page_unrecognized")
    }
    
    func testApprovalGate() async throws {
        let flow = try FlowLoader.load(from: """
        {
            "name": "Test Flow",
            "vendor": "Test",
            "entry_url": "https://example.com",
            "version": 1,
            "spends": true,
            "thresholds": {"act": 0.85, "confirm": 0.5},
            "pages": [
                {
                    "name": "review",
                    "match": {
                        "url_host": "www.consumersenergy.com",
                        "url_contains": "/pay",
                        "anchors": [
                            {"text": "Review Payment", "weight": 3}
                        ]
                    },
                    "steps": [
                        {"action": "confirm", "params": {"message": "Pay $86.90?"}}
                    ]
                }
            ]
        }
        """)
        
        let driver = MockDriver(initialPage: makeReviewPage())
        
        // Test approval denied
        let engineDenied = FlowEngine(driver: driver) { _ in false }
        let eventsDenied = await engineDenied.run(flow)
        
        guard case .flowAborted(let reason) = eventsDenied.last else {
            XCTFail("Expected flowAborted on denial")
            return
        }
        XCTAssertEqual(reason, "approval_denied")
        
        // Test approval granted
        let driver2 = MockDriver(initialPage: makeReviewPage())
        let engineApproved = FlowEngine(driver: driver2) { _ in true }
        let eventsApproved = await engineApproved.run(flow)
        
        guard case .flowComplete = eventsApproved.last else {
            XCTFail("Expected flowComplete on approval")
            return
        }
    }
    
    func testAmountSanityGate() async throws {
        let flow = try FlowLoader.load(from: """
        {
            "name": "Test Flow",
            "vendor": "Test",
            "entry_url": "https://example.com",
            "version": 1,
            "spends": true,
            "thresholds": {"act": 0.85, "confirm": 0.5},
            "pages": [
                {
                    "name": "dashboard",
                    "match": {
                        "url_host": "www.consumersenergy.com",
                        "url_contains": "/account",
                        "anchors": [
                            {"text": "Account Summary", "weight": 3}
                        ]
                    },
                    "steps": [
                        {"action": "read", "params": {"selector": ".amount-due", "as": "amount"}},
                        {"action": "gate", "params": {"type": "amount_sanity", "value_key": "amount", "last_key": "last_amount", "within_pct": "15.0"}}
                    ]
                }
            ]
        }
        """)
        
        let driver = MockDriver(initialPage: makeDashboardPage())
        let engine = FlowEngine(driver: driver) { _ in true }
        
        // Set up context with baseline
        // Note: In real usage, context would be passed to run()
        // For this test, we verify the gate fails without proper baseline
        
        let events = await engine.run(flow)
        
        // Should abort at gate due to missing baseline
        let hasGateFailed = events.contains { event in
            if case .gateFailed = event { return true }
            return false
        }
        XCTAssertTrue(hasGateFailed)
    }
}
