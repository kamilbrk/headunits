---
id: "Ksw-S-M600_OS_v1.3.6NEXAI-ota"
vendor: ksw
platform: m600
android: 12
date: 2023-04-10T04:36:47Z
signatures:
  md5: 096052e5d5bc4c5125614fc1b2f453aa
  sha1: 981e0e72e69028aefb8db31d47af255a2eb0180a
  sha256: b70df50462006bee6ddfb00ddef2fdaae1e208555784a68c3bb5b18c2804c681
---
#### Summary
- Android "Files" app (DocumentsUI) added
- "Speedometer Selection" shown in factory "Vehicle" settings
- Wi-Fi uses the real MAC address on connected networks

#### Changes
- Added DocumentsUI app (`com.android.documentsui`, "Files"), kept out of the launcher's app list
- KswPLauncher (`com.wits.ksw`) app updated from `1.20_230329` to `1.20_230410`
  - "Speedometer Selection" (`Dashboard_MaxSpeed` in [factory settings](/factory-settings/ksw)) is shown in the "Vehicle" page, with "260km/h" and "280km/h" choices
  - `Benz_MBUX_2021_KSW`, `Benz_MBUX_2021_KSW_V2`, `UI_MBUX_2021_KSW_1024` and `UI_MBUX_2021_KSW_1024_V2`: the home screen background appears to no longer follow the playing song's album art (not tested)
  - More iGO Primo builds are treated as navigation apps, which appears to matter only on `UI_GS_ID8`
  - Factory "Boot Logo" selection refreshes its list of custom logos once they are unpacked
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.22_230329_feasy` to `1.0.22_230410_feasy`
  - Triggering Siri from a connected iPhone appears to no longer bring up the call screen (not tested)
  - Closing the pairing dialog in the ALS ID7 Bluetooth screens stops the search or pending connection
- CenterService (`com.wits.pms`) app updated from `1.0_230318` to `1.0_230331`
  - Treats `com.wits.ksw.music` and `com.wits.ksw.video` as the built-in media player; neither app ships in this build
- Wi-Fi uses the unit's real MAC address on connected networks (`config_wifi_connected_mac_randomization_supported` switched off)
