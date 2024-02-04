---
id: "Ksw-T-M600_OS_v1.4.0-ota"
platform: "m600"
date: "2023-12-07T05:52:19Z"
signatures:
  md5: 3519f5a6f459aa91045eebe72642bf53
  sha1: 537f88c1e7d990d594936aa902362848cf60beb5
  sha256: 0bfbb7ef8ab0c2e1d10c104846b2ee76b0cbde3961bf95256e82befa5d54d857
---
Summary:
- Potentially fixed USB permissions

Changes since `Ksw-T-M600_OS_v1.3.8-ota` built 6 days earlier:
- CarplayZlink (`com.zjinnova.zlink`) app updated from `5.4.23` to `5.4.26`
- Ksw360Camera (`com.ivicar.avm`) app updated from `1.0.1_231129` to `1.0.1_231207`
  - Reading MCU data to find out system mode and camera status
  - Support for 1024x600 screen resolution
- Framework resources
  - Changed `<bool name="config_disableUsbPermissionDialogs">false</bool>` to `true` which would affect the logic in Android's `UsbProfileGroupSettingsManager` at https://android.googlesource.com/platform/frameworks/base.git/+/master/services/usb/java/com/android/server/usb/UsbProfileGroupSettingsManager.java#1076
- CenterService (`com.wits.pms`) app updated from `1.0_231121` to `1.0_231205`
  - Added handling for Zlink event broadcasts to pause/resume things, based on MCU system mode and Ksw360Camera app state
- TXZWeather (`com.txznet.weather`) app updated from `1.0.5_4` to `1.0.8`
  - Added Thai (`th-TH`) language
  - Added ability to send "buried point reports" to "collect abroad weather messages"
  - Updated Gradle build tools to 7.4
