---
section: "Function"
settings:  
  - name: "USB HOST"
    configKey: usbHostMode
    control: checkbox
  - name: "Hicar"
    configKey: hicarVisible
    control: checkbox
  - name: "Google Apps"
    configKey: googleVisible
    control: checkbox
  - name: "AUX"
    configKey: auxVisible
    control: checkbox
  - name: "DTV"
    configKey: dtvVisible
    control: checkbox
  - name: "F_CAM"
    configKey: frontCamera
    control: checkbox
  - name: "screen cast-MS9120"
    configKey: screenCastVisible
    control: checkbox
  - name: "Touch data continuously sent"
    configKey: touchData
    control: checkbox
  - name: "Sound APK"
    configKey: eqVisible
    control: checkbox
  - name: "Weather APK"
    configKey: weatherVisible
    control: checkbox
  - name: "Amplifier Selection"
    configKey: amplifierSelection
    children:
      - name: "OEM Amplifier"
        configValue: 0
        control: radio
      - name: "Aftermarket Amplifier"
        configValue: 1
        control: radio
  - name: "Whether to use the left front horn"
    configKey: useHorn
    children:
      - name: "Enable"
        configValue: 0
        control: radio
      - name: "Disable"
        configValue: 1
        control: radio
---
