---
id: "Ksw-Q-Userdebug_OS_v4.2.9-ota"
vendor: ksw
platform: m501
date: 2023-12-25T09:07:23Z
signatures:
  md5: 2a63d501d6daa9388f64ffcb5cc81bb6
  sha1: 84be79669dd890c61e64ef5401b15b4d3187fa4a
  sha256: a65dddc361de19eae1dbe91a3ade81b47c06aeddf583ac250ca38de3f8b82db7
---
Summary:
- Looks like Android 10 updates for M501/SD625 are recently showing up more often and are kept in line with latest Android 13 images for M600/SD662 and M700/SD680
- Launcher and Zlink are updated to latest versions

Changes since `Ksw-Q-Userdebug_OS_v4.2.0-ota`:
- CarplayZlink (`com.zjinnova.zlink`) app updated from `5.4.2` to `5.4.25`
    - Same updates as in M600 A13 1.4.0
    - Added Huawei HiCar graphics and even more HiCar labels than A13 version
- KswPLauncher (`com.wits.ksw`) app updated from `1.20_230907` to `1.20_231222`
    - Same updates as in M600 A13 1.4.4
    - Added intents for adding/removing/replacing apps, together with performance improvements around detecting changes to installed apps
    - Added permission to receive boot completed event
    - Improvements to handling available locales/languages
- TxzOta (`com.txznet.ota`) app updated from `1.1.3` to `1.1.5`
    - Same updates as in M600 A13 1.3.8
    - Added a class for "multi file download manager" using okhttp3
- Framework and system utils
    - Added code to check RAM information from `/mnt/vendor/persist/OEM/memoryvalue_501a`
