---
id: "Ksw-T-M600_OS_v1.3.8-ota"
vendor: ksw
platform: m600
date: 2023-12-01T07:27:56Z
signatures:
  md5: 24a78587cc1c9a48a3244ae3cad0a481
  sha1: 999d60a715570c669b2cdc000ddb104b202589f0
  sha256: 22601268897cb91f9981ca8ceffec1e587e4dd396e17586969d9f7b294f09f83
---
Summary:
- Zlink update 5.4.23 with Huawei HiCar graphics
- Czech translations
- New [`UI_MBUX_YO`](/headunits/themes/ksw/ui_mbux_yo) theme which seems to be a variation of [`Benz_MBUX_2021`](/headunits/themes/ksw/benz_mbux_2021)
- Greetings from Android Automotive Discord https://discord.gg/Ex8e6qE2eR
- Some internal changes in KSW Bluetooth app around A2DP AVRCP profiles and resuming playback
- Further work on Ksw 360 Camera app

Changes since `Ksw-T-M600_OS_v1.2.9-ota`:
- CarplayZlink (`com.zjinnova.zlink`) app updated from `5.4.19` to `5.4.23`
  - Updated Tencent Legu packer from `4.5.2.5` to `4.5.3.9`
  - Removed code to check CPU architecture (x86/armeabi/armeabi-v7a)
  - Added Huawei HiCar graphics
- Ksw360Camera (`com.ivicar.avm`) app updated from `1.0.1_231103` to `1.0.1_231129`
  - Added labels for custom car number, custom license plates colour, car montage width setting, floating view
  - Added handling for autostart via the `BOOT_COMPLETED` event
- APKInstaller (`com.wits.apk`) app updated from `1.0_20231010` to `1.0_20231117`
- KSWAirConditioner (`com.wits.ksw.airc`) app updated from `1.0_230803` to `1.0_231117`
- KswPLauncher (`com.wits.ksw`) app updated from `1.20_231103` to `1.20_231201`
  - Added Czech translations
  - Added support for Benz [`UI_MBUX_YO`](/headunits/themes/ksw/ui_mbux_yo) theme (which seems to be a variation of `Benz_MBUX_2021`)
  - Improvements/internal cache for a list of installed applications
  - Fixed lots of themes to include `pt`, `tr`, `vi`, `pl`, `ar`, `ja`, `iw/IL`, `el`, `th`, `hr`, `cs` locale options
  - Improvements for Ksw360Camera app
- KswPMusic (`com.wits.ksw.music`) app updated from `1.2_230923` to `1.2_231117`
  - Added support for Benz [`UI_MBUX_YO`](/headunits/themes/ksw/ui_mbux_yo) theme
  - Added Czech translations
  - Improved error handling to autoplay next song
- KswPVideo (`com.wits.ksw.video`) app updated from `1.2_231106` to `1.2_231129`
  - Added support for Benz [`UI_MBUX_YO`](/headunits/themes/ksw/ui_mbux_yo) theme
  - Added Czech translations
  - Improved error handling to autoplay next video
  - Added handling for Huawei HiCar wired/wireless connection events
- kswEq (`com.wits.csp.eq`) app updated from `1.01_230720` to `1.01_231121`
  - Added support for Benz [`UI_MBUX_YO`](/headunits/themes/ksw/ui_mbux_yo) theme
  - Added Czech translations
  - Added Croatian translations …file with Chinese labels inside, so not so much
- CenterService (`com.wits.pms`) app updated from `1.0_231031` to `1.0_231121`
  - Added handling for Huawei HiCar
  - Added Czech locale support
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.22_231106_feasy` to `1.0.22_231129_feasy`
  - Added support for Benz [`UI_MBUX_YO`](/headunits/themes/ksw/ui_mbux_yo) theme
  - Added Czech translations
  - Improvements for Ksw360Camera app
  - Changed `CLOSE_A2DP_AVRCP` profile from `50185` to `246793`
  - Changed `OPEN_A2DP_AVRCP` profile from `50345` to `246953`
  - Improvements to resuming playback after returning to the app
  - Added handling for ID8 skin change events
- TxzOta (`com.txznet.ota`) app updated from `1.1.3` to `1.1.5`
  - Added a class for "multi file download manager" using okhttp3
