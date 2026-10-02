---
id: "Ksw-R-M600_OS_v2.0.0-ota"
vendor: ksw
platform: m600
android: 11
date: 2022-03-08T04:32:02Z
signatures:
  md5: 566f99b8e7de30c6a517075bd933c972
  sha1: 3f4f4c2d5035cfd3ba8f511f52563e3cc5055a51
  sha256: 8c73a802b3c0b8a3ffaf21a2b74963037f0cde52637979c0ba6a46f068de61da
---
#### Summary
- New theme `Audi_mib3_ty`, an Audi MIB3-style home screen not limited to one client
- With "Google Apps" off, the default keyboard switches from iFlytek to Sogou
- Climate popup shows the right-hand temperature correctly in °F

#### Changes
- New theme `Audi_mib3_ty` (set with `UI_type`) with a two-page home screen, a left shortcut bar and 1920x720 and 1280x480 layouts. Unlike `Audi_mib3_FY`, it is not restricted to the `ALS_6208` client
- `Audi_mib3_ty` reuses the Audi MIB3 settings, dashboard, Bluetooth, music, video and equalizer screens
- `Audi_mib3_FY` equalizer gets a 1280x480 layout
- Keyboard: with "Google Apps" off, the default keyboard changes from iFlytek to Sogou (`com.sohu.inputmethod.sogou`), also on updated units. The iFlytek keyboard is removed, and Sogou is not in this firmware (added back in 2.0.3)
- KswAirConditioner (`com.wits.ksw.airc`): in °F mode the right-hand temperature now shows on the right
- KswPLauncher (`com.wits.ksw`) app updated from `1.1.4` to `1.1.5`
- KswPMedia (`com.wits.ksw.media`) app updated from `1.2_11_12` to `1.2_11_13`
- kswEq (`com.wits.csp.eq`) app updated from `1.0` to `1.0.11`
