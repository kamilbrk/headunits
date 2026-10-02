---
id: "Ksw-S-M600_OS_v1.2.1NEXAI-ota"
vendor: ksw
platform: m600
android: 12
date: 2023-01-29T05:52:27Z
signatures:
  md5: 9e9771368de07b70ea6c3d9409aaa336
  sha1: a1cbd09d31708bcdf44498ad77a75d3533ff2eff
  sha256: abb766449d36ab88faa36f534f2c8d15a6a1937cb09e97ad8e72d862bbe9c0e1
---
#### Summary
- New theme `UI_GS_ID8`, a BMW ID8-style home screen with a scrolling row of cards
- KswBt and the media app can no longer share the screen in split screen
- Groundwork for Android 13 system updates
- The voice assistant asks for the unit's IMEI as its ID, instead of one fixed ID for every unit

#### Changes
- KswPLauncher (`com.wits.ksw`) app updated from `1.20_221213_2` to `1.20_230129`
  - New theme `UI_GS_ID8`: a row of cards that snaps to each card, and a left bar with "APPS" plus four shortcuts you can change
  - `UI_GS_ID8` has its own "EDITOR MODE" (not tested), "CHANGE MODUS" ("PERSONAL", "SPORT", "EFFICIENT") and settings menu, and uses the `BMW_ID8_UI` dashboard, app list, Bluetooth and media screens
  - Handles an Android 13 boot logo file (`mylogo13.zip`)
- Split screen: choosing KswBt and the media app for the two halves shows "The app does not support simultaneous split screen"
- The Recents button ignores a second press within one second
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.22_221213_feasy` to `1.0.22_230111_feasy`
  - Layouts for a 634dp-wide window, which appears to be half of a 1920x720 screen
  - The call history reloads when an empty call history page is opened
- KswPMedia (`com.wits.ksw.media`) app updated from `1.2_221213_1` to `1.2_230111`
  - Layouts for a 634dp-wide window
  - When a CarPlay / Android Auto call starts, the video player appears to pause and resume after the call (not tested)
- Car Care (`com.wits.carcare`) app updated from `1.0_220809` to `1.0_221221`, with a 634dp-wide layout
- CenterService (`com.wits.pms`) app updated from `1.0_221208` to `1.0_230111`
  - System updates also accept `Ksw-T-M600_OS_v…ota.zip` packages
- Toppal Voice (`com.txznet.smartadapter`) version code updated from `221213` to `221222`
  - The voice engine ID was the fixed string `ZJY202212121059` on every unit; it now asks Android for the unit's IMEI, which Android may not grant
- CarplayZlink (`com.zjinnova.zlink`) app updated from `5.3.20` to `5.3.28`
