---
section: "Function"
settings:  
  - name: "USB HOST"
    configKey: USB_HOST
    control: checkbox
    onValue: 1
    offValue: 0
    description: "Allow USB devices to be available to Android system. Switch this off if you want to run fastboot or other related tools."
  - name: "Zlink"
    configKey: zlink_auto_start # See CenterService.BootReceiver. Also, when either `zlink_auto_start` or `hotspot_open` (undocumented) options are true, Settings.MyReceiver will run `start5GTether` to set Wi-FI AP config and start tethering.
    control: checkbox
    onValue: 1
    offValue: 0
    description: "When enabled, Zlink should automatically start on boot. Additionally, it will take over Wi-Fi to create and maintain its wireless hotspot, therefore you will not be able to use Wi-Fi for other purposes."
  - name: "HiCar"
    configKey: zlink_hicar # See CenterService.BootReceiver
    control: checkbox
    onValue: 1
    offValue: 0
    description: "When enabled, Zlink should automatically start on boot. It will also directly open the Huawei HiCar mode/screen in Zlink. Most likely dependant on the \"Zlink\" option above."
  - name: "Google Apps"
    configKey: GoogleAPP
    control: checkbox
    onValue: 1
    offValue: 0
  - name: "AUX"
    configKey: AUX_Type
    control: checkbox
    onValue: 1
    offValue: 0
  - name: "DTV"
    configKey: DTV_Type
    control: checkbox
    onValue: 1
    offValue: 0
  - name: "F_CAM"
    configKey: Front_view_camera
    control: checkbox
    onValue: 1
    offValue: 0
  - name: "Txzing Assistant"
    configKey: Support_TXZ
    control: checkbox
    onValue: 1
    offValue: 0
  - name: "BT"
    control: checkbox
    onValue: 1
    offValue: 0
    editable: false
    description: "Which Bluetooth the unit uses is set by \"Bluetooth Selection\" below, which owns the `BT_Type` key. What this box does on its own is not known."
  - name: "Touch data continuously sent"
    configKey: touch_continuous_send
    control: checkbox
    onValue: 1
    offValue: 0
  - name: "Equaliser App"
    nameOld: "Equalizer APP"
    configKey: EQ_app
    control: checkbox
    onValue: 1
    offValue: 0
  - name: "Global Weather App"
    configKey: globalweather_app
    control: checkbox
    onValue: 1
    offValue: 0
  - name: "360APK"
    configKey: APK360
    control: checkbox
    unverified: true
    onValue: 1
    offValue: 0
  - name: "Boot Mode Memory"
    nameOld: "Remember The Last Mode"
    configKey: Default_PowerBoot
    description: "You can choose what system is automatically launched on start-up"
    children:
      - name: "Enable"
        description: "Try to remember last used interface and use that (OEM or Android)"
        configValue: 0
        control: radio
      - name: "Original Car Interface"
        nameOld: "To OEM System"
        description: "Start with OEM system, where you can switch to Android later"
        configValue: 1
        control: radio
      - name: "Android Interface"
        nameOld: "To Android Homepage"
        description: "Start with Android, where you can switch to OEM system later"
        configValue: 2
        control: radio
  - name: "DVR"
    configKey: DVR_Type
    description: "Choose type of the DVR module"
    children:
      - name: "Close"
        configValue: 0
        control: radio
        description: "Turn off DVR"
      - name: "CVBS DVR"
        configValue: 1
        control: radio
      - name: "USB DVR"
        configValue: 2
        control: radio
        description: "Set the `<SupportDvrAppList>` to supply supported application package names. Then, to select an app to use USB DVR, use the `<DVRApk_PackageName>` setting separately, which is often set to `com.ankai.cardvr` by default on some devices."
  - name: "Bluetooth Selection"
    configKey: BT_Type
    children:
      - name: "Original Car Bluetooth"
        nameOld: "OEM Bluetooth"
        configValue: 1
        control: radio
      - name: "Additional Bluetooth"
        nameOld: "Android Bluetooth"
        configValue: 0
        control: radio
  - name: "Amplifier Selection"
    configKey: AMP_Type
    children:
      - name: "Original Car Amplifier"
        nameOld: "OEM Amplifier"
        configValue: 0
        control: radio
      - name: "External Amplifier Box"
        nameOld: "Aftermarket Amplifier"
        configValue: 1
        control: radio
  - name: "360 Camera Type"
    nameOld: "360 Camera"
    children:
      - name: "CVBS Camera"
        control: radio
      - name: "VGA Camera"
        control: radio
  - name: "Automatic Backlight Control"
    nameOld: "Automatic Brightness"
    children:
      - name: "Sidelight Control"
        nameOld: "Width Lamp Control"
        control: radio
      - name: "Close"
        control: radio
  - name: "Unit Selection"
    configKey: DashBoardUnit
    children:
      - name: "Metric Unit"
        configValue: 0
        control: radio
      - name: "Imperial Unit"
        configValue: 1
        control: radio
  - name: "AHD Camera Selection"
    configKey: AHD_cam_Select
    children:
      - name: "Automatic Detection"
        configValue: 0
        control: radio
      - name: "AHD-1080P-30HZ"
        configValue: 1
        control: radio
      - name: "AHD-1080P-25HZ"
        configValue: 2
        control: radio
      - name: "AHD-720P-30HZ"
        configValue: 3
        control: radio
      - name: "AHD-720P-25HZ"
        configValue: 4
        control: radio
      - name: "AHD-720P-50HZ"
        configValue: 5
        control: radio
      - name: "CVBS-NTSC"
        configValue: 6
        control: radio
      - name: "CVBS-PAL"
        configValue: 7
        control: radio
  - name: "Disable Video In Motion"
    configKey: DoNotPlayVideosWhileDriving
    control: checkbox
    onValue: 1
    offValue: 0
  - name: "Front view mirror setting"
    configKey: forwardCamMirror
    unverified: true
    control: checkbox
    onValue: 1
    offValue: 0
---
