---
id: "Ksw-R-M600_OS_v1.3.5-ota"
vendor: ksw
platform: m600
android: 11
date: 2021-07-26T11:53:10Z
signatures:
  md5: 48fe9fec5ce001fc68906d0fc2cd7090
  sha1: de9f627e9d5c19d3f9847de05cf8c9d081a85f5e
  sha256: 1c6c677f7cc584b689c8c8299e94109d27d686a1ccdb2137168122fd7e1be3c7
---
#### Summary
- New theme `Audi_mib3`
- Lexus-style equaliser for `LEXUS_UI` and `LEXUS_LS_UI`
- Google app and Google Assistant pre-installed
- Zlink downgraded to 5.1.5

#### Changes
- New theme `Audi_mib3` (Audi MIB3), with its own home screen, settings and Bluetooth screens
- `Benz_MBUX_2021` and `Benz_NTG6_FY` get separate 1024x600 and 1920x720 layouts, which appear to be small position tweaks
- New Lexus-style equaliser for `LEXUS_UI` and `LEXUS_LS_UI` with "User", "Flat", "POP", "Classical", "Rock", "Jazz", "Dance", "Heavy Metal" and "Hip Hop" presets
- New "Screen cast - MS9120" (`Screen_cast`) factory option, hidden on Android 11
- The KSW launcher is forced as the default home app only on first boot, so another default launcher should no longer be reset on every start (not tested)
- "Select Music App" and "Select Video App" rows appear in the `ALS_ID7_UI` system settings, but nothing in this firmware makes them work yet
- The voice assistant (TXZ) is told when reverse gear is engaged and released
- The Bluetooth module appears to be switched off when wireless CarPlay connects while a phone is connected over Bluetooth (not tested)
- The ID7 Bluetooth pairing screen shows "Closed" when Bluetooth is switched off
- Google app (`com.google.android.googlequicksearchbox` 11.22.11.21) and Google Assistant (`com.google.android.apps.googleassistant`) pre-installed, enabled or disabled with the other Google apps
- Zlink (`com.zjinnova.zlink`) app downgraded from `5.1.10` to `5.1.5`, which removes its "HD" video switch
- TXZ voice adapter replaced by a new build (`1.1.5` to `210708-37`) that runs permanently; TXZ core also updated
- Qualcomm network-settings app: CDMA and EVDO modes removed from the "Preferred network type" list
- 5 GHz Wi-Fi limited to 40 MHz channels (was 80 MHz), which appears to apply to the hotspot only
- Bluetooth Serial Port Profile (`SPP_ENABLE=1`) turned on
- Speaker audio is routed through a different output path of the audio codec, with updated audio calibration files
- KswBt talks to `com.txznet.smartadapter` instead of `com.txznet.adapter` on builds named `NEXAI`
