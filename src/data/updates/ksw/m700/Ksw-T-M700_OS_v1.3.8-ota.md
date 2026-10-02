---
id: "Ksw-T-M700_OS_v1.3.8-ota"
vendor: ksw
platform: m700
android: 13
date: 2024-07-26T02:22:05Z
signatures:
  md5: dbf1daa5686f4983bd8f3f455de0fe04
  sha1: 83811c122ab32da811f1b0fc9be660353a3acd04
  sha256: b94c62c70cbdcaceaba92951854d0a85ad7d3bb6c7d7763fc1c497fe544aa3c8
---
#### Summary
- Zlink updated to `5.4.54`
- New `EVOID9_ALS` and `EVOID8_UG_2mode` themes

#### Changes
- Zlink updated from `5.4.53` to `5.4.54`
- New `EVOID9_ALS` theme
    - It will have the following modes to switch between: Comfort, Elegant, Mystery, Noble, Passionate, Steady, Energetic
    - It will have a wallpaper selection, including a "personalised wallpaper", and a "real-time speed" label on its dashboard card
    - Ability to select a free form app to be drawn similarly to ID8 theme, set to Amap Auto by default if installed, otherwise Google Maps (if Google apps are enabled)
    - There's going to be a new internal setting about a free window radius, which turns rounded corners of floating windows on for `UI_GS_ID8` and off for `EVOID9_ALS`
    - It's likely that the floating app is (re)activated whenever the home screen is shown again
    - Most apps like Launcher, CenterService, Music, Video, Equalizer, Bluetooth, have initial support for this theme now, it appears fairly safe to apply by now, but it has not been tested.
- New `EVOID8_UG_2mode` theme
- New "AUX Position" settings screen on `UI_NTG6_FY_V3` theme, shown only when factory AUX type is "Other"