---
id: "Witstek-T-M700_OS_v1.6.6-ota"
vendor: ksw
platform: m700
android: 13
date: 2025-09-12T10:19:53Z
signatures:
  md5: d005a42a7d7adedd9b3515b121db288f
  sha1: 9150c9203701073169fae8eaaf6508b985d81478
  sha256: aef4ee1dfccb7a7bd81571f230f0103cd6f3f4d326f9bc5f2f880706c66de54a
---
#### Summary
- Zlink updated to 5.5.12

#### Changes
- Zlink updated from 5.4.95 to 5.5.12 with a new "HUAWEI HiCar Display Settings" option (a "Small" to "Large" slider)
- The Android version override in `/mnt/vendor/persist/OEM/ksw_android11` now also accepts `15`. With it set, Android settings show a `V` in the build number, "February 1, 2025" as the security patch level, the "Vanilla Ice Cream" codename and the Android 15 easter egg
- Both changes are identical to those in `Witstek-T-M600_OS_v1.8.7-ota`, which also brings changes this build does not have
