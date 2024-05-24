---
id: "Ksw-T-M600_OS_v1.4.4-ota"
vendor: ksw
platform: m600
date: 2023-12-27T11:08:24Z
signatures:
  md5: d9b20236d8753463e9a7ab6608163a59
  sha1: 8d7fa62686de537a2f528d2708ce49260b1066f5
  sha256: 4b78ccf89d847513343c445faf9213ee251849f3c17aba0650737ee1b3b64dd9
---
Summary:
- Minor performance updates in main launcher

Changes since `Ksw-T-M600_OS_v1.4.0-ota` built 20 days earlier:
- Ksw360Camera (`com.ivicam.avm`) app updated from `1.0.1_231207` to `1.0.1_231227`
  - Changes to splash activity
  - Support for 1280x720 screen resolution
- KswPLauncher (`com.wits.ksw`) app updated from `1.20_231201` to `1.20_231222`
  - Added intents for adding/removing/replacing apps, together with performance improvements around detecting changes to installed apps
  - Added permission to receive boot completed event
  - Improvements to handling available locales/languages
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.22_231129_feasy` to `1.0.22_231215_feasy`
  - Changes to how Ksw360Camera app activity is detected
- Wits-framework-res
  - New `third_system_app_whitelist` that contains `com.txznet.txz`
