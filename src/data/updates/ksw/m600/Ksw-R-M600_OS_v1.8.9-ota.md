---
id: "Ksw-R-M600_OS_v1.8.9-ota"
vendor: ksw
platform: m600
android: 11
date: 2021-12-23T02:13:19Z
signatures:
  md5: af1427fefedf90123bbc31d3aee255f7
  sha1: 3d3006306198a15bf2c14f6e285b578eeca4194c
  sha256: 115f2fefccceebb20c3a7e149bfc2f0f53b949fd234159d946bb24142c33f312
---
#### Summary
- The air-conditioning popup gets back °F and the per-manufacturer hide check that `1.8.6` dropped
- TXZ voice assistant apps are hidden from the app list when "Txzing Assistant" is off
- `ALS_ID7_UI` changes: new skin picker, new in-call dial pad, skins applied across KswBt

#### Changes
- Air-conditioning popup: temperatures are shown in °F again when the unit is set to Fahrenheit. In °F mode the right-hand temperature appears to be written into the left-hand field (not tested)
- Air-conditioning popup: never shown when the factory car manufacturer is BMW or Audi, otherwise follows the factory "Air Conditioner" checkbox, as before `1.8.6`. The Lexus climate screen is still missing until `1.9.0`
- The app list hides the TXZ voice assistant apps when "Txzing Assistant" (`Support_TXZ` in [factory_config.xml](/factory-settings/ksw)) is off
- "Disable Video In Motion" in the factory "Function" page is also shown on `ALS_ID6_UI`
- Benz NTG6-style settings: the time shown follows the 12/24-hour setting
- `ALS_ID7_UI` home: a long press on the skin tile shows an inline blue/yellow/red skin bar instead of a popup
- `ALS_ID7_UI` Bluetooth: the chosen skin is applied as soon as the app starts, and the in-call dial pad is replaced by what appears to be a rotary dial pad
- `ALS_ID7_UI` music: the music and video lists and the play screen are restyled
- The default skin is set to blue when the system settings are first created
- Zlink (`com.zjinnova.zlink`) app updated from `5.2.0` to `5.2.14`
  - New "The MFI chip is not detected" message, a "Recommend to use the 5G hotspot" hint and Latin American Spanish
- TXZ voice assistant adapter updated from `211111-59` to `211203-76`
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.21_1117` to `1.0.21_1221`
