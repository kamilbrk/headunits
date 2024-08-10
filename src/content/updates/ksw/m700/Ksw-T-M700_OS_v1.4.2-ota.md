---
id: "Ksw-T-M700_OS_v1.4.2-ota"
vendor: ksw
platform: m700
android: 13
date: 2024-08-08T09:13:33Z
signatures:
  md5: 18c761fa4a9ec28834e33edbdcc432aa
  sha1: d2eb7f509ea49ce67583372c430ceacde8a972e7
  sha256: a3a123aeeebb349d467cd2ac70a5b391060ec0025dd4babbedf6b31247b20aa5
---
Summary:
- Zlink updated to `5.4.58` with split screen (?)

Changes since `Ksw-T-M700_OS_v1.4.0-ota` built 6 days earlier:
- Zlink updated from `5.4.54` to `5.4.58`, potentially supporting split screen since all activities are now marked as resizable
- OTA updates with Android 13 can now be also prefixed with `Witstek-T-` in addition to existing `Ksw-T-`, for example `Witstek-T-M785_OS_v1.4.2-ota.zip`
- Added a scrollbar to the apps view on [`EVOID9_ALS`](/headunits/themes/ksw/evoid9_als) theme
- The `<Screen_cast>` option in factory config is now read on boot to start capture service (?)
- The `su` binary has been swapped for `witsu`
- Build property `ro.build.tags` was changed from `test-keys` to `release-keys`
- GoogleTTS (text-to-speech) engine package is now pre-installed
- Other minor user interface adjustments across a handful of apps, e.g. changed fonts and sizes, resized elements and graphics, etc.

Modification points (provided by Witstek):
- Split screen】 Version: 1.3.4 When split screen, after the carplay call ends, exit the split screen interface
- ZLINK】 1.6.4, after playing the USB music, return to carplay to play music, the car plays the USB music, and the phone plays the carplay music (appears once)
- Support Apple Music
- The USB icon in the status bar is displayed at the bottom of the 1024X600 resolution
