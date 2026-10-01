---
id: "Ksw-R-M600_OS_v2.0.9-ota"
vendor: ksw
platform: m600
android: 11
date: 2022-04-22T08:46:02Z
signatures:
  md5: 617bdaef0ae1e714685a70de91927114
  sha1: d376cb609de6815ac97aa3db1388444eff13934d
  sha256: 71b7f42e81f400f8bf60024986aeb2d73167fd25acd55a80966584583f29fe17
---
#### Summary
- Small fixes: `ALS_ID7_UI` home menu focus, Bluetooth search state, video player libraries

#### Changes
- `ALS_ID7_UI`: the home screen's main-menu buttons get focus back when the launcher refreshes, instead of always losing it
- KswBt: stopping a device search also clears the "searching" state, so the pairing screen should no longer show a search as running (not tested; reverted in 2.1.5)
- KswBt: at start-up it no longer re-applies the colour skin itself
- KswPMedia: the bundled ijkplayer video libraries are replaced with different builds; what differs is not known
