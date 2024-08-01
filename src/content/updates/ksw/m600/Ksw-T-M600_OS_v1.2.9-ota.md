---
id: "Ksw-T-M600_OS_v1.2.9-ota"
vendor: ksw
platform: m600
android: 13
date: 2023-11-06T13:13:54Z
signatures:
  md5: 07e5ca34c51fafb2db960dd4263c93bc
  sha1: 721d4dd2ae556168fbb7dc79e2e40e176e30db08
  sha256: c1651e789ae3fcf24288c1504fc92c49b1a26a98406c358ea5ae9b10f62da2ad
---
Summary:
- Zlink update 5.4.19 with "Recording mic file", "Noise reduction" and "Echo cancellation"
- Version strings are now prefixed with `Witstek `
- Further work on Ksw 360 Camera app
- Fix for signal status icon
- Partial fix for USB permission issues

Changes since `Ksw-T-M600_OS_v1.2.0-ota`:
- CarplayZlink (`com.zjinnova.zlink`) app updated from `5.3.49` to `5.4.19`
    - Internal checks to see if it's running on Android 13 (SDK 33) and mark some internal class files as read-only.
    - Updated Tencent Legu packer from `4.5.0.4` to `4.5.2.5`
    - Added a toast message that can be invoked from another application, it would say something along the lines of "Your device may have security risks, please send the following information to the developer. Thank you." (google translation)
    - Added labels for "User Manual", "Recording mic file", "Noise reduction" and "Echo cancellation" (with 3 algorithms to choose from)
    - Added launcher icons for DLNA, Huawei HiCar and screen mirroring
    - Updated to Material 3
- Ksw360Camera (`com.ivicar.avm`) app updated from `1.0.1_231010_1` to `1.0.1_231103`
    - Ability read MCU values via power manager app
    - Added keyboard functionality
    - High temperature protection preventing the app from opening
- KSWPLauncher (`com.wits.ksw`) app updated from `1.20_231010` to `1.20_231103`
    - Updated few themes to prepend displayed version with `Witstek ` string
    - Reading memory value from `/mnt/vendor/persist/OEM/memoryvalue_501a` file on Android 10 instead of reporting hard-coded `4GB` text
    - Improved handling for detection of Ksw360Camera app
- KswPVideo (`com.wits.ksw.video`) app updated from `1.2_231010` to `1.2_231106`
- Added ability to listen into `android.net.wifi.WIFI_AP_STA_JOIN` and `_LEAVE` broadcasts
- Added GPS permission for `com.ecar.assistantnew`
- Updated 4th and 5th default boot image for 1920_720 resolution
- Updated CenterService (`com.wits.pms`) from `1.0_231009.3` to `1.0_231031`
    - Added handling for Zlink to broadcast events that Huawei HiCar has been connected (wired and wireless)
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.22_230915_feasy` to `1.0.22_231106_feasy`
    - Added handling for Zlink's Huawei HiCar, to stop call activity when connected
    - Improved something to do with BMW ID8 theme and its "touch bean"
- Settings app updated to prepend version with `Witstek ` string
- WitsSystemUI updated
    - Fixed signal status icon to correctly update level under 5
    - Updated UsbConfirmActivity resume method to prompt user rather than finishing early
