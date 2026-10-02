---
id: "Witstek-T-M600_OS_v1.8.7-ota"
vendor: ksw
platform: m600
android: 13
date: 2025-11-03T06:37:29Z
signatures:
  md5: 49cf128831c5a093bf1af8d6eec3129d
  sha1: 2b575fbbd78a656ff148e2e488591aa455f81ec2
  sha256: 630f49f6d6f86bddb2e64e19ea5e1bf1dcef8d9bc6b3ed85e0efb3e6dbbec853
---
#### Summary
- Zlink updated to 5.5.12
- Screen resolution is now shown in Android settings and in the system info of Benz MBUX 2021 and NTG6 themes

#### Changes
- Zlink updated from 5.4.95 to 5.5.12 with a new "HUAWEI HiCar Display Settings" option (a "Small" to "Large" slider)
- KswPLauncher updated to `1.20_250418`, adding "Screen resolution" to the system info page of Benz MBUX 2021 and NTG6 themes
- New "Screen resolution" row in Android settings, under About
- The Android version override in `/mnt/vendor/persist/OEM/ksw_android11` now also accepts `15`. With it set, Android settings show a `V` in the build number, "February 1, 2025" as the security patch level, the "Vanilla Ice Cream" codename and the Android 15 easter egg
- Yandex Navigator is no longer handled like YouTube when it comes to the foreground
- Zlink and the Android 15 override also arrived on M700 in `Witstek-T-M700_OS_v1.6.6-ota`
