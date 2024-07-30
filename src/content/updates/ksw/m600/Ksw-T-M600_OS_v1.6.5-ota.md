---
id: "Ksw-T-M600_OS_v1.6.5-ota"
vendor: ksw
platform: m600
android: 13
date: 2024-07-12T02:33:08Z
signatures:
  md5: d06231fe667f4fd65528d4552fd0f91f
  sha1: 79e79d53e8f2a4c4c7dc04543bf009605603c95b
  sha256: 5311a54971f39366d452948e10c6f1631d9ed3b6c6709753e0071aff6cd6735e
---
Summary:
- Zlink updated to `5.4.53`
- CPU information now shown in settings with "M606" label for SD460/SM4250
- Further support for the new [`UI_NTG6_FY_V3`](/headunits/themes/ksw/ui_ntg6_fy_v3) theme

Changes since `Ksw-T-M600_OS_v1.6.1-ota` built 77 days earlier:
- Zlink app updated from `5.4.34` to `5.4.53`: there's a `Free_version` file inside with a value of `0` and app manifest has a new `AAOrCPEnable` flag set to `false`
- APKInstaller app updated: new functionality to receive app updates (?)
- KswPLauncher app updated: added CPU information text on most themes to show one of M600, M606, M700 or M785. The `M606` label is new and it's for the Qualcomm Snapdragon 460 (SM4250 SM_KAMORTA) platform.
- kswEq app updated: ablility to automatically enable equalizer
- The [`UI_NTG6_FY_V3`](/headunits/themes/ksw/ui_ntg6_fy_v3) theme should be now supported in more apps like Bluetooth, Music, Video and Equalizer
- CenterService app updated: seems like M785 platform can get their own OTA updates after all, since the filenames can contain `M785_OS_v` string. There's also potential support for automatically toggling dark mode and further improvements for Huawei HiCar integration
- Updated the red and yellow skins across all media apps (bluetooth, music, video, equalizer, etc)