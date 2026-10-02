---
id: "Ksw-R-M600_OS_v2.4.2-ota"
vendor: ksw
platform: m600
android: 11
date: 2022-10-21T12:28:20Z
signatures:
  md5: 6de43afb9a61780f7376da1fcef051b0
  sha1: b3ff80ec310cd3092bf5c1ad82ab800c2115a03d
  sha256: 0e4849c9b658f8432fdc6b3c9368a7f1ea16142c2070020293fc78f0fae297b6
---
#### Summary
- Eight new themes: `UI_KSW_MBUX_1024` and seven "V2" themes with a live weather card
- `BMW_ID8_UI` becomes a full launcher theme
- New TXZ Weather and TXZ OTA apps pre-installed
- Video player switches to software decoding, capped at 30 fps
- New Bluetooth stack build

#### Changes
- KswPLauncher (`com.wits.ksw`) app updated from `1.20_220913` to `1.20_221019`
  - New themes `UI_mib3_V2`, `Audi_mib3_FY_V2` (`ALS_6208` client only), `UI_NTG6_FY_V2` (`ALS_6208` client only), `Benz_MBUX_2021_KSW_V2`, `LEXUS_LS_UI_V2`, `BMW_EVO_ID7_V2` and `PEMP_ID7_UI_V2` (`ALS_6208` client only), each with a weather card from the TXZ Weather app
  - New theme `UI_KSW_MBUX_1024`, a three-page MBUX-style home screen using the NTG6 settings
  - `BMW_ID8_UI` rebuilt: a home screen of cards that can be rearranged in "EDITOR MODE", "EFFICIENT" / "PERSONAL" / "SPORT" colour modes, its own settings, apps grid and dashboard
  - New "System check update" row in system information, which asks the TXZ OTA app for an update
  - `UI_KSW_ID7`: a Benz control-panel button on the home screen, and the factory "Control Panel" option always shown
  - Factory settings: the first time "Function" is opened, "USB HOST" is switched on
- SystemUI: a separate `BMW_ID8_UI` status bar, picked when SystemUI starts, so switching to or from ID8 probably needs a reboot
- SystemUI: thinner status bar icons on the other themes
- kswEq (`com.wits.csp.eq`) app updated from `1.0.11` to `1.01_221021`
  - New 12-band `BMW_ID8_UI` EQ screen
- KswPMedia (`com.wits.ksw.media`) app updated from `1.2_220913` to `1.2_221013`
  - Video uses software decoding, capped at 30 fps instead of 60
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.22_220915_feasy` to `1.0.22_221013_feasy`
  - Deleting a paired phone sends its address to the Bluetooth module, which should stop the wrong phone being unpaired
  - Writes the unit's IMEI to the system log whenever a Bluetooth screen opens, and now ships as a test-only build (`testOnly`)
- Bluetooth stack (`libbluetooth_qti.so`, `blueware.properties`):
  - New build that appears to talk to Zlink through a library instead of the `zj_bt_socket` / `zj_bt_serial` links
  - "OBDII" and "AutoMeter DashLink" OBD dongles recognised alongside "D-6.1200"
  - Call audio settings changed (wideband calls off, echo delay added); the audible effect is not known
  - Shorter ringtone (3.3 s to 2.2 s)
- Wi-Fi: the hotspot can use indoor-only channels and the 5.8 GHz SRD channels in EU countries
- Wi-Fi hotspot (`hostapd`): an Apple vendor element is back, most likely for wireless CarPlay discovery
- Android hotspot: moving the hotspot to 5 GHz forces WPA2-PSK unless security was changed by hand; the password is written to the system log
- CenterService (`com.wits.pms`) app updated from `1.0_220915` to `1.0_221019`
  - Starts the TXZ update service at every boot
  - No longer puts user-installed apps into app standby
  - System updates accept any `Ksw-R-M600_OS_v*` file containing `.zip`
  - The boot-time sync of the TXZ voice assistant switch (`Support_TXZ`) is removed
- New boot logo `imagefv_004` with KSW branding, for 1920x720 screens only
- New pre-installed TXZ Weather (`com.txznet.weather` `1.0.5_2`) and TXZ OTA (`3.0.0`) apps, both contacting `txzing.com` servers with the unit's IMEI
- CarplayZlink (`com.zjinnova.zlink`) app updated from `5.2.72` to `5.3.6`
- TXZAdapter (`com.txznet.adapter`) app updated from `220620-84` to `221018-84`
