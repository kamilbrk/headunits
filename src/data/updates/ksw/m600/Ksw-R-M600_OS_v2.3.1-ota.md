---
id: "Ksw-R-M600_OS_v2.3.1-ota"
vendor: ksw
platform: m600
android: 11
date: 2022-08-18T11:05:04Z
signatures:
  md5: 479336273c20acc6e330ad3f4456df9b
  sha1: 6ad22fb27f6fed78a9c65a4cfb6af4c4cb88d24a
  sha256: ff151d13142598fc56ea7423d69a747e5a8c35a7704f21ef01476b4af58dd78b
---
#### Summary
- New theme `UI_KSW_ID7` on the Android 11 line
- With Zlink on screen, the car's iDrive knob and buttons control it directly
- The launcher no longer starts the `BMW_ID8_UI` home screen and appears to show the ID7 one instead
- Groundwork for Android 12 system updates

#### Changes
- New theme `UI_KSW_ID7`: a two-page BMW ID7-style home screen of cards, using the BMW ID7 settings screens
- With `BMW_ID8_UI` selected, the launcher appears to fall through to the default BMW ID7 home screen; the Bluetooth and media apps keep their ID8 screens
- KswBt recognises `Benz_MBUX_2021_KSW_V2`; the launcher and media app do not yet
- CenterService (`com.wits.pms`) app updated from `1.0_220708` to `1.0_220726`
  - While Zlink is in the foreground, what appear to be the car's knob, arrow, OK, back, navigation, media and call keys go straight to Zlink
  - Switching back from the car's own screen appears to no longer force a jump to the Android home screen
  - With wired AirPlay mirroring connected, the unit's Bluetooth is no longer switched off the way it is for CarPlay
  - System updates also accept `Ksw-S-M600_OS_v…ota.zip` packages
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.22_220706_feasy_1` to `1.0.22_220815_feasy_1`
  - `BMW_ID8_UI` phone screens reworked, with ID8-style "Tips" dialogs
  - During a call, the TXZ voice assistant is switched off only if it is actually running in the foreground
  - The paired-devices list should now put the connected phone first
- KswPMedia (`com.wits.ksw.media`) app updated from `1.2_220707` to `1.2_220816`
  - `BMW_ID8_UI` music player shows lyrics from `.lrc` files
  - Artist and album are read from the file's own tags
- KswPLauncher (`com.wits.ksw`) app updated from `1.20_220706` to `1.20_220818`
  - `ALS_ID7_UI`: the navigation and phone cards follow the skin colour
  - `LEXUS_UI` factory radio screen: with `OEM_FM` enabled, opening or leaving it no longer sends MCU command 103
- Android Settings: battery optimisation no longer restricts apps in the background
- SystemUI: notifications in the pull-down shade should always be expandable (not tested)
- CarplayZlink (`com.zjinnova.zlink`) app updated from `5.2.52` to `5.2.68`
  - New "Link Type" (AUTO / CARLIFE) and "Mic Loopback" options, and 1280x720 and 1920x720 layouts
