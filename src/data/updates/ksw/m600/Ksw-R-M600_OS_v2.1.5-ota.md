---
id: "Ksw-R-M600_OS_v2.1.5-ota"
vendor: ksw
platform: m600
android: 11
date: 2022-05-18T09:07:43Z
signatures:
  md5: d468ec2068844424b0ee259bb7dcb0a6
  sha1: a3e0d1186ddfae638bcb0a0525a6f1df6a933b0b
  sha256: 9db803dce5655472bc24fc48c5a23a48e392a90e88472dc83b2b692cf7ac0e2f
---
#### Summary
- Builds `2.1.0` to `2.1.4` are not on this site, so some of these changes may have first appeared in one of them
- First, unfinished `BMW_ID8_UI` home screen
- `ALS_ID7_UI` colour skin appears to survive a restart
- Button fixes for `Benz_MBUX_2021`, `Benz_MBUX_2021_KSW` and CAN car keys

#### Changes
- `BMW_ID8_UI` gets a home screen on the Android 11 M600 firmware, but only a placeholder: a row of eight identical "Navigation" tiles with nothing to tap
- `ALS_ID7_UI`: the chosen colour skin is applied again when the launcher, media and Bluetooth apps start, which appears to make it survive a restart. The home-screen music ring follows the skin colour
- `ALS_ID7_UI` video: the Chinese "Type: unknown" line under each file is removed
- `Audi_mib3`, `Audi_mib3_FY`, `Audi_mib3_ty` video: in what appear to be split-screen widths, tapping the video hides or shows the control bars
- `Benz_MBUX_2021` and `Benz_MBUX_2021_KSW`: a home-screen tile appears to stay highlighted after a key press
- Car buttons that arrive over the CAN bus are debounced (150 ms), so a single press should no longer register twice (not tested)
- Bluetooth music (ID7 themes): the progress bar can no longer be dragged
- If the default navigation app cannot be opened, the launcher appears to still fall back to AutoNavi (with "Google Apps" off). Other shortcuts just show "not installed"
- KswPLauncher (`com.wits.ksw`) app updated from `1.1.9` to `1.20_220518`
- KswPMedia (`com.wits.ksw.media`) app updated from `1.2_11_13` to `1.2_220517`
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.22_0107` to `1.0.22_220518_feasy`
- Sogou keyboard (`com.sohu.inputmethod.sogou`) app updated from `11.0` to `11.3`
