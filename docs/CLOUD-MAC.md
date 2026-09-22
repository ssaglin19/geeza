# Cloud Mac Strategy for iOS MVP

## Objective
Build and test a small iOS MVP from a Windows laptop by renting a cloud Mac first, then decide whether buying a Mac mini is worthwhile.

## Recommended approach
Use a managed, interactive cloud Mac rather than a CI-only build service. Build most of the cross-platform app on the Windows laptop, then use the rented Mac for Xcode, iOS builds, signing, simulator testing, and TestFlight preparation.

## Provider comparison

| Provider | Starting Price | Apple Silicon | Persistent Storage | Remote Desktop | Notes |
|----------|---------------|---------------|-------------------|----------------|-------|
| **MacinCloud** | ~$30-50/mo | M1/M2 available | Yes, on dedicated plans | Yes | Cheapest entry, shared/dedicated options |
| **MacStadium** | ~$50-100/mo | M1/M2/M4 available | Yes, dedicated | Yes | Most reliable, best support, US/EU data centers |
| **Rent a Mac** | ~$40-80/mo | M1 available | Yes | Yes | Smaller provider, good pricing |
| **AWS EC2 Mac** | ~$1.08/hr (~$780/mo) | M1/M2 available | EBS volumes | No (SSH only) | Overkill for MVP, CI-focused |

**Recommendation:** Start with **MacinCloud** (cheapest) or **MacStadium** (most reliable). Both offer persistent Apple Silicon Macs with remote desktop. Avoid AWS for MVP.

## Prerequisites

- A Windows laptop
- An Apple ID
- An iPhone if real-device testing is needed
- A GitHub or other remote Git repository
- A small test budget for the cloud Mac
- An Apple Developer account if installing on a physical device, using TestFlight, or distributing through the App Store

The Apple Developer Program may be required for device distribution and App Store/TestFlight workflows. Confirm Apple's current fee and enrollment requirements directly before paying.

## Setup sequence

1. Choose a managed cloud Mac with interactive remote-desktop access. Prefer Apple Silicon if available because it better matches current Mac development and simulator performance.

2. Create the provider account, select a macOS image with a compatible Xcode version, and confirm whether the machine is dedicated or shared. Check that the workspace persists between sessions.

3. Connect from Windows using the provider's remote-desktop application or browser client. If the provider requires an initial setup session, complete that first.

4. Sign in to the Mac with the Apple ID that will own the development project. Keep two-factor authentication available. Never paste passwords or verification codes into the project files or chat.

5. Install Xcode from the App Store or the provider-approved installation route. Open it once so Xcode can install its required components and accept its license.

6. Install the project toolchain required by the app:
   - Git
   - Homebrew, if needed
   - Swift Package Manager, CocoaPods, Flutter, React Native, or other framework dependencies
   - Any simulator runtimes required by the target iOS version

7. Clone the project from the remote repository. Keep source code, configuration templates, and documentation in version control. Do not rely on the rented Mac as the only copy.

8. Build a deliberately small vertical slice first: launch screen, navigation, one core workflow, basic data/API path, and error handling. Avoid building the whole product before testing whether the MVP is useful.

9. Run the app in the iOS Simulator. Test layout, navigation, API calls, login, permissions, and basic state handling. Expect remote display latency, especially during simulator animation or video-heavy work.

10. If an iPhone is available, test on the physical device. The simulator cannot fully reveal camera, Bluetooth, notifications, sensors, battery behavior, performance, or every permission issue.

11. For TestFlight or App Store distribution, configure signing and provisioning through Xcode and the Apple Developer account. Treat certificates, provisioning profiles, and App Store credentials as sensitive. Do not commit them to Git.

12. Record the MVP result in the repository: what worked, what failed, device and simulator versions, screenshots, known limitations, and the next decision.

13. If the MVP earns continued development, move the same repository to a physical Mac mini later. If not, cancel the cloud Mac and retain the project, build notes, and test results.

## Practical limitations

- A cloud Mac is not the same as owning a Mac. Network latency affects Xcode, simulator interaction, and debugging.
- Provider session persistence varies. Confirm whether files and installed tools survive stopping or restarting the machine.
- A cloud Mac is useful for simulator testing, but physical iPhone testing still requires an iPhone and a supported connection or distribution route.
- Hardware-dependent features need real-device testing.
- Xcode and macOS versions must be compatible with the iOS deployment target and the project's dependencies.
- Keep the project in Git and back up important signing and configuration material securely.
- Building Android first does not replace the Mac portion. It can reduce the time spent on macOS, but iOS compilation, signing, simulator testing, and release work still require macOS/Xcode.

## Decision rule

Rent first if the goal is to validate the MVP and macOS use will be occasional. Buy a Mac mini later if development becomes weekly or continuous and the accumulated rental cost approaches the price of a used Apple Silicon Mac mini. The rental is a validation expense, not a commitment to a permanent cloud setup.

## Provider comparison (researched 2026-09)

| Provider | Entry Price | Apple Silicon | Persistent | Remote Desktop | Best For |
|----------|-------------|---------------|------------|----------------|----------|
| **MacinCloud** | ~$20-50/mo (VM), ~$179/mo (dedicated) | M1/M2 available | Yes, on dedicated plans | Yes | **Cheapest entry, occasional use** |
| **MacStadium** | ~$109/mo (M2), ~$119/mo (M4) | M2/M4 available | Yes, dedicated | Yes | **Enterprise, CI/CD, reliability** |
| **My Remote Mac** | ~$85/mo (M4) | M4 available | Yes | VNC/SSH | **Budget dedicated, solo devs** |
| **AWS EC2 Mac** | ~$1.08/hr (~$780/mo) | M2 only (no M4) | EBS volumes | No (SSH only) | **AWS-native teams, CI fleets** |
| **Scaleway** | ~$219/mo (M4 Pro) | M1-M4 Pro | Yes | DIY VNC | **EU jurisdiction, GDPR** |

**Recommendation for Boosh:** Start with **MacinCloud's cheapest plan that supports Xcode**. If the MVP validates and usage becomes weekly, upgrade to dedicated or buy the Mac mini. Avoid AWS (24-hour minimum, no M4, SSH-only).

**Note:** Both MacinCloud and MacStadium require contacting sales for exact pricing. The figures above are from third-party comparisons and may vary.

## Agent handoff instructions

When continuing this project:

- Preserve the goal: validate an iOS MVP before buying a Mac mini.
- Prefer the cheapest persistent interactive Apple Silicon cloud Mac that supports the required Xcode version.
- Compare current provider pricing and terms before recommending a subscription.
- Keep all source code in the remote Git repository.
- Do not claim the app works until it has been built and tested.
- Separate simulator results from physical-iPhone results.
- Do not claim App Store or TestFlight readiness until signing, provisioning, and an actual build have been verified.
- Stop and ask the owner before paid upgrades, publishing, or other irreversible external actions.
