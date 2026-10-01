---
id: "Ksw-R-M600_OS_v1.4.5-ota"
vendor: ksw
platform: m600
android: 11
date: 2021-08-12T05:32:50Z
signatures:
  md5: 4187de13fee162ccb84e1e5fbaab5fbb
  sha1: d9a21a09aa5f89e91c5e13ac7a14c56668536db9
  sha256: e5a6e4dff66c368dd47a50d92f2c4d7dbd708ffc9f0af23cddfed80f9028a1f8
---
#### Summary
- "Clear all" button in the recent apps screen
- Default mobile network mode changes to LTE
- The factory "Launcher's Music App" button is hidden on every theme

#### Changes
- Recent apps: new "Clear all" button next to "Screenshot"
- Default preferred network type changes from `33` (NR/LTE/TD-SCDMA/CDMA/EvDo/GSM/WCDMA) to `11` (LTE only) and `9` (LTE/GSM/WCDMA)
- Android Settings: CDMA and EvDo entries removed from the "Preferred network type" list
- The factory "Launcher's Music App" button on the "Function" page is hidden on every theme, not only on `PEMP_ID7_UI`
- The Wi-Fi hotspot's on/off state is saved on every change, so a hotspot left on should come back on at boot more reliably (not tested)
- Bluetooth: switching back from the car's original system to Android appears to no longer unmute and resume Bluetooth music (not tested)
- Larger-screen layouts: the factory password keypad is rebuilt for `BMW_EVO_ID7`-style settings, `LEXUS_UI` / `LEXUS_LS_UI` get their own factory password screen, and the ID6 and ID7 settings panels are resized
- The app lists behind "Select Music App" / "Select Video App" use slightly smaller icons
