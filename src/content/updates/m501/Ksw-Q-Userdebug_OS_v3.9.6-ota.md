---
id: "Ksw-Q-Userdebug_OS_v3.9.6-ota"
platform: "m501"
date: "2022-12-16T05:37:01Z"
---
- CarplayZlink (`com.zjinnova.zlink`) app updated from `5.2.74` to `5.3.24`
    - Added CarLife (USB and Bluetooth)
    - Added support for more screen sizes (1712x440)
- TXZAdapter (`com.txznet.adapter`) app updated from `221116-84` to `221202-84`
- APKInstaller (`com.wits.apk`) app updated from `1.0_20221024` to `1.0_20221126`
- KswPLauncher (`com.wits.ksw`) app updated from `1.20_221124` to `1.20_221216`
    - Updated graphics for ID8 theme
    - Improvements to multi window handling on resume
- KswPMedia (`com.wits.ksw.media`) app updated from `1.2_221013` to `1.2_221213`
    - Added more implementations for ID8 theme
- SpeedPlay (`com.suding.speedplay`) app is no longer automatically installed (?)
- CenterService (`com.wits.pms`) app updated from `1.0_221117` to `1.0_221213`
    - Changes to support TXZ voice (?)
    - Split mic gain settings to separate values for M501 and M600 chipsets, where M600 is for Android 11 and 12 based units
    - Added new NetOTAUpdate class that handles firmware upgrades from USB storage
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.22_221124_goc` to `1.0.22_221213_goc`
    - Changes to music playback state detection
    - Changes to dimensions of dialogs/popups
    - Added support for ID8 skins (sport = red, efficient = default/blue, comfort = yellow)
- SystemUIWithLegacyRecents app updated
    - Added ID8 skin support
