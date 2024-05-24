---
id: "Ksw-T-M700_OS_v1.1.5-ota"
vendor: ksw
platform: m700
date: 2023-12-15T03:25:21Z
signatures:
  md5: df16172f9fa2c9e3a36c6fb275ce6521
  sha1: e6e8ae17e298afa4574941be021db5471323d995
  sha256: 5df574d3f8a7c9789210967d3824f3bb09921488a4e8786996f3f2e096ee094c
---
Summary:
- Starting in December 2023, we have first firmware updates for `M700` head units runnning on Qualcomm Snapdragon 680 SM6225 chips.
- It appears that M600 and M700 builds are coming from the same code branch, perhaps just built for two different architecture targets, therefore generating two different artifacts.
- There does not seem to be any M700 specific changes in this firmware, just code changes that happened between M600 1.4.0 (built 8 days earlier) and M600 1.4.4 (built 12 days later) anyway.

Changes between `Ksw-T-M600_OS_v1.4.4-ota` (M600/SD662) built 12 days later (other than 1.4.0 - 1.4.4)
- SoC board variant `config.hw_platform` from `["QRD"]` to `["MTP"]` in the following files:
  - `/vendor/etc/sensors/config/bengal_qrd_ak991x_0.json` (compass and magnetometer)
  - `/vendor/etc/sensors/config/bengal_qrd_lsm6dso_0.json` (accelerometer and gyro)
  - `/vendor/etc/sensors/config/bengal_qrd_tmd2725.json` (ambient light sensor)
