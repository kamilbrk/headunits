---
id: "Ksw-R-M600_OS_v1.7.2NEXAI-ota"
vendor: ksw
platform: m600
android: 11
date: 2022-04-12T05:48:31Z
signatures:
  md5: b326b2d86860ed370bae97724877bed2
  sha1: b1e0fdd03a5529eb6806ca703fe9772ad1551047
  sha256: 3206458e6e1c7b10eba1bd0fd6853f64e2c0937b288a91505af5c5b88a3336bd
---
:::warning
The NEXAI assistant checks its activation over unencrypted HTTP, and its Device Info screen has "Upload Log" and "Upload Voice" buttons that, after a confirmation, upload the assistant's log and voice folders to TXZ's servers.
:::

#### Summary
- NEXAI build based on `Ksw-R-M600_OS_v2.0.3-ota`; the 1.7.2 number does not mean it is older than 2.0.3
- The Chinese TXZ voice assistant is replaced by TXZ's overseas assistant, NEXAI ("Hey Nex")
- NEXAI has to be activated online with the NEXAI app
- Launcher, themes, KSW settings, media and air-conditioning apps are byte-identical to 2.0.3

#### Changes
- Voice engine `com.txznet.txz` (TXZCore) goes from the Chinese `3.6.44` to the overseas `3.3.3_2`, with Cerence US-English speech recognition and Vocalizer text-to-speech
- New "Toppal Service" (`com.txznet.aipal` `2.0.0`) handles NEXAI activation by QR code, which needs internet, and lists "Basic Edition", "Standard Edition" and "Premium Edition"
- New "Toppal Voice" (`com.txznet.smartadapter` `YC-KSW-SH-3.3.0`) holds the assistant's settings: wake-up word, language downloads, voice, default music, navigation and video apps, and more
- The Chinese `com.txznet.adapter` is removed. First-boot setup installs "Toppal Voice" only when "Google Apps" is on, so the assistant probably needs "Google Apps" on (not tested)
- "Toppal Voice" has "Upload Log" and "Upload Voice" buttons that send the `/sdcard/txz/log` and `/sdcard/txz/voice` folders to `oss.txzing.com`
- Activation is checked over plain HTTP at `abroad-license.txzing.com`
- `com.txznet.aipal` appears to get location and storage access automatically
- Wi-Fi hotspot: when the unit moves the hotspot to 5 GHz it sets WPA2 security again, unless "Security" was changed by hand. The hotspot password is written to the system log
- Wi-Fi driver settings `gindoor_channel_support=1` and `etsi13_srd_chan_in_master_mode=1` appear to allow the hotspot on indoor-only and 5.8 GHz short-range channels
- CenterService can receive door, seat belt, fuel, speed and temperature warnings from the MCU for the voice assistant; nothing in this firmware appears to use them yet
- Several voice "volume up" or "volume down" commands within 300 ms now count as one step
- Voice dialling: CenterService sends KswBt the bare number instead of `{number:…}`
- USB mode switching uses the M600 handling on any M600 or M501B build
- The `/sdcard/otapackage` updater added in 2.0.3 reports an error when there is no update file or the install fails
