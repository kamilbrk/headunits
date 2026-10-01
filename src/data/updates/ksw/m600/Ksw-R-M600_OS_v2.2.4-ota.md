---
id: "Ksw-R-M600_OS_v2.2.4-ota"
vendor: ksw
platform: m600
android: 11
date: 2022-07-09T03:42:20Z
signatures:
  md5: 9977d1fc7dc62a3ae113d657c74a7488
  sha1: a6fccf0e00cf620d1f642509fd8610c40afa42c6
  sha256: 1ab9f4e42c6860780f21ec16da4e51b9d95e019b5120dfc146949dc469f32a71
---
#### Summary
- On what appear to be Mercedes-Benz units, the unit sends its clock time to the car every 30 seconds
- The Android version shown in "About" can be overridden by a file on the persist partition

#### Changes
- CenterService (`com.wits.pms`) app updated from `1.0_220620` to `1.0_220708`
  - New `benzClockSort` setting, used only when the car manufacturer appears to be Benz. CenterService sends it with the current time to the MCU every 30 seconds, most likely to keep the car's clock in sync
  - A number in `/mnt/vendor/persist/OEM/ksw_android11` now becomes the `ksw_android11` property; with the 2.2.3 launcher a number above 11 changes the Android version shown in "About". Whether any unit ships such a file is not known
  - Tracks the video player's state the way it already tracked music
