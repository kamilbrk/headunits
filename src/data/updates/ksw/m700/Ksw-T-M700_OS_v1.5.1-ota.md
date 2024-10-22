---
id: "Ksw-T-M700_OS_v1.5.1-ota"
vendor: ksw
platform: m700
android: 13
date: 2024-09-30T01:04:12Z
signatures:
  md5: 5645e01c03525ab33316563d6d5b2a8e
  sha1: 1af9958fc47b8b580abbd224baaace4ec3b9bc25
  sha256: 1c9faccad7b7a3102c43fd76a5e8395f273a669323d6cfd3bfd44ba8cebc40af
---
Summary:
- Zlink updated to 5.4.75

Changes since `Ksw-T-M700_OS_v1.5.0-ota` built 12 days earlier:
- Zlink app updated from `5.4.63` to `5.4.75`, potential updates to wireless mirroring for Android and iOS phones, using mobile phone's Wi-Fi hotspot
- Minor updates to [`EVOID9_ALS`](/headunits/themes/ksw/evoid9_als) theme including new graphics, ability to show car speed in mph (in addition to existing kph) and support for more apps like Music, Video and Equalizer
- More Ukrainian translations
- Mentions of Zlink config file that can be imported from USB at `/OEM/zjAecConfig.txt` into internal storage under `/mnt/vendor/persist/OEM/other/zjAecConfig.txt`