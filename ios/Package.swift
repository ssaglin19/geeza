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
        // MLX Swift for on-device LLM inference
        // Note: We'll switch to PrismML-Eng/mlx-swift fork when integrating Bonsai ternary weights
        .package(url: "https://github.com/ml-explore/mlx-swift", from: "0.21.0"),
    ],
    targets: [
        .target(
            name: "Boosh",
            dependencies: [
                .product(name: "MLX", package: "mlx-swift"),
                .product(name: "MLXLLM", package: "mlx-swift"),
                .product(name: "MLXLMCommon", package: "mlx-swift"),
            ],
            path: "Sources/Boosh"
        ),
        .testTarget(
            name: "BooshTests",
            dependencies: ["Boosh"],
            path: "Tests/BooshTests"
        ),
    ]
)
