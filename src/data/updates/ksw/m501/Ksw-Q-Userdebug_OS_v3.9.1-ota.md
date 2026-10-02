---
id: "Ksw-Q-Userdebug_OS_v3.9.1-ota"
vendor: ksw
platform: m501
android: 10
date: 2022-10-24T13:17:37Z
signatures:
  md5: 36219a688b37204d257875469b928e8a
  sha1: d7015c2202d0eab9c203d92a3f547e7dfffe2f6d
  sha256: 7245ed2de686084d067819df42bebd179b8c2ff13887a71af3377d189cbe3327
---
#### Summary
- `BMW_ID8_UI` theme gets its own home screen
- New TXZ Weather app and weather-enabled "V2" variants of seven themes
- New theme `UI_KSW_MBUX_1024`
- New "FL Speaker Enable" and "Speed Type Selection" factory settings

#### Changes
- KswPLauncher (`com.wits.ksw`) app updated from `1.20_220913` to `1.20_221024`
  - `BMW_ID8_UI` gets its own home screen; in `3.8.9` the launcher fell back to the BMW ID7 layout
    - Home screen of cards with an "EDITOR MODE" to reorder them, "ADD WIDGET" and changeable left-bar shortcuts
    - "MODUS" switches the colour scheme: "EFFICIENT" (blue), "SPORT" (red) or "PERSONAL" (yellow)
    - Own settings, instrument cluster and EQ screens
  - New theme `UI_KSW_MBUX_1024`, a three-page Mercedes-Benz MBUX-style home screen using the NTG6 settings
  - New weather-enabled themes `BMW_EVO_ID7_V2`, `PEMP_ID7_UI_V2` (`ALS_6208` client only), `Benz_MBUX_2021_KSW_V2`, `UI_NTG6_FY_V2` (`ALS_6208` client only), `UI_mib3_V2`, `Audi_mib3_FY_V2` (`ALS_6208` client only) and `LEXUS_LS_UI_V2`
  - New "FL Speaker Enable" and "Speed Type Selection" options in the factory "Car" section (`Front_left`, `Speed_type`). Nothing in the changed apps appears to read them
  - The "Control Panel" factory option also shows on `UI_KSW_ID7` and `UI_KSW_MBUX_1024`
  - New "System check update" button in System Info, which no app in this firmware appears to answer
- New TXZ Weather app (`com.txznet.weather` `1.0.5_2`), pre-installed; the weather cards open it
  - It has to be activated online and appears to send the unit's device ID to `tsp.txzing.com`
- KswPMedia (`com.wits.ksw.media`) app updated from `1.2_220913` to `1.2_221013`
  - Video player switched from hardware to software decoding, capped at 30 fps
- kswEq (`com.wits.csp.eq`) app updated from `1.0.11` to `1.01_221021`
  - New ID8 EQ screen
- TXZ voice assistant adapter (`com.txznet.adapter`) updated from `220620-84` to `221018-84`
- New KSW boot logo (`logo_004`) for 1920x720 screens only
- Android Settings exempts Melon, Naver Map, Tom VPN, KimGiSa, Amazon Music and Spotify from battery optimisation
