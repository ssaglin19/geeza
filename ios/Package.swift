// swift-tools-version: 6.0
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "Boosh",
    platforms: [
        .iOS(.v17)
    ],
    products: [
        .library(
            name: "Boosh",
            targets: ["Boosh"])
    ],
    dependencies: [
        // No external dependencies for the flow engine core
        // MLX will be added when integrating Bonsai for on-device inference
    ],
    targets: [
        .target(
            name: "Boosh",
            dependencies: [],
            path: "Sources/Boosh"
        ),
        .testTarget(
            name: "BooshTests",
            dependencies: ["Boosh"],
            path: "Tests/BooshTests"
        ),
    ]
)
