---
id: "Ksw-S-M600_OS_v1.1.4NEXAI-ota"
vendor: ksw
platform: m600
android: 12
date: 2022-12-15T06:17:54Z
comparedTo:
  - ksw/m600/ksw-s-m600_os_v120-ota
signatures:
  md5: 2913ca28c5cf617e69f514d61e6388dc
  sha1: 2ea48d3f8bcea20691abe8d1624dc8f96fbaa54e
  sha256: eb63b45ccc5ae76fd61c0f4e5d55d4c8588087649e9d91d06ebe6df396a836c2
---
#### Summary
- First Android 12 NEXAI build: the Chinese TXZ voice assistant is replaced by NEXAI ("Hey Nex")
- The 1.1.4 number does not mean it is older than 1.2.0
- Vendor handling for split screen
- Google Assistant, the Google app, Gboard and eCar AppManager added; iFlytek and the Files app removed
- New "Car Care" app for the voice assistant's speed and fuel warnings, which may not be installed
- Changes to: `BMW_ID8_UI` bass/middle/treble, the air-conditioning popup on Audi themes, the mph speedometer needle, hardware video decoding

#### Changes
- Voice engine `com.txznet.txz` (TXZCore) goes from the Chinese `3.6.44` to the overseas `4.1.0_17`, with built-in US-English speech recognition and command files for 22 locales
- New "Toppal Service" (`com.txznet.aipal` `2.0.0`) handles NEXAI activation by QR code, which needs internet
- New "Toppal Voice" (`com.txznet.smartadapter` `YC-KSW-A-4.0.0`) holds the assistant's settings: wake-up word, language downloads, voice, default music, navigation and video apps
- The Chinese `com.txznet.adapter` is removed. As on Android 11, first-boot setup installs "Toppal Voice" only when "Google Apps" is on
- "Toppal Voice" has "Upload Log" / "Upload Voice" buttons (`oss.txzing.com`), and the apps talk to several `txzing.com` addresses, some over plain HTTP
- New "Car Care" app (`com.wits.carcare` `1.0_220809`, in `PreInstall`) with "Speed warning" and "Fuel warning" sliders. No install step for it was found, so it may not be installed
- Google Assistant (`0.1.187945513`), the Google app (`11.22.11.21`) and Gboard (`8.1.7.241875604`) added as system apps, switched with the other Google apps
- iFlytek keyboard (`com.iflytek.inputmethod.google`) removed. Sogou moves to `/system/PreInstall`; nothing in the firmware was found to install it
- Android's Files app (`DocumentsUI`) removed
- eCar AppManager (`com.ecar.AppManager` `1.0.0.20`) added
- Split screen: the status bar appears to be hidden and the Recents button disabled while two apps share the screen (not tested); a swipe down shows the status bar for two seconds; the same app on both sides is refused
- Window open and close animations switched off, and the system swipe gesture edge grows from 24dp to 60dp
- CenterService (`com.wits.pms`) app updated from `1.0_221031` to `1.0_221208`
  - "MIC Gain" is stored as `mic_gain_m600` instead of `Mic_gain`, so a gain set on 1.2.0 probably reads as unset after the update (not tested)
- `BMW_ID8_UI`: bass, middle and treble are saved as 0–24 like every other theme
- `BMW_ID8_UI`: the Weather card can be deleted in edit mode
- Audi themes: the factory "Air Conditioner" checkbox is shown and defaults to on, so the air-conditioning popup is no longer always off
- The factory "Control Panel" option is shown only for Benz themes
- Dashboard gauges: in mph the speed needle is converted before it is drawn
- KswPMedia (`com.wits.ksw.media`) app updated from `1.2_221013` to `1.2_221213_1`
  - Videos below 2000 pixels in both dimensions use hardware decoding; before, every video was software-decoded
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.22_221103_feasy` to `1.0.22_221213_feasy`
  - The phonebook is saved for each phone and should show straight away on reconnect (not tested)
- APKInstaller (`com.wits.apk`) app updated from `1.0` to `1.0_20221126`
- CarplayZlink (`com.zjinnova.zlink`) app updated from `5.3.6` to `5.3.20`
- TXZ Weather (`com.txznet.weather`) app updated from `1.0.5_3` to `1.0.5_4`
- The fourth built-in boot logo (`image_004`) is removed
