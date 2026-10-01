---
id: "Ksw-R-M600_OS_v2.0.3-ota"
vendor: ksw
platform: m600
android: 11
date: 2022-03-25T08:31:14Z
signatures:
  md5: ed14d3f5a6472894a7f095bed2ff89c0
  sha1: 999342b78eab1fcdfe0f7cd914121972b685b3fe
  sha256: 4be94f9ab52241d218a95ba54e389e2f5018c8c988baf85befdeb21d9af54686
---
#### Summary
- Sogou and iFlytek keyboards are included again
- Factory setting "MIC Gain" goes up to 20 again
- Groundwork for an updater that installs a firmware file from `/sdcard/otapackage`

#### Changes
- Keyboards: Sogou (`com.sohu.inputmethod.sogou` `11.0`) and iFlytek (`com.iflytek.inputmethod.google` `8.1.8212`) added back as system apps
- Factory settings: the "MIC Gain" slider goes from 0-12 to 0-20
- New CenterService updater: it installs a file from `/sdcard/otapackage` whose name contains `Ksw-R-M600_OS_v` and `ota.zip`. Nothing in this firmware appears to download to that folder or start it
- Steering wheel voice key: with Android Auto, AirPlay or Android screen mirroring connected through Zlink, it now appears to open the phone's own assistant, as CarPlay already did
- Google Maps: every time it comes to the front, CenterService switches location off and back on 200 ms later
- At boot, the "Txzing Assistant" factory setting now appears to actually switch the voice assistant on or off
- Volume up/down from voice commands takes effect 300 ms after the command
- TXZAdapter (`com.txznet.adapter`) updated from `220217-83` to `220325-84`; it no longer speaks the boot welcome message
- NTG6 system settings: the "Brightness" label moves closer to its control
- Telephony: with the 14-digit IMEI option on, the IMEI appears to no longer be shortened
- New boot service `lnbt` (`/system/bin/ln_bt.sh`) links Zlink's Bluetooth devices under `/dev` when `persist.ln.bt=1`; nothing in this firmware appears to set that
