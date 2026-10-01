---
id: "Ksw-R-M600_OS_v1.9.7-ota"
vendor: ksw
platform: m600
android: 11
date: 2022-02-17T11:37:36Z
signatures:
  md5: 5ce7b633cb0e67fed59a79c52019d73d
  sha1: b5eb3626bbfb88570ee705da1f9ed42dea5bbf65
  sha256: 3d60fdc3741a7af6bca08635937fee97da502f56979aa00715ec979cebbfffc8
---
#### Summary
- Builds `1.9.1` to `1.9.6` are not on this site, so some of these changes may have first appeared in one of them
- New theme `Benz_MBUX_2021_KSW`
- Preinstalled apps now depend on the factory "Google Apps" option
- Preinstalled apps are updated after a firmware update
- New factory options "Phone Key Selection" and "HiCar voice function key"

#### Changes
- New theme `Benz_MBUX_2021_KSW`, a KSW variant of `Benz_MBUX_2021` with 7 background colours and a "Classical" / "Modern" icon style. It uses the Benz NTG6 settings, Bluetooth, media and EQ screens
- With "Google Apps" off, AutoNavi maps, `TXZAdapter.apk`, QQ Music, Kugou and Ximalaya are installed; with it on, DAB-Z (`com.zoulou.dab`) and WitsScreencast are installed instead. MX Player, ES File Explorer and Zlink are installed for everyone
- With "Google Apps" off, an app that fails to open from the launcher opens AutoNavi maps instead
- After an OTA update, CenterService reinstalls any preinstalled app that is newer on the system image, with an "App is updating" progress dialog
- New "Phone Key Selection" factory option: "Original vehicle function", "Android Bluetooth feature" or "Undefined" (`phone_key`)
- New "HiCar voice function key" choice for the steering-wheel voice key (`Voice_key` = `4`)
- The "MIC Gain" factory slider now stops at `12` instead of `20`
- HiCar: switching to the car's original system appears to stop HiCar music (not tested)
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.21_1223` to `1.0.22_0107`
  - The TXZ voice assistant is switched off during a call and back on after hang-up
- Bluetooth pairing page on `ALS_ID7_UI` and `PEMP_ID7_UI`: shows "Closed" when Bluetooth is switched off
- Music and video player: media buttons act only on key release, so one press should no longer register twice
- EQ: moving a band slider switches the preset to "User" on the `ALS_6208` Benz EQ screen and on `Audi_mib3` and `Audi_mib3_FY`
- `ALS_ID7_UI`: the chosen skin colour is remembered across restarts, and "Select Music App" also sets the first home shortcut
- The home music tile on `ALS_ID7_UI`, `PEMP_ID7_UI` and `BMW_EVO_ID6_CUSP` appears to open the app chosen in "Select Music App" (not tested)
- `LAND_ROVER` on 1280x660 screens: "Select Music App" and "Select Video App" added to system settings
- TXZ adapter (`com.txznet.adapter`) updated from `211203-76` to `220107-77`
