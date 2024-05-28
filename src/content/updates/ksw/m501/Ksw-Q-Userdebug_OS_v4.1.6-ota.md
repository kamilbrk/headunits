---
id: "Ksw-Q-Userdebug_OS_v4.1.6-ota"
vendor: ksw
platform: m501
date: 2023-07-17T05:58:17Z
---
Changes since `Ksw-Q-Userdebug_OS_v4.0.7-ota`
- CarplayZlink (`com.zjinnova.zlink`) app updated from `5.3.24` to `5.4.2`
    - Added labels for "Echo cancellation" (with 3 algorithms to choose from), "Noise reduction" and "Ring volume adjustment"
- APKInstaller (`com.wits.apk`) app updated from `1.0_20221126` to `1.0_20230710`
- KswPMedia (`com.wits.ksw.media`) app has been replaced with separate KswPMusic `com.wits.ksw.music` and KswPVideo (`com.wits.ksw.video`) apps
- KswPLauncher (`com.wits.ksw`) app updated from `1.20_230323` to `1.20_230710`
    - Added [UI_PEMP_ID8](../../../themes/ksw/ui_pemp_id8) theme
    - Support for KswPMusic and KswPVideo video apps in place of KswPMedia
    - Observing top/foreground app state
    - Added handling for split Music/Video apps in place of old Media app
    - Added handling for 360 boot up camera, global weather app, turn signal control, "mic external built-in toggle switch"
- ksqEq (`com.wits.csp.eq`) app updated from `1.01_230323` app `1.01_230629`
    - Added support for [UI_PEMP_ID8](../../../themes/ksw/ui_pemp_id8) theme
    - Added support for [UI_MIB3_V2](../../../themes/ksw/ui_mib3_v2) theme
- TXZAdapter (`com.txznet.adapter`) app is now installed automatically (?)
- Added two additional default, KSW-themed boot logos
- CenterService (`com.wits.pms`) app updated from `1.0_221213` to `1.0_230715`
    - Added a silent package installer module
    - Added MCU reboot option
    - Added internal code and checks for Android 13 based firmware
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.22_230323_goc` to `1.0.22_230710_goc`
- TXZOta (`com.txznet.ota`) app updated from `3.0.0` (version code `1`) to `1.1.2` (version code `101020`)
    - OTA firmware upgrade app, with a full user interface, same as in Android 12/13 versions
