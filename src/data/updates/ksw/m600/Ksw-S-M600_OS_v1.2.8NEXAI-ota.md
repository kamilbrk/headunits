---
id: "Ksw-S-M600_OS_v1.2.8NEXAI-ota"
vendor: ksw
platform: m600
android: 12
date: 2023-03-06T12:18:54Z
signatures:
  md5: c8a0cd80f9ead6fa675c6d3045156ac3
  sha1: 0f1391f380b5f90e2eb424c1b72c67b30eb7a767
  sha256: 6f99ccea94dd35a3d84e1f8d278f4a2e8582d195d33a9744cb74a81528bf0438
---
#### Summary
- `UI_GS_ID8` home screen shows the navigation app in a floating window
- Split-screen layouts for the BMW ID8 phone, music and video screens
- `Audi_MMI_4G` home screen shows weather instead of the logo

#### Changes
- KswPLauncher (`com.wits.ksw`) app updated from `1.20_230129` to `1.20_230306_1`
  - `UI_GS_ID8`: the navigation card opens the first installed of AMAP Auto, Google Maps, NaviKing 3D and iGO Primo in a floating window, which appears to sit over the card
  - `UI_GS_ID8`: the left bar starts with a fixed "NAV" entry, and the three other slots default to Music, Phone and Car info
  - `Audi_MMI_4G`: the right-hand home screen widget shows weather where it showed a logo, and the `Audi_Logo_Right` factory choices are renamed to match
  - "Speedometer Selection" is hidden in the factory "Vehicle" settings
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.22_230111_feasy` to `1.0.22_230301_1_feasy`
  - Compact `BMW_ID8_UI` layouts for split screen
- KswPMedia (`com.wits.ksw.media`) app updated from `1.2_230111` to `1.2_230304`
  - Compact `BMW_ID8_UI` music and video layouts for split screen
- CenterService (`com.wits.pms`) app updated from `1.0_230111` to `1.0_230215`
- kswEq (`com.wits.csp.eq`) app updated from `1.01_221103` to `1.01_230304`
  - `UI_GS_ID8` opens the `BMW_ID8_UI` equalizer screen
- SystemUI: `UI_GS_ID8` uses the `BMW_ID8_UI` status bar
- Android system: floating (freeform) windows switched on at boot, with the maximise and close buttons hidden
- Recent apps menu: "Free form" removed, and "Split screen" no longer offered for Zlink, Settings, the TXZ weather app and the Equalizer
- AMAP Auto and Papago appear to get twice the default Java heap while in the foreground (not tested)
- Bluetooth: a ringtone file (`/etc/bluetooth/RingTone.wav`) is now included, so it should play for phones that cannot send their own (not tested)
