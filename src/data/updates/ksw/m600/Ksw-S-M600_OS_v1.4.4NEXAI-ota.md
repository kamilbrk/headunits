---
id: "Ksw-S-M600_OS_v1.4.4NEXAI-ota"
vendor: ksw
platform: m600
android: 12
date: 2023-05-26T08:32:00Z
signatures:
  md5: 0ca3198a2cd88cb2ea5e8e150feba192
  sha1: c9e080e5ba322f4827ff6f5a0170653e18f430d8
  sha256: 8d4de00c3eb842217a7ba89ca6e67bafdae3d05041bbc7baf435638c6df9dc26
---
#### Summary
- Audi-style air conditioning popup for the Audi themes
- Croatian language option (`hr`)
- "Global Weather App" factory setting is on by default

#### Changes
- KswAirConditioner (`com.wits.ksw.airc`) app updated from `1.0_221116` to `1.0_230526`
  - New full-screen air conditioning popup for the Audi themes, with an animated fan and seat heating and cooling levels; it closes after 3 seconds instead of 5
- CenterService (`com.wits.pms`) app updated from `1.0_230420` to `1.0_230519`
  - Added Croatian language option (`hr`)
- "Global Weather App" is switched on at boot if it has never been set
- A fresh settings database starts with `BMW_ID8_UI` as the theme, unless the factory config sets another one (not tested)
- KswPLauncher (`com.wits.ksw`) app updated from `1.20_230510` to `1.20_230526_1`
  - With "Google Apps" off, Google Maps, Play Store, Google and Google Assistant are hidden from the `LEXUS_LS_UI` / `LEXUS_LS_UI_V2` app list
  - Choosing a navigation app in the theme settings also appears to set the map shown on the home screen
- KswPVideo (`com.wits.ksw.video`) app updated from `1.2_230510` to `1.2_230524`
  - The external "close video" command appears to pause instead of stopping the player
- KswPMusic (`com.wits.ksw.music`) app updated from `1.2_230510` to `1.2_230524`
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.22_230510_feasy` to `1.0.22_230517_feasy`
- Bluetooth stack config turns on the GATT client (`GATT_ENABLE=2`) and adds `HICAR_ENABLE=1`
- TXZOta (`com.txznet.ota`) app changed from `3.0.0` to `1.1.2`
