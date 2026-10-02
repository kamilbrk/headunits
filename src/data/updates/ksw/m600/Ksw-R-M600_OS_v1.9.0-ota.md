---
id: "Ksw-R-M600_OS_v1.9.0-ota"
vendor: ksw
platform: m600
android: 11
date: 2022-01-05T06:16:37Z
signatures:
  md5: ec3b617977815c4b4a1e2cdc34545be1
  sha1: 39cc180a21c2473e12c6abf50cfbff4464e25430
  sha256: 2d20061365b4084fd4ef0a2760d5bd2fe176d15325874c430fa3634e33d59b30
---
#### Summary
- New theme `Audi_mib3_FY` for the `ALS_6208` client
- The Lexus touch climate screen, missing since `1.8.6`, is back
- Pressing the steering wheel voice key again closes the voice assistant

#### Changes
- New theme `Audi_mib3_FY` (`ALS_6208` client only; other units fall back to the `BMW_EVO_ID7` home screen), with a two-page home screen, a left shortcut bar and 1920x720 layouts
- `Audi_mib3_FY` dashboard with "ECO PRO", "COMFORT" and "SPORT" modes
- `Audi_mib3_FY` reuses the Audi MIB3 settings, Bluetooth, music and video screens, and gets its own equalizer screen in kswEq (`com.wits.csp.eq`)
- Lexus themes: the climate button opens the touch climate screen in KswAirConditioner (`com.wits.ksw.airc`) again, with temperature, fan, A/C, auto, recirculation and demist buttons
- Steering wheel voice key: pressing it while the TXZ voice assistant is showing now closes it
- `BMW_EVO_ID7`, `BMW_EVO_ID7_HiCar`, `Common_UI_GS_UG`, `Common_UI_GS_UG_1024` and `Audi_mib3_FY`: the home-screen music tile opens the app chosen in "Select Music App" instead of the factory "Launcher's Music App". On `Audi_mib3` the left-bar music button now follows the same choice
- `PEMP_ID7_UI`: the home-screen music widget's buttons open the music app first when nothing is playing (not tested)
- ALS dashboard (`ALS_6208` client): the touch area that opens the drive-mode panel is narrower
- "Disable Video In Motion" in the factory "Function" page is also shown on `BMW_EVO_ID6_GS`
- Audi-style dates in the launcher and KswBt no longer show the next year in the last days of December
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.21_1221` to `1.0.21_1223`
  - Contact lists are rebuilt on every phonebook update, so edited contacts should now refresh
- APKInstaller (`com.wits.apk`) shows each APK's version in its list
