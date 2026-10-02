---
id: "Ksw-R-M600_OS_v1.9.9-ota"
vendor: ksw
platform: m600
android: 11
date: 2022-02-24T03:56:32Z
signatures:
  md5: 9eaec7246bb252db7a22955ac072d628
  sha1: d6304c6991f725536efb3ffed2c232be1129fa12
  sha256: 0187da7d891f0bb2c4515795e351c98219c5de2ac72bd343b1da3920f0224ebc
---
#### Summary
- New factory setting "Reverse exit time configuration"
- The first "AHD Camera Selection" option is renamed "Automatic Detection"
- Bluetooth calls appear to get the microphone straight away when the TXZ voice assistant is not running (not tested)

#### Changes
- New factory page "Reverse exit time configuration": "Exit according to the original vehicle agreement" or "Custom exit time" with a 0-10 slider (`Reverse_time`, sent to the MCU; the unit of the value is not stated)
- Factory "Function" page: the first "AHD Camera Selection" choice is renamed from "Not Supported" to "Automatic Detection"; the stored value appears unchanged
- KswBt and CenterService: a call takes the microphone immediately when the TXZ voice assistant is not installed or not started yet; otherwise it still waits for TXZ to release it (not tested)
- KswBt: the call mute state from the Bluetooth module appears to be read correctly now
- Launcher: with "Google Apps" off, an AutoNavi map that cannot be opened yet shows "Application installation in progress"
- `Audi_mib3_FY` home screen and dashboard get 1280x480 layouts
- Audio: "ADC1 Volume" in `mixer_paths_qrd.xml` drops from 12 to 6 and the speaker calibration file changes; the effect is not known
- TXZ voice assistant adapter (`TXZAdapter.apk`) updated from `220107-77` to `220217-83`
- KswPMedia (`com.wits.ksw.media`) app updated from `1.2_11_11` to `1.2_11_12`
