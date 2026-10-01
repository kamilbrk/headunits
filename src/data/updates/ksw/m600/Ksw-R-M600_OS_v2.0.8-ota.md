---
id: "Ksw-R-M600_OS_v2.0.8-ota"
vendor: ksw
platform: m600
android: 11
date: 2022-04-20T07:23:47Z
signatures:
  md5: f187fb4db6705d9109b28ff2a75844ff
  sha1: 5d215d58c60dfe5b9fa2a203a038a0fc9e766768
  sha256: 816fac507565f2bafffbbbd18f64499849eb19799b15029cb9e763f2233c66ca
comparedTo:
  - ksw/m600/ksw-r-m600_os_v203-ota
---
#### Summary
- Bluetooth reworked: the Feasycom stack appears to run inside Android's Bluetooth stack, and new pairings ask yes/no instead of a PIN
- Bluetooth OBD-II adapters can be paired from the Bluetooth device list
- Steering-wheel call keys appear to work with Android Auto and Android screen mirroring through Zlink (not tested)
- Groundwork for TXZ car warnings and a third-party 360 camera app

#### Changes
- Bluetooth: the `blueware` service and `/system/bin/blueware` are removed. The Feasycom stack appears to live in a new `/system/lib64/libbluetooth_qti.so`
- Bluetooth: switching Bluetooth on or off in KswBt now switches Android's Bluetooth adapter
- Bluetooth: Android's own Bluetooth profiles (A2DP, HFP, PBAP, MAP, PAN, OPP, HID host) are turned off, presumably so they do not compete with the Feasycom stack
- Bluetooth pairing: secure simple pairing with a yes/no prompt replaces legacy PIN pairing (`PAIR_MODE` `0` to `2`)
- Bluetooth OBD-II: devices named `OBDII` are marked as OBD devices; tapping one offers to configure it over the serial port profile (SPP)
- Android Auto or Android screen mirroring (Zlink): the steering-wheel call key appears to answer or end calls through the Bluetooth phone connection (not tested). Wired CarPlay is now treated like wireless CarPlay here
- Repeated voice "volume up/down" commands no longer pile up
- Dialling from other apps: CenterService passes KswBt the plain phone number instead of `{number:…}`
- The location off/on toggle that 2.0.3 added for Google Maps also runs for Sygic (`com.sygic.aura`), with a 50 ms pause instead of 200 ms
- TXZ warnings (not visible yet): CenterService forwards door, seatbelt, fuel, speed and temperature status from the MCU to the voice assistant. A factory page for the alarm levels exists in KswPLauncher, but no menu opens it
- 360 camera (not visible yet): when reversing, CenterService starts `com.baony.avm360`, which is not in the firmware
- `ALS_ID7_UI`: tapping the skin button repeatedly within 1.5 seconds shows "Your operation is too frequent", and skin changes apply to the whole launcher
- `ALS_ID7_UI` dashboard: the rev counter needle is recalibrated (not tested)
- `Benz_NTG5` on 1920-wide screens: the labels under the home-screen icons sit higher
- `Audi_mib3_FY`: the equaliser sliders are re-laid out for 1280x480 screens
- Launcher: the dashboard and settings screens no longer appear in the recent apps list
- USB host/device switching also applies to `M501B` builds
- The `/sdcard/otapackage` updater reports a failure when no update file is found or the install fails
- TXZAdapter (`com.txznet.adapter`) app updated from `220325-84` to `220401-85`
- KswPLauncher (`com.wits.ksw`) app updated from `1.1.5` to `1.1.9`
