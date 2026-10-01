---
id: "Ksw-R-M600_OS_v2.3.6-ota"
vendor: ksw
platform: m600
android: 11
date: 2022-09-21T07:37:29Z
signatures:
  md5: 5d04e26c9b3260b3142bf9166edfe845
  sha1: 624f3570c7661798a7b7aaa963940a983480af68
  sha256: 4989a7953109b534067c29f423de7fe77d4055a7ac2e2def6696ec3a0d51124d
---
#### Summary
- New Wi-Fi chip firmware, installed by CenterService at the first boot after the update
- Car-brand badges removed from the launcher's car pictures and logos
- New full-screen music player for `BMW_ID8_UI`
- Zlink updated to `5.2.72`

#### Changes
- CenterService (`com.wits.pms`) app updated from `1.0_220726` to `1.0_220915`
  - At the first boot after the update it replaces the Wi-Fi firmware on the modem partition with `WLAN.HL.3.2.4-01022` and offers a reboot ("Wifi Firmware UPDATE")
  - The modem partition is now mounted read-write, apparently to make that copy possible
- KswPLauncher (`com.wits.ksw`) app updated from `1.20_220818` to `1.20_220913`
  - Car pictures and brand logos redrawn without the manufacturer badge (for example the Audi rings and the "Audi" / "Alfa Romeo" logos)
  - Mercedes MBUX themes: the "me" icon becomes a person and the Android Auto robot an arrow
  - With `e_car` at `0`, the eCar assistant is also hidden from the app list
- KswPMedia (`com.wits.ksw.media`) app updated from `1.2_220816` to `1.2_220913`
  - `BMW_ID8_UI`: new full-screen music player with a favourite button, opened by itself after 10 seconds without input while music plays
  - `BMW_ID8_UI`: the music and video lists appear to keep focus for the rotary controller while scrolling
  - The music player layout now also covers 634dp-wide windows
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.22_220815_feasy_1` to `1.0.22_220915_feasy`
  - Waking Siri on an iPhone no longer opens the in-call screen
  - Deleting a paired phone in the ID7-style list also disconnects it
- CarplayZlink (`com.zjinnova.zlink`) app updated from `5.2.68` to `5.2.72`
  - New "CarPlay", "Android Auto" and "Mirroring" launcher icons, disabled by default
  - New "Connection Error" and "Resolution change detected, need to reload" dialogs
  - Plain HTTP is allowed to any server
  - Targets API 23, so Android should ask for its permissions at runtime
- Android Wi-Fi service: Zlink may change Wi-Fi configurations even when it is not the app on screen
- Android Settings: Melon, Naver Map, TomVPN, KimGiSa, Amazon Music and Spotify are added to the battery-optimisation allow list
- Wi-Fi hotspot (`hostapd`): the Zjinnova hook that appears to have added an Apple vendor element is gone
