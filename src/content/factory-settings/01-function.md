---
section: "Function"
settings:  
  - name: "USB HOST" # KeyConfig.USB_HOST='USB_HOST', this.funtion1
    control: checkbox
  - name: "Zlink" # KeyConfig.ZLINK_AUTO_START='zlink_auto_start' / cbox_function_google_off
    control: checkbox
    description: "When enabled, Zlink should start automatically on boot. Additionally, it will take over Wi-Fi to create and maintain its wireless hotspot, therefore you won't be able to use Wi-Fi for other purposes."
  - name: "HiCar" # zlink_hicar
    control: checkbox
    description: "When enabled, Zlink should start automatically on boot and enter Huwawei HiCar mode."
  - name: "Google Apps"
    control: checkbox
  - name: "AUX"
    control: checkbox
  - name: "DTV"
    control: checkbox
  - name: "F_CAM" # F_CAM_Type / Front_view_camera
    control: checkbox
  - name: "Txzing Assistant"
    control: checkbox
  - name: "BT"
    control: checkbox
  - name: "Touch data continuously sent"
    control: checkbox
  - name: "Equalizer APP"
    control: checkbox
  - name: "Global Weather App"
    control: checkbox
  - name: "360APK"
    control: checkbox
  - name: "Remember The Last Mode"
    children:
      - name: "Enable"
        control: radio
      - name: "To OEM System"
        control: radio
      - name: "To Android Homepage"
        control: radio
  - name: "DVR"
    children:
      - name: "Close"
        control: radio
      - name: "CVBS DVR"
        control: radio
      - name: "USB DVR"
        control: radio
  - name: "Bluetooth Selection"
    children:
      - name: "OEM Bluetooth"
        control: radio
      - name: "Android Bluetooth"
        control: radio
  - name: "Amplifier Selection"
    children:
      - name: "OEM Amplifier"
        control: radio
      - name: "Aftermarket Amplifier"
        control: radio
  - name: "360 Camera"
    children:
      - name: "CVBS Camera"
        control: radio
      - name: "VGA Camera"
        control: radio
  - name: "Automatic Brightness"
    children:
      - name: "Width Lamp Control"
        control: radio
      - name: "Close"
        control: radio
  - name: "Unit Selection"
    children:
      - name: "Metric Unit"
        control: radio
      - name: "Imperial Unit"
        control: radio
  - name: "AHD Camera Selection"
    children:
      - name: "Automatic Detection"
        control: radio
      - name: "AHD-1080P-30HZ"
        control: radio
      - name: "AHD-1080P-25HZ"
        control: radio
      - name: "AHD-720P-30HZ"
        control: radio
      - name: "AHD-720P-25HZ"
        control: radio
      - name: "AHD-720P-50HZ"
        control: radio
      - name: "CVBS-NTSC"
        control: radio
      - name: "CVBS-PAL"
        control: radio
  - name: "Disable Video In Motion"
    control: checkbox
  - name: "Front view mirror setting"
    control: checkbox
---
