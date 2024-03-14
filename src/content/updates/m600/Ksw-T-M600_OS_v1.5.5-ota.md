---
id: "Ksw-T-M600_OS_v1.5.5-ota"
platform: "m600"
date: "2024-03-01T06:27:09Z"
signatures:
  md5: 962205777cf8814fbe233925ba7b3d9b
  sha1: f4323584737c562566b387bb6b2a0509d653dd54
  sha256: 832371ccfc60adb4c7b5ef8d4abdc12749b1395a7524a22eb99aae16b0d6e84e
---
Summary:
- Updated Zlink app 5.4.33 could be more robust between head unit restarts

Changes since `Ksw-T-M600_OS_v1.5.0-ota` built one month earlier:
- CarplayZlink (`com.zjinnova.zlink`) app updated from `5.4.29` to `5.4.33`
    - Updated the CarLife activity to have its own launcher icon instead of re-using icon for Android Auto
    - Removed `android.permission.GET_TASKS` permission that allowed Zlink to retrieve information about running apps - that permission was effectively deprecated since Android 5.0 Lollipop and only returned tasks from Zlink, perhaps to discover when Zlink was running or put into background
    - Added permissions (`android.permission.RECEIVE_BOOT_COMPLETED`) and broadcast receivers (`android.intent.action.LOCKED_BOOT_COMPLETED`) that allow Zlink to use Direct Boot mode and better handle itself between device restarts
    - Added explicit layouts for 1024x592 and 1150x720 screen resolutions
    - Added a bluetooth search button on the Huawei HiCar mode
- Ksw360Camera (`com.ivicar.avm`) app updated from `1.0.1_240124` to `1.0.1_240301`
    - Improved logic around starting/stopping of video recordings
    - Improved handling of storage being removed/ejected
    - Improved clearing up old videos from storage (loop-recording)
- KswPLauncher (`com.wits.ksw`) app updated from `1.20_240124` to `1.20_240201`
    - Improved handling factory app card with four options - AUX, DTV, DVR or Front view camera
    - Cleaned up about 6 MB worth of redundant images
    - Application is now using the `android:testOnly` flag
- KswPVideo (`com.wits.ksw.video`) app updated from `1.2_231129` to `1.2_240221`
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.22_240109_feasy` to `1.0.22_240221_feasy`
    - Fixed an issue where clicking on hang up button did not properly finish the call activity
    - Improved error handling on contacts page
- WitsSystemUI updated
    - Exiting split screen will now send a broadcast to close Ksw360Camera app
- The `ro.build.user` has changed from `lijun` to `robot`, although it's still built from the same machine