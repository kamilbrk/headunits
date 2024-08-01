---
id: "Ksw-T-M600_OS_v1.2.0-ota"
vendor: ksw
platform: m600
android: 13
date: 2023-10-10T10:07:17Z
signatures:
  md5: 39c0b2d641969c20423bfda587c6163b
  sha1: de060a92cc2d55e701042dcb64ea8491db68b7fd
  sha256: a5c47c6bd7a2fbfed52ceeced01e687131f6ccff285afb43cd2997ce99a8c432
---
Changes since `Ksw-T-M600_OS_v1.1.9-ota`:
- Ksw360Camera (`com.ivicar.avm`) app updated to `1.0.1_231010_1`
    - New code to set `vendor.wits.360camera.power.open` setting
    - Disabled camera auto recording by default
    - Added screen size adjustment
    - Added option to display driving speed
    - Added lots of logging
- APK Installer (`com.wits.apk`) app updated to `1.0_20231010`
    - Minor layout changes
- KSWPLauncher (`com.wits.ksw`) app updated to `1.20_231010`
    - New factory setting "360APK" that should appear after "Global Weather App" and "Equalizer APP"
- KswPVideo (`com.wits.ksw.video`) app updated to `1.2_231010`
    - Automatic pause/resume of video playback based on status of Ksw360Camera
- Wits Framework
    - Boot process optimisations based on activity manager, likely to ensure all essential processes are running prior to launching any apps like Ksw360Camera
    - Setting under `adb shell dumpsys wits_car_manager boot_optimize fallbackhome` / `persist.vendor.wits.boot_optimize.fallbackhome.enable`
- CenterService (`com.wits.pms`) app updated to `1.0_231009.3`
    - Power manager service changes for handling Ksw360Camera
