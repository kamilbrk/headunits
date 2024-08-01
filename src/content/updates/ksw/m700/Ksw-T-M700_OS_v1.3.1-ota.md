---
id: "Ksw-T-M700_OS_v1.3.1-ota"
vendor: ksw
platform: m700
android: 13
date: 2024-05-16T03:27:59Z
signatures:
  md5: afff5f225da521b0cf697d9cd02e8b57
  sha1: e295e6c81e055efa802aafb852083cac1c47abea
  sha256: 814059eb72a5aba3c7e480e9e7da5f5fbced972d9710e66307becd8bdcc63be8
---
Summary:
- Updates that were also present in recent [M600](/headunits/updates/ksw) builds, since they're both coming from the same source. Expect roughly the same changes as between [M600 1.4.2](/headunits/updates/ksw/m600/ksw-t-m600_os_v142-ota) and [M600 1.6.1](/headunits/updates/ksw/m600/ksw-t-m600_os_v161-ota).
- Some references to a potentially new "M610" platform

Changes since `Ksw-T-M700_OS_v1.1.5-ota` built 5 months earlier:
- Zlink: Updated to `5.4.34`, same as [M600 1.5.8](/headunits/updates/ksw/m600/ksw-t-m600_os_v158-ota)
- Ksw360Camera: Removed some labels to do with activation process
- APKInstaller: Added ability to check versions and update apps, although only on devices with `M610` in their version string
- KswPLauncher: Added more graphics, labels and functionality for [`UI_NTG6_FY_V3`](/headunits/themes/ksw/ui_ntg6_fy_v3) theme, including ability to change wallpaper, display temperature, etc.
- KswBt (Bluetooth app): Fixes around displaying contact book, caller name and properly finishing call activity
- Launcher3QuickStep: Potential changes to recent apps and split views
- Added more French translations
- Sound settings are now hidden (?)

Changes since `Ksw-T-M600_OS_v1.6.1-ota` built 20 days earlier:
- KswBt (Bluetooth app): Fixes around displaying caller name
- Added more French translations
