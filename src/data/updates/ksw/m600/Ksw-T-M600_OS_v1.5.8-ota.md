---
id: "Ksw-T-M600_OS_v1.5.8-ota"
vendor: ksw
platform: m600
android: 13
date: 2024-03-18T01:47:35Z
signatures:
  md5: 7985fe505770b9668dfa087cd29e9f0e
  sha1: e9eb66a1ed82171b441ff6b141030b99ccc3d788
  sha256: 02f0bb9685727990462e2523e6934ed5eb3094c715140f4a5edda46df73bdd94
---
Summary:
- Upcoming support for SD685 platform, which will be shown as "M785"

Changes since `Ksw-T-M600_OS_v1.5.5-ota` built 17 days earlier:
- Zlink: Updated to `5.4.34`
- Ksw360Camera: Updated to `1.0.1_240314`, new feature to automatically start/stop recording when external storage is mounted/ejected
- KswPLauncher: Updated to `1.20_240314`, no longer set to `testOnly` mode, introduced logic to show `M785` in the version string on SD685 platform