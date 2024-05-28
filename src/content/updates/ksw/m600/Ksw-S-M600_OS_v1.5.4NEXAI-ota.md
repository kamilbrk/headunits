---
id: "Ksw-S-M600_OS_v1.5.4NEXAI-ota"
vendor: ksw
platform: m600
date: 2023-06-31T01:10:14Z
---
Changes since `Ksw-S-M600_OS_v1.2.1NEXAI-ota`:
- Added Croatian language option (`hr`)
- Added "MCU restart" option
- KswPLauncher (`com.wits.ksw`) app updated from `1.20_230129` to `1.20_230727`
    - Added [`Alfa_Romeo_V2`](../../../themes/ksw/alfa_romeo_v2) theme
    - Added [`UI_MBUX_2021_KSW_1024`](../../../themes/ksw/ui_mbux_2021_ksw_1024) theme
    - Added [`UI_MBUX_2021_KSW_1024_V2`](../../../themes/ksw/ui_mbux_2021_ksw_1024_v2) theme
    - Added [`UI_PEMP_ID8`](../../../themes/ksw/ui_pemp_id8) theme
    - New settings:
    - 360 boot up camera: No camera use, Retrofit camera, Original car camera
    - Turn signal control: Uncontrolled, Controlled
    - MIC external built-in toggle switch: External, Built-in
    - Change in code reporting amount of memory. A hard-coded "4GB" value will be reported on all Android 10.
    - Added unread count bubble (?)
    - Added two more default splash screen images
    - Added native support for iGO maps (`com.nng.igo.*`)
    - Added "CAR INFO" icon in [`BMW_ID8_UI`](../../../themes/ksw/bmw_id8_ui) theme
    - Added handling for equalizer app `com.wits.csp.eq`
    - Added handling for weather app `com.txznet.weather`
- CarplayZlink app updated from `5.3.28` to `5.3.49`
    - Added wireless screen mirroring guidance images
    - Added phone ring volume adjustment
- Added DocumentsUI app
- KswPMedia (`com.wits.ksw.media`) app has been replaced with separate KswPMusic `com.wits.ksw.music` and KswPVideo (`com.wits.ksw.video`) apps
- TXZOta app updated from `3.0.0` to `1.1.3` (yes, lower semver, but higher version code)
    - Added more instructions about OTA upgrade process
- KswAirConditioner (`com.wits.ksw.airc`) app updated from `1.0_221116` to `1.0_230724`
    - Added Audi / Audi MIB3 support
- KugouAuto (KuGou Music) (`com.kugou.android.auto`) app updated from 1.1.7 to 3.5.4
- Center Service (`com.wits.pms`) app updated from `1.0_230111` to `1.0_230726`
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.22_230111_feasy` to `1.0.22_230615_feasy`
