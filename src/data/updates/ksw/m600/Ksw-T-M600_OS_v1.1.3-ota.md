---
id: "Ksw-T-M600_OS_v1.1.3-ota"
vendor: ksw
platform: m600
android: 13
date: 2023-08-31T09:11:06Z
signatures:
  md5: aca293258f40154a669f58f4141a72ec
  sha1: 92ae0daab9d3720b72d5cea8af6134e9eb698a5a
  sha256: d886250718c45695d9981fcfc62abc1ead4a6fe9d3e8d728695c49ca6ae5ad0e
---
Changes since `Ksw-S-M600_OS_v1.5.6NEXAI-ota`:
- KswPLauncher (`com.wits.ksw`)  app updated from `1.20_230810` to `1.20_230830`
    - Work in progress on new versions of existing themes (do not activate):
    - Benz_MBUX2021_KSW_Three
    - Benz_MBUX2021_KSW_V2_Three
    - Various themes support translucent status bar (BMW ID7)
- APKInstaller (`com.wits.apk`) app updated from `1.0_20221126` to `1.0_20230824`
    - Updated with new permissions like `RECEIVE_BOOT_COMPLETED`, `WRITE_EXTERNAL_STORAGE`, `MOUNT_UNMONT_FILESYTEMS`, `CLEAR_APP_CACHE`, `REQUEST_DELETE_PACKAGES`, etc
    - New functionality around updating apps, importing and clearing AW3603D/360CAM files, importing "overseas" and "domestic" files with date/time selection
    - 360CAM files seem to be on `/M600_aw3603D` folder and relates to `com.ivicar.avm` app that does not exist yet (see OTA 1.1.9 above)
- TXZAIPal app removed
- TXZCore app removed
- TXZOverSeaAdapter (`com.txznet.smartadapter`) app `YC-KSW-A-4.0.0` removed
