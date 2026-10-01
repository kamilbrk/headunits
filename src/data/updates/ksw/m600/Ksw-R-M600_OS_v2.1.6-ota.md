---
id: "Ksw-R-M600_OS_v2.1.6-ota"
vendor: ksw
platform: m600
android: 11
date: 2022-06-02T07:57:06Z
signatures:
  md5: 06110bb6014ef088b2fd92eef8dcacbc
  sha1: 9dcdbe426faf0cc58f495e38b6a2ddbe2e09afb7
  sha256: 2c5eb938eab8b87fbe5f6910fcdb176baaca47ed2ec4514b19aba6df9b993dbd
---
#### Summary
- `BMW_ID8_UI` home screen fleshed out, still not usable
- `LEXUS_UI` instrument cluster shows an imperial unit image in mph mode
- Car status sent to the voice assistant appears to be read from the correct bits now

#### Changes
- `BMW_ID8_UI` home screen gets a left bar ("APPS", "Music", "TEL", "Navigation") and eight different cards, but nothing responds to taps yet
- `LEXUS_UI` instrument cluster: in mph mode an imperial unit image is shown next to the speed
- `Benz_MBUX_2021` on 1920x720 screens: the page dots and "Theme Settings" button appear to be centred at the bottom
- The car status given to the TXZ voice assistant (doors, seatbelt, fuel, speed, temperature) is read from different bits of the MCU message, which appear to be the correct ones
- Zlink: CenterService tracks when Siri is on, and its microphone handling for Zlink calls checks that state
- `ALS_ID7_UI` video player: the side menu icons and labels appear to be centred
- KswPLauncher (`com.wits.ksw`) app updated from `1.20_220518` to `1.20_220531_1`
- KswPMedia (`com.wits.ksw.media`) app updated from `1.2_220517` to `1.2_220527_1`
- CenterService (`com.wits.pms`) app updated from `1.0` to `1.0_220601_1`
