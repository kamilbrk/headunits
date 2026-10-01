---
id: "Ksw-R-M600_OS_v2.4.4-ota"
vendor: ksw
platform: m600
android: 11
date: 2022-11-25T08:17:47Z
signatures:
  md5: 651e17f9607ff3bed3938bd3ebbd65d7
  sha1: d01f438a21cbd48fe83e1fcedcb82eea3042dc29
  sha256: 905417b401b5ff41a73b166be576046fb3f110bee0ac58680f7498e1c63d62b0
comparedTo:
  - ksw/m600/ksw-r-m600_os_v242-ota
---
#### Summary
- New "FL Speaker Enable" and "Speed Type Selection" factory settings
- Video player uses hardware decoding again for videos below 2K
- iFlytek keyboard removed, and Sogou moves out of the system apps
- The KSW-branded boot logo added in 2.4.2 is removed again

#### Changes
- Factory settings > "Vehicle": new "FL Speaker Enable" (`Front_left`) and "Speed Type Selection" (`Speed_type`) options, passed straight to the MCU. What "Speed Type" changes on the car side is not known
- Factory settings > "Vehicle": "Control Panel" is shown only on Benz themes, and "Air Conditioner" is also offered for Audi
- Factory settings: the "Screen cast - MS9120" checkbox is hidden again, after earlier builds forced it visible
- `LEXUS_LS_UI` and `LEXUS_LS_UI_V2`: an "AC" tile follows the factory "AC Control" setting
- `UI_KSW_MBUX_1024`: gets the control panel button that `UI_KSW_ID7` already had
- `UI_NTG6_FY_V2`: the home cards are reordered, with a new "PhoneLink" card
- `BMW_ID8_UI`: the weather card can be removed in edit mode, and the EQ bass, mid and treble bars can be dragged
- `Common_UI_GS_UG`: the "More Apps" and "PhoneLink" tiles swap places
- App list: with "Google Apps" off, Google Assistant is hidden too
- KswPMedia (`com.wits.ksw.media`) app updated from `1.2_221013` to `1.2_221125`
  - Videos below 2000 px in both dimensions use hardware decoding
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.22_221013_feasy` to `1.0.22_221125_feasy`
  - During a call the TXZ voice assistant is put to sleep instead of switched off
  - The call screen closes if Bluetooth is switched off
  - The connected flag read by the launcher and TXZ should drift out of sync less often (not tested)
- CenterService (`com.wits.pms`) app updated from `1.0_221019` to `1.0_221117`
  - At boot the TXZ voice assistant is again switched on or off from the saved `Support_TXZ` value
  - MCU update: a file whose checksum does not match appears to be rejected before anything is sent
- iFlytek keyboard (`com.iflytek.inputmethod.google`) removed. Sogou moves to `/system/PreInstall`; nothing in the firmware was found to install it
- The fourth built-in boot logo (`imagefv_004`) added in 2.4.2 is removed
- CarplayZlink (`com.zjinnova.zlink`) app updated from `5.3.6` to `5.3.18`
- TXZAdapter (`com.txznet.adapter`) app updated from `221018-84` to `221116-84`
- TXZ Weather (`com.txznet.weather`) app updated from `1.0.5_2` to `1.0.5_4`
- KswPLauncher (`com.wits.ksw`) app updated from `1.20_221019` to `1.20_221124`; its images are re-encoded from PNG to WebP, shrinking it from 231 MB to 151 MB
