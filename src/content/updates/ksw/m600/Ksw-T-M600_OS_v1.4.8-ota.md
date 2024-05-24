---
id: "Ksw-T-M600_OS_v1.4.8-ota"
vendor: ksw
platform: m600
date: 2024-01-24T13:21:04Z
signatures:
  md5: 8c40511bc78d6538160623e54e8aead1
  sha1: f4eb5a28e95b45fc879039e54ed0675d7eccd84b
  sha256: 0d50d3a286402fc07bf620f4966ea024cc6991b8749aed988f200fa63b7c1220
---
Summary:
- Potential support for Snapdragon 460 chip on M600 platform

Changes since `Ksw-T-M600_OS_v1.4.4-ota`:
- CarplayZlink (`com.zjinnova.zlink`) app updated from `5.4.26` to `5.4.29`
  - New labels for user license activation
  - Further changes for Huawei HiCar support
  - Tencent Legu packer updated from `4.5.3.9` to `4.5.3.23`
- Ksw360Camera (`com.ivicar.avm`) app updated from `1.0.1_231227` to `1.0.1_240124`
- KswPLauncher (`com.wits.ksw`) app updated from `1.20_231222` to `1.20_240124`
  - Version checks can now detect Snapdragon 460 (SM_KAMORTA) chip as M600 platform as well as existing SD662, based on `/sys/devices/soc0/chip_name` file contents. This could mean that we will see SD460 units on the market, which is a low-end chip from the same timeframe as mid-range SD662.
- CenterService (`com.wits.pms`) app updated from `1.0_231222` to `1.0_240112`
  - Fixed detection for TXZ support
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.22_231215` to `1.0.22_240109`
  - Refactored sorting of the contact list
  - Call screen is now full screen, without the action bar 