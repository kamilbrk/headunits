---
id: "Ksw-S-M600_OS_v1.3.0NEXAI-ota"
vendor: ksw
platform: m600
android: 12
date: 2023-03-16T03:51:50Z
signatures:
  md5: f497dfcfc613448104b1aa02d8d5d244
  sha1: bfa14c01fb4a8d59e61632419c491af37e334fa7
  sha256: 750f02b3f4d8039dd8bdf843187ba678d3423b3366040499b6ca87f39936ca6c
---
#### Summary
- New "Equalizer APP" factory setting to show or hide the Equalizer app
- The equalizer button in Music opens the theme's own sound settings
- KuGou Music updated to 3.5.4

#### Changes
- KswPLauncher (`com.wits.ksw`) app updated from `1.20_230306_1` to `1.20_230316`
  - New "Equalizer APP" (`EQ_app`) checkbox in the factory "Function" settings; when off, the Equalizer app is hidden from the app list
  - `BMW_ID8_UI`: "CHANGE MODUS" opens as a separate screen
  - On first start the launcher sets `ro.zlink.land.display` to the screen resolution
- KswPMedia (`com.wits.ksw.media`) app updated from `1.2_230304` to `1.2_230315`
  - The equalizer button in Music opens the theme's own settings, which appears to land on its sound screen, for the BMW ID7, ID6/ID5, Benz, Audi, Lexus and Land Rover themes; on `BMW_ID8_UI` and `UI_GS_ID8` Video does the same
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.22_230301_1_feasy` to `1.0.22_230316_feasy`
- CenterService (`com.wits.pms`) app updated from `1.0_230215` to `1.0_230309_1`
- Floating windows appear to get rounded corners unless they are 1280 or 1920 pixels wide (not tested)
- "Split screen" is no longer offered for ES File Explorer and the TXZ voice assistant apps
- KugouAuto (KuGou Music) (`com.kugou.android.auto`) app updated from `1.1.7` to `3.5.4`
