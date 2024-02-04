---
id: "Ksw-Q-Userdebug_OS_v4.2.0-ota"
platform: "m501"
date: "2023-09-08T04:03:22Z"
signatures:
  md5: 4a407c662cae405dc12a7d4104b46714
  sha1: 87c4a3943c91ee7af83d638dc318df775044359a
  sha256: cfa48401373ab3211a41b89d082663297ea37ea4644476b0e692f076d7a9ee3f
---
Changes since `Ksw-Q-Userdebug_OS_v4.1.6-ota`
- KswAirConditioner (`com.wits.ksw.airc`) app updated from `1.0` to `1.0_230803`
    - Added support for Audi_MMI_4G, Audi_mib3, Audi_mib3_FY, Audi_mib3_FY_V2, Audi_mib3_ty, Benz and UI_mib3_v2 themes
- KswPLauncher (`com.wits.ksw`) app updated from `1.20_230710` to `1.20_230907`
    - Added support for 360 camera (`com.ivicar.avm`) app
- Framework
    - Added new labels
        - `failed_split_screen` Split screen mutually exclusive
        - `failed_split_screen_app` App does not support split-screen.
- CenterService (`com.wits.pms`) app updated from `1.0_230715` to `1.0_230726`
    - Optimisations to OTA update file handling (e.g. closing streams, etc.)
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.22_230710_goc` to `1.0.22_230816_goc`
    - Support for translucent status bar
    - Updates to connection state handling
- TXZOta (`com.txznet.ota`) app updated from `1.1.2` to `1.1.3`
- Settings app updated
    - Added new labels for "CPU info", "Memory total size" and `qualcomm_chip_type` being "Qualcomm Snapdragon 450 (SDM450), 8-core 1.8GHz, Cortex-A53"
