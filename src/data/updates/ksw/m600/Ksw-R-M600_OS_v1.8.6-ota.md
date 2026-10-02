---
id: "Ksw-R-M600_OS_v1.8.6-ota"
vendor: ksw
platform: m600
android: 11
date: 2021-11-29T03:13:45Z
signatures:
  md5: 0536d3e55e4e1c1f3cd2233bfadba916
  sha1: 19b3f558cea40be4bcbb06c9574f48ceabd7d8f2
  sha256: 71ce0dba5d59fa294fcbc407431518f1d1f298c6ed1bd638d99c85904b6da3ed
---
:::warning
Android bug reports taken on the unit are emailed to the vendor with the unit's IMEI in the subject and its Bluetooth log attached, through a mail account whose password is built into the firmware.
:::

#### Summary
- Builds between `1.4.5` and `1.8.6` are not on this site, so some of these changes may have first appeared in one of them
- New theme `ALS_ID7_UI` with blue, yellow and red colour skins
- New "MIC Gain" page in factory settings
- Widevine DRM support and exFAT tools
- Support for 1280x720 screens on Benz themes and 1560x700 screens on `Audi_mib3`
- Bug reports taken on the unit are emailed to the vendor automatically

#### Changes
- New theme `ALS_ID7_UI` with its own home, settings, factory, Bluetooth, music and video screens. Long-press the home screen's skin tile to pick blue (default), yellow or red
- New "MIC Gain" factory page with a 0-20 slider, saved as `Mic_gain` in [factory_config.xml](/factory-settings/ksw)
- "Gear Selection" in the factory "Car config" page now offers "Gear type 1", "Gear type 2" and "Gear type 3" instead of "Automatic" and "Manual"
- The "Screen cast - MS9120" factory option is shown again. With it on, the new WitsScreencast app (`com.ms.ms2160` `1.0.1.8.2`) starts when what appears to be a MacroSilicon USB display adapter is plugged in
- "Disable Video In Motion" in the factory "Function" page is also shown on `Common_UI_GS_UG` and `Common_UI_GS_UG_1024`
- The DVR "Choose apk" list in factory settings appears to list all installed apps
- Widevine DRM service (`android.hardware.drm@1.3-service.widevine`) added
- exFAT tools (`mount.exfat`, `fsck.exfat`, `mkfs.exfat`) added
- 1280x720 layouts for `Benz_NTG6`, `Benz_NTG6_FY` and `Benz_MBUX_2021`, and 1560x700 layouts for `Audi_mib3`
- `Audi_mib3` gets its own dashboard and MIB3-styled EQ screen
- `LEXUS_UI` / `LEXUS_LS_UI`: the EQ button opens a Lexus-styled EQ screen
- `Benz_NTG6`, `Benz_NTG6_FY` and `Benz_MBUX_2021` get a new app drawer
- CarPlay: wired CarPlay is now recognised for call, voice and audio handling, and the steering wheel voice button appears to start Siri while CarPlay is connected
- During a phone call other apps can no longer take audio focus, so they should no longer start music over the call
- Bluetooth (read from code, not tested): with Android Auto connected, Bluetooth music is switched off at the module instead of disconnecting A2DP
- Changing the time format in the vendor settings also switches Android's own 12/24-hour setting
- The screen timeout is set to "never", apparently at every boot
- Preinstalled third-party apps are installed only on the very first boot, not after every firmware update
- New WitsLog app (`com.wits.log`) emails every Android bug report, with the unit's IMEI and the Bluetooth module log, to the vendor (`witsreceiver@witstech.cn`)
- KswAirConditioner (`com.wits.ksw.airc`) loses °F, the per-manufacturer hide check and the Lexus climate screen (restored in `1.8.9` and `1.9.0`)
- The Google app moves from `system/app` to `system/priv-app`
- The Wi-Fi hotspot on/off state saving added in `1.4.5` is removed again
- Zlink (`com.zjinnova.zlink`) app updated from `5.1.20` to `5.2.0`
  - New "Device Info" page, MFi chip warning, "Wireless CarPlay" / "Wireless Android Auto" labels
- TXZ voice assistant adapter updated from `210708-37` to `211111-59`, with new wake word, welcome phrase, voiceprint and voice settings
- AMap Auto updated from `4.0.5.1824` to `5.0.5.601614`; the second AMap copy (`Auto.apk`) is removed
- KswPLauncher (`com.wits.ksw`) app updated from `1.1.1` to `1.1.4`
- KswBt (`com.wits.ksw.bt`) app updated from `1.0` to `1.0.21_1117`
- KswPMedia (`com.wits.ksw.media`) app updated from `1.0` to `1.2_11_11`
