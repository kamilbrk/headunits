---
id: "Ksw-T-M600_OS_v1.1.9-ota"
platform: "m600"
date: "2023-09-25T08:52:03Z"
signatures:
  md5: d4578e57ce55092a4426161f67889b19
  sha1: c0f8fb27c6f4b9e102e87cd6d26a22344d3edfad
  sha256: 9895a189c54b4f36918feb90ab5a1a8f6ec69ad5fd5a884a7e93bf2dbf40ad11
---
Changes since `Ksw-T-M600_OS_v1.1.3-ota`:
- New app: Ksw360Camera (`com.ivicar.avm`) version `1.0.1_230925`
- Lots of permissions with storage, camera, location and network access
- Activities around video settings, calibration, shop and license screens, recording, perhaps picture-in-picture / floating image, some unknown integration with receiving broadcasted events from Zlink
- Includes a certificate for `xinyao_url` which is at `http://121.41.17.229:30083`. References in code mention shopping in both `en` and `ch` store versions, perhaps hardware will be available on other markets. You will be able to pay within the app, through Wechat.
- Seems to have functionality around car doors, gearbox, power, radar, "double light", steering wheel, vehicle lights and vehicle speed. Radar related code has tests that seem to be about "dangerous levels" from four sides, almost like parking sensors. There are references to 2D, 3D and birdview modes, voice actions, "AVM RV Display", etc. Is this a third party camera with deep integration in KSW software, is this something like Torque or other OBD apps reading car details in real-time? Both?
- KswPLauncher (`com.wits.ksw`) app updated to `1.20_230918`
- Removed code around starting the 360 app (that was previously added in A13 1.1.3)
- Listens for `PACKAGE_REMOVED` broadcast to update cards, most likely to cleanup shortcuts to apps that have been uninstalled
- References to saving "old UI name" into system settings, perhaps a new generation of themes incoming?
- TingCar (`com.ximalaya.ting.android.car`) app updated from `3.0.1` to `5.0.1`
- APKInstaller (`com.wits.apk`) app updated from `1.0_20230824` to `1.0_20230916`
- New activity around importing aw360 files
- KswPMusic (`com.wits.ksw.music`) app updated from `1.2_230819` to `1.2_230923`
- Minor improvements to Zlink status handling, e.g. checking if there's a phone call in progress
- KswPVideo (`com.wits.ksw.video`) app updated from `1.2_230823` to `1.2_230923`
- Picture-in-picture changes to do with IviCar AVM 360 camera, seems like Video app will be receiving video stream from the new Ksw360Camera
- KswBt (`com.wits.ksw.bt`) app updated from `1.0.22_230818_feasy` to `1.0.22_230915_feasy`
- Handling for phone call status when Camera360 app is in foreground
- CenterService (`com.wits.pms`) app updated from `1.0_230822` to `1.0_230923`
- New internal settings about allowing certain apps to boot before boot animation completes and/or implementing a delay to continue boot animation until certain apps start:
  - `com.android.bluetooth`
  - `com.android.systemui`
  - `com.android.permissioncontroller`
  - `com.android.providers.media.module`
  - `com.android.launcher3`
  - `com.android.networkstack.process`
  - `com.android.shell`
  - `com.android.settings`
  - `com.wits.pms`
