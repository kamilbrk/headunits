---
id: "Witstek-T-M700_OS_v1.5.6-ota"
vendor: ksw
platform: m700
android: 13
date: 2024-11-16T04:54:39Z
signatures:
  md5: 23ecd756e172ced35d84745048df2ddd
  sha1: fd98944197dd7b3bf2fbf4b06f15429b80f64f1b
  sha256: da90042237e3776611a27e5ffb531f6576e53107f9fcb78b91530e0b04331096
---
Summary:
- Mostly internal changes, nothing to see here
- Due to `Witstek-` file name prefix, you need to either upgrade from at least [M700 1.4.2](/headunits/updates/ksw/m700/ksw-t-m700_os_v142-ota) where support for these filenames was introduced or rename the file to start with `Ksw-`.

Changes since `Ksw-T-M700_OS_v1.5.5-ota` built 22 days earlier:
- Ksw360Camera: New "Function button display" setting with "Left and right ends" and "Bottom" options
- Fixed missing version information display on Audi theme
- New `witssudo` service with a corresponding `/system/bin/wits_sudo.sh` script that can swap some files via `getprop wits.logo1` (splash), `getprop wits.logo2` (bootlogo and bootanimation) and `getprop wits.item` (?)
- Some new code to replace returned Android and Android SDK versions. There are mentions of at least AnTuTu Benchmark (`com.antutu.ABenchMark`) and 3DMark (`com.futuremark.dmandroid.application`) apps, althought it's hard to say if this is to fake/spoof shown versions or fix/correct their values. There's also a `ksw_android11` value that could be shown in places, yet to test on a real device.
- New factory setting `<cpu_firmware_version>`