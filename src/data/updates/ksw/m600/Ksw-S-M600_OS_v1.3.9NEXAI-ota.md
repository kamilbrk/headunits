---
id: "Ksw-S-M600_OS_v1.3.9NEXAI-ota"
vendor: ksw
platform: m600
android: 12
date: 2023-05-11T01:36:34Z
signatures:
  md5: ab55124fd6edc2987863304fbd045f52
  sha1: 12d7a453da7d59fd6dcef459289ce146c3f7145d
  sha256: aa37f851222d435427f38eeae1bc578f2b361708820cc27e0ec97ee9aee10f88
---
#### Summary
- New theme `Alfa_Romeo_V2`
- The combined media app is split into separate Music and Video apps
- New "360 boot up camera", "Turn signal control" and "Global Weather App" factory settings

#### Changes
- KswPLauncher (`com.wits.ksw`) app updated from `1.20_230410` to `1.20_230510`
  - Added `Alfa_Romeo_V2` theme (`UI_type` = `Alfa_Romeo_V2`): the Alfa Romeo menu plus a weather, date and temperature panel. It uses the Alfa Romeo settings and the ID7-style dashboard and app list
  - New settings:
    - 360 boot up camera: No camera use, Retrofit camera, Original car camera (`BootUpCamera`, sent to the MCU)
    - Turn signal control: Uncontrolled, Controlled (`TurnSignalControl`, sent to the MCU)
    - Global Weather App (`globalweather_app`): when off, the TXZ weather app (`com.txznet.weather`) is hidden from the app list
  - Unread-count badges ("99+" at most) on app icons in the ID7-style app list, set by other apps through the `com.wits.ksw.launcher.bubble.unread` broadcast
  - The Equalizer app is left out of the `LEXUS_LS_UI` / `LEXUS_LS_UI_V2` app pickers when "Equalizer APP" is off
  - Opening KuGou (`com.kugou.android`) tells the MCU to switch to source mode `13`
- KswPMedia (`com.wits.ksw.media`) app has been replaced with separate KswPMusic (`com.wits.ksw.music`) and KswPVideo (`com.wits.ksw.video`) apps, both `1.2_230510`
  - Each has its own launcher entry and background service; the screens are the same as before
  - The music scanner also picks up `.dsf` (DSD) and `.amr` files
  - Music can be chosen in Android's "Open with" dialog for audio files
- Split screen can no longer pair Music with Video, or either of them with Bluetooth
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.22_230410_feasy` to `1.0.22_230510_feasy`
  - Pairing and connecting dialogs appear to no longer stay open after leaving the app
  - Closing the "searching"/"connecting" dialog stops the search or connection
  - Siri activation from an iPhone, and a Huawei number made of eleven zeros, appear to no longer open an incoming call (not tested)
- CenterService (`com.wits.pms`) app updated from `1.0_230331` to `1.0_230420`
  - The TXZ voice assistant is sent gear changes; what it does with them is not known
  - The navigation key appears to open the navigation app in window mode when it is also the home-screen map app
- On first boot the sample songs and videos are always copied to internal storage, after waiting for storage to be ready
- CarplayZlink (`com.zjinnova.zlink`) app updated from `5.3.28` to `5.3.49`
