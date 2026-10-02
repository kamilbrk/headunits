---
id: "Ksw-R-M600_OS_v2.1.7-ota"
vendor: ksw
platform: m600
android: 11
date: 2022-06-10T09:19:03Z
signatures:
  md5: a74d88dd0b432dc296d30c062c3c7ff4
  sha1: b84bc86d8c891f00d8695083965bf1b788b16a1a
  sha256: 7a68108227d9cc6a19f87969f6334cba322d09d8f094a667a3e11164b97d820c
---
#### Summary
- With an aftermarket amplifier, what appear to be the car's volume buttons also step the Android volume
- Android keeps more apps alive in the background
- "Screen pinning" removed from Android Settings

#### Changes
- CenterService (`com.wits.pms`) app updated from `1.0_220601_1` to `1.0_220609`
  - With "Amplifier Selection" set to "Aftermarket Amplifier", car key codes 21 and 22, which appear to be volume up/down, also change the Android media volume
- Android system: the cached background process limit goes from 4 to 32, so apps should reload less often when switching (not tested)
- Android system: the TXZ voice assistant processes appear to be no longer killed as "empty" processes
- Android Settings: "Screen pinning" removed from the Security page
