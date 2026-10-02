---
id: "Ksw-S-M600_OS_v1.3.2NEXAI-ota"
vendor: ksw
platform: m600
android: 12
date: 2023-03-29T07:37:26Z
signatures:
  md5: a21597865126d50299a47ffe5ea6e5c1
  sha1: e5c93cf4e9b313be81e9edc0a383d08d3b776422
  sha256: cf433c2b1d6dfef3476d27704cacd49e459da678a2e99f96551d470e009a7c87
---
#### Summary
- New themes `UI_MBUX_2021_KSW_1024` and `UI_MBUX_2021_KSW_1024_V2`
- EQ buttons follow the "Equalizer APP" factory setting

#### Changes
- KswPLauncher (`com.wits.ksw`) app updated from `1.20_230316` to `1.20_230329`
  - New theme `UI_MBUX_2021_KSW_1024`, a 1024x600 version of `Benz_MBUX_2021_KSW`
  - New theme `UI_MBUX_2021_KSW_1024_V2`, the same for `Benz_MBUX_2021_KSW_V2`
  - BMW ID8 audio settings open straight on the sound page when reached from an EQ button
  - `UI_GS_ID8`: the home screen video card's buttons appear to control the video player (not tested)
  - `Benz_MBUX_2021_KSW` and `Benz_MBUX_2021_KSW_V2`: the "Theme Settings" dialog is reworked
  - The screen resolution for CarPlay/Android Auto (`ro.zlink.land.display`) appears to be set on every boot (not tested)
- KswPMedia (`com.wits.ksw.media`) app updated from `1.2_230315` to `1.2_230324`
  - The music and video EQ button opens the Equalizer app again, and the theme's own sound settings only when "Equalizer APP" is off
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.22_230316_feasy` to `1.0.22_230329_feasy`
  - The Bluetooth music EQ button follows "Equalizer APP" the same way
- "Equalizer APP" (`EQ_app`) now defaults to on
- CenterService (`com.wits.pms`) app updated from `1.0_230309_1` to `1.0_230318`
- kswEq (`com.wits.csp.eq`) app updated from `1.01_230304` to `1.01_230323`
- Updated Feasycom Bluetooth stack `libbluetooth_qti.so` (build 2022-11-22 to 2023-03-20)
