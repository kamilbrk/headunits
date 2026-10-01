---
id: "Ksw-R-M600_OS_v2.2.0-ota"
vendor: ksw
platform: m600
android: 11
date: 2022-06-20T03:51:02Z
signatures:
  md5: 00bf04db44b0cf832e325ba703c27716
  sha1: 61858b6955e034f478fa43b383c85581c5c1db13
  sha256: 23ac4d725bcabd442cc4e24eb98176509bf4f0e7f7e8fcf11fe74e59ac100d1c
---
#### Summary
- New "Front view mirror setting" factory option
- Zlink updated to `5.2.49`, with call volume settings and DLNA "TV projection"
- Zlink's manifest sets up Baidu Mobile Statistics with location collection on (traffic not verified)
- With an aftermarket amplifier, the car's volume buttons change the call volume during a Bluetooth call

#### Changes
- New "Front view mirror setting" checkbox (`forwardCamMirror`) in the factory "Function" page, sent to the MCU, which appears to do the mirroring
- CenterService (`com.wits.pms`) app updated from `1.0_220609` to `1.0_220620`
  - With "Aftermarket Amplifier", the car's volume buttons step the call volume during a Bluetooth call; the Android-volume stepping added in 2.1.7 is removed again
- KswPLauncher (`com.wits.ksw`) app updated from `1.20_220531_1` to `1.20_220614_1`
  - `ALS_ID7_UI` dashboard uses a different needle image
- CarplayZlink (`com.zjinnova.zlink`) app updated from `5.2.14` to `5.2.49`
  - New "Call volume adjustment" page (not tested)
  - New "Force Port Layout" (Android Auto in portrait) and "Back to hu" switches
  - New "TV projection" (DLNA) screen, with its launcher icon disabled by default
  - Screens say "CP" and "AA" instead of "CarPlay" and "Android Auto"
  - Its manifest sets up Baidu Mobile Statistics with GPS, cell and Wi-Fi location reporting on (actual traffic not verified)
