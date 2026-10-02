---
id: "Ksw-R-M600_OS_v1.4.3-ota"
vendor: ksw
platform: m600
android: 11
date: 2021-08-11T02:13:18Z
signatures:
  md5: bd960eaa39285ac8a2301d4a621ee49c
  sha1: 15476ae9604898c6467f1e2a0cbba209cb5c3417
  sha256: b1dbd17e96f87d3fb13b6088594e80f2150339ab831e90c17a5801bdb5c66b92
---
:::warning
Encryption of the `/data` partition is removed, so apps and settings on the unit are no longer stored encrypted; on a unit whose data is already encrypted the effect is not known. Update files with `force-update` in their name now install without asking, and a file named `Ksw-R-M600_OS_v-ota-only-reset-data_factory.zip` on a USB stick reboots the unit into recovery to wipe it.
:::

#### Summary
- "Select Music App" and "Select Video App" for most themes, followed by the home-screen music and video tiles
- Encryption options removed from the `/data` mount settings
- QQ Music and Kugou are no longer installed on first boot
- A system update file with `force-update` in its name installs without asking

#### Changes
- New "Select Music App" and "Select Video App" entries in system settings for `Audi_MMI_4G`, `Benz_NTG5`, `Audi_mib3`, the Benz themes, `BMW_EVO_ID7` and the themes using its settings, `LAND_ROVER`, `LEXUS_UI`, `LEXUS_LS_UI` and `Alfa_Romeo`
- The larger-screen layouts of the `PEMP_ID7_UI` and ID6-style settings also gain both entries
- The home-screen music and video tiles open the app chosen in those settings (falling back to the built-in player) on most themes; the music tile no longer follows the factory "Launcher's Music App" button
- `PEMP_ID7_UI` larger-screen layout: the left menu gets the three assignable shortcut buttons that `1.4.0` added
- `fileencryption=` and `metadata_encryption=` are removed from the `/data` entries in `fstab.default` and `fstab.emmc`. The effect on units whose data is already encrypted is not known
- First-boot setup no longer installs QQ Music (`qqmusiccar.apk`) or Kugou (`KugouAuto.apk`); it copies both to internal storage as installer files instead
- A system update file whose name contains `force-update` installs straight away, without the "update?" question
- The USB recovery script `dual_clear_ota.sh` now runs at every boot and looks for `Ksw-R-M600` file names instead of `Ksw-Q-Userdebug`
- CenterService drops key code `1318`, the factory reset without wiping internal storage that `1.4.0` added
- Bluetooth: while the car's original system is shown, Bluetooth appears to no longer change its own volume on audio focus changes (not tested)
- Status bar: the USB/SD indicator appears to update when a drive is mounted, but ignores USB drives of 1.5 GB or less
- Android Settings: the search bar is hidden
- Audio calibration files and the audio policy library changed; what changed inside them is not known
