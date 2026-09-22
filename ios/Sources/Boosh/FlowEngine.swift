//
//  FlowEngine.swift
//  Boosh
//
//  Deterministic flow execution engine — System 0.
//  Port of engine/boosh_flow/engine.py
//

import Foundation

// MARK: - Types

public struct Flow: Codable {
    public let name: String
    public let vendor: String
    public let entryURL: String
    public let version: Int
    public let spends: Bool
    public let thresholds: Thresholds
    public let pages: [PageSpec]
    
    enum CodingKeys: String, CodingKey {
        case name, vendor, version, spends, thresholds, pages
        case entryURL = "entry_url"
    }
}

public struct Thresholds: Codable {
    public let act: Double
    public let confirm: Double
}

public struct PageSpec: Codable {
    public let name: String
    public let match: MatchSpec
    public let steps: [Step]
}

public struct MatchSpec: Codable {
    public let urlHost: String?
    public let urlContains: String?
    public let anchors: [Anchor]
    
    enum CodingKeys: String, CodingKey {
        case urlHost = "url_host"
        case urlContains = "url_contains"
        case anchors
    }
}

public struct Anchor: Codable {
    public let selector: String?
    public let text: String?
    public let weight: Double
}

public struct Step: Codable {
    public let action: String
    public let params: [String: String]
}

public enum FlowEvent {
    case pageMatched(page: String, confidence: Double)
    case pageUnrecognized(url: String)
    case read(key: String, value: String)
    case gatePassed(gate: String, detail: String)
    case gateFailed(gate: String, detail: String)
    case approvalRequired(message: String)
    case approvalResult(approved: Bool)
    case flowComplete
    case flowAborted(reason: String)
}

// MARK: - Browser Driver Protocol

public protocol BrowserDriver {
    func goto(_ url: String) async throws
    func snapshot() async throws -> PageSnapshot
    func fill(_ selector: String, value: String) async throws
    func click(selector: String?, text: String?) async throws
    func readText(_ selector: String) async throws -> String
}

public struct PageSnapshot {
    public let url: String
    public let elements: [Element]
    
    public struct Element {
        public let selector: String?
        public let text: String?
        public let value: String?
    }
}

// MARK: - Flow Engine

