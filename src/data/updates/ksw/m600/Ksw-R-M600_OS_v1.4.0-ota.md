---
id: "Ksw-R-M600_OS_v1.4.0-ota"
vendor: ksw
platform: m600
android: 11
date: 2021-08-07T08:09:38Z
signatures:
  md5: 18d383f45241dfbaa63be37814579bf6
  sha1: 826aa6eef3d7b01a961a035b912bc4be6f3e278f
  sha256: e5909cbbf7a0f4b94f85f130d6a6748cbebe37229558b4ffffb2c0cbf92f7b27
---
#### Summary
- `PEMP_ID7_UI` gets assignable home-screen shortcuts, working "Select Music App" / "Select Video App" and a speedometer
- `Audi_mib3` gets its own music and video player screens
- New equaliser screen for Benz themes on the `ALS_6208` client
- Zlink updated to `5.1.20`
- The unit switches off after an MCU update

#### Changes
- `PEMP_ID7_UI` (`ALS_6208` client only): the home screen's left menu gets three shortcut buttons (browser, music and video by default); long-press one to assign any installed app
- `PEMP_ID7_UI`: "Select Music App" and "Select Video App" now list the installed apps, and the home-screen music and video cards open the chosen app
- `PEMP_ID7_UI`: the dashboard card shows vehicle speed (up to 280 km/h or 160 mph) instead of engine RPM
- `PEMP_ID7_UI`: the factory "Launcher's Music App" button is hidden
- ID6-style settings gain "Select Music App" and "Select Video App", but only the `BMW_EVO_ID6_CUSP` home screen follows the choice
- `Benz_NTG6_FY`: the default background changes from 1 to 8
- `Benz_MBUX_2021` and `Benz_NTG6_FY`: the small buttons on the home-screen music card skip tracks instead of opening the music app
- `Audi_mib3`: new MIB3-style music and video file lists and players
- `ALS_6208` client: Benz themes open a new equaliser with "User", "Flat", "POP", "Classical", "Rock", "Jazz", "Dance", "Heavy Metal" and "Hip Hop" presets
- The equaliser now checks the `client` value, not the theme name, to decide whether the unit is `ALS_6208`
- Bluetooth music appears to no longer start or resume during a phone call (not tested)
- After a successful MCU update the unit shuts down instead of showing "MCU updated success!"
- A system update file whose name contains `reset-data` performs a factory reset after installing (internal storage is kept)
- CenterService gains key codes `1317` (shut down) and `1318` (factory reset without wiping internal storage)
- Zlink (`com.zjinnova.zlink`) app updated from `5.1.5` to `5.1.20`
  - New "HD", "Allow HiCar connection" and "Default Connection Type" ("Last Mode", "Link Mode First", "Mirroring Mode First") settings
  - The activation screen shows product key, ID and SN, with new activation-code errors
- Android Settings switches on "Allow screen overlays on Settings" at every boot
- Status bar: the mobile signal icon drops to zero bars when the SIM has no service
- Ximalaya FM (`com.ximalaya.ting.android.car` `3.0.1`) and AutoNavi (`com.autonavi.amapauto` `4.3.0.600362`) installers are copied to internal storage on first boot, but not installed
- The `blueware` Bluetooth service is no longer restarted if it exits
- Audio calibration files, the audio and camera HAL libraries and the IPA network firmware changed; what changed inside them is not known
