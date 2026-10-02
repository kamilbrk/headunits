---
id: "Ksw-R-M600_OS_v2.2.3-ota"
vendor: ksw
platform: m600
android: 11
date: 2022-07-07T02:29:03Z
signatures:
  md5: 72d4c658985e304292169f8a29dfaaa1
  sha1: 14a6f7b65cf1d3b4417c2b99bba95e9ae914542c
  sha256: 622a5ff2841e624c165d439ecbdeb7668c7c3fc317cbbceda5c78b30fea32ecd
---
#### Summary
- Bluetooth and media apps get `BMW_ID8_UI` screens
- "Front view mirror setting" appears on more factory "Function" page layouts
- Tapping the clock in the notification shade no longer opens the alarm app
- Zlink updated to `5.2.52`

#### Changes
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.22_220518_feasy` to `1.0.22_220706_feasy_1`
  - New `BMW_ID8_UI` phone screens: dial pad, contacts, call history, paired devices, Bluetooth music and an in-call screen. The launcher has had a `BMW_ID8_UI` home screen since 2.1.5
- KswPMedia (`com.wits.ksw.media`) app updated from `1.2_220527_1` to `1.2_220707`
  - New `BMW_ID8_UI` music and video player and file-list screens
  - Dedicated `ALS_ID7_UI` music and video layouts for 1280x480 screens
- Both apps take the `BMW_ID8_UI` colour skin from a new `ID8_skin` setting, which nothing in this build appears to write
- Both apps treat the new theme name `BMW_EVO_ID7_V2` like `BMW_EVO_ID7`; the launcher does not know it yet
- KswPLauncher (`com.wits.ksw`) app updated from `1.20_220614_1` to `1.20_220706`
  - "Front view mirror setting" is also on the larger-screen and `ALS_ID7_UI` versions of the factory "Function" page. On larger screens the 2.2.0 page looked for a checkbox it did not have, a probable crash (not tested), which this avoids. On `ALS_ID7_UI` the checkbox is not wired to anything
  - The Android version in "About" can show a number higher than 11 if the system stores one (see 2.2.4)
- SystemUI: tapping the clock in the notification shade no longer opens the alarm app
- CarplayZlink (`com.zjinnova.zlink`) app updated from `5.2.49` to `5.2.52`
- TXZAdapter (`com.txznet.adapter`) app updated from `220401-85` to `220620-84`