public actor FlowEngine {
    private let driver: BrowserDriver
    private let approver: (String) async -> Bool
    private var context: [String: Any] = [:]
    
    public init(driver: BrowserDriver, approver: @escaping (String) async -> Bool) {
        self.driver = driver
        self.approver = approver
    }
    
    public func run(_ flow: Flow) async -> [FlowEvent] {
        var events: [FlowEvent] = []
        
        // Navigate to entry URL
        do {
            try await driver.goto(flow.entryURL)
        } catch {
            events.append(.flowAborted(reason: "navigation_failed"))
            return events
        }
        
        // Execute pages in order
        for page in flow.pages {
            // Check if current page matches
            let snapshot = try? await driver.snapshot()
            guard let snapshot = snapshot else {
                events.append(.flowAborted(reason: "snapshot_failed"))
                return events
            }
            
            let confidence = pageConfidence(snapshot: snapshot, page: page)
            
            if confidence < flow.thresholds.confirm {
                events.append(.pageUnrecognized(url: snapshot.url))
                events.append(.flowAborted(reason: "page_unrecognized"))
                return events
            }
            
            events.append(.pageMatched(page: page.name, confidence: confidence))
            
            // Execute steps
            for step in page.steps {
                let result = await executeStep(step, flow: flow, events: &events)
                if result == .aborted {
                    return events
                } else if result == .completed {
                    events.append(.flowComplete)
                    return events
                }
            }
        }
        
        events.append(.flowComplete)
        return events
    }
    
    private func pageConfidence(snapshot: PageSnapshot, page: PageSpec) -> Double {
        guard let host = URL(string: snapshot.url)?.host else { return 0.0 }
        
        // Hard gate: host must match
        if let expectedHost = page.match.urlHost, host != expectedHost {
            return 0.0
        }
        
        // Hard gate: path must contain required substring
        if let pathContains = page.match.urlContains {
            guard snapshot.url.contains(pathContains) else { return 0.0 }
        }
        
        // Score anchors
        let totalWeight = page.match.anchors.reduce(0.0) { $0 + $1.weight }
        guard totalWeight > 0 else { return 1.0 }
        
        var hitWeight = 0.0
        for anchor in page.match.anchors {
            let matched = snapshot.elements.contains { element in
                if let selector = anchor.selector, element.selector == selector {
                    return true
                }
                if let text = anchor.text, element.text?.localizedCaseInsensitiveContains(text) == true {
                    return true
                }
                return false
            }
            if matched {
                hitWeight += anchor.weight
            }
        }
        
        return hitWeight / totalWeight
    }
    
    private func executeStep(_ step: Step, flow: Flow, events: inout [FlowEvent]) async -> StepResult {
        switch step.action {
        case "fill":
            guard let selector = step.params["selector"],
                  let value = resolve(step.params["value"] ?? "", context: context) else {
                events.append(.flowAborted(reason: "invalid_fill_params"))
                return .aborted
            }
            try? await driver.fill(selector, value: value)
            
        case "click":
            let selector = step.params["selector"]
            let text = step.params["text"]
            try? await driver.click(selector: selector, text: text)
            
        case "read":
            guard let selector = step.params["selector"],
                  let key = step.params["as"] else {
                events.append(.flowAborted(reason: "invalid_read_params"))
                return .aborted
            }
            let value = (try? await driver.readText(selector)) ?? ""
            context[key] = value
            events.append(.read(key: key, value: value))
            
        case "wait":
            // Real driver waits for page stability
            try? await Task.sleep(nanoseconds: 500_000_000)
            
        case "gate":
            guard let gateType = step.params["type"] else {
                events.append(.flowAborted(reason: "invalid_gate_params"))
                return .aborted
            }
            let (passed, detail) = evaluateGate(type: gateType, params: step.params, context: context)
            if passed {
                events.append(.gatePassed(gate: gateType, detail: detail))
            } else {
                events.append(.gateFailed(gate: gateType, detail: detail))
                events.append(.flowAborted(reason: "gate_failed"))
                return .aborted
            }
            
        case "confirm":
            let message = resolve(step.params["message"] ?? "Confirm?", context: context) ?? "Confirm?"
            events.append(.approvalRequired(message: message))
            let approved = await approver(message)
            events.append(.approvalResult(approved: approved))
            if !approved {
                events.append(.flowAborted(reason: "approval_denied"))
                return .aborted
            }
            
        case "complete":
            return .completed
            
        default:
            events.append(.flowAborted(reason: "unknown_action:\(step.action)"))
            return .aborted
        }
        
        return .continue
    }
    
    private func resolve(_ template: String, context: [String: Any]) -> String? {
        guard template.hasPrefix("$") else { return template }
        let path = String(template.dropFirst())
        let components = path.split(separator: ".").map(String.init)
        
        var current: Any? = context
        for component in components {
            if let dict = current as? [String: Any] {
                current = dict[component]
            } else {
                return nil
            }
        }
        return current as? String
    }
    
    private func evaluateGate(type: String, params: [String: String], context: [String: Any]) -> (Bool, String) {
        switch type {
        case "amount_sanity":
            guard let valueKey = params["value_key"],
                  let lastKey = params["last_key"],
                  let valueStr = context[valueKey] as? String,
                  let lastStr = context[lastKey] as? String,
                  let value = parseAmount(valueStr),
                  let last = parseAmount(lastStr) else {
                return (false, "missing_amount_data")
            }
            let tolerance = Double(params["within_pct"] ?? "15.0") ?? 15.0
            let diff = abs(value - last) / last * 100
            return (diff <= tolerance, String(format: "%.2f vs %.2f (%.1f%%)", value, last, diff))
            
        default:
            return (false, "unknown_gate_type")
        }
    }
    
    private func parseAmount(_ text: String) -> Double? {
        let cleaned = text.replacingOccurrences(of: "$", with: "")
            .replacingOccurrences(of: ",", with: "")
            .trimmingCharacters(in: .whitespaces)
        return Double(cleaned)
    }
    
    private enum StepResult {
        case `continue`
        case aborted
        case completed
    }
}

// MARK: - Flow Loading

public enum FlowLoader {
    public static func load(from url: URL) throws -> Flow {
        let data = try Data(contentsOf: url)
        return try JSONDecoder().decode(Flow.self, from: data)
    }
    
    public static func load(from string: String) throws -> Flow {
        guard let data = string.data(using: .utf8) else {
            throw FlowError.invalidJSON
        }
        return try JSONDecoder().decode(Flow.self, from: data)
    }
}

public enum FlowError: Error {
    case invalidJSON
    case flowNotFound
}
