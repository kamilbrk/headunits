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
  # - name: "Google Voice"
  #   configKey: googleVoiceSwitch
  #   control: checkbox
  #   description: "This seems to be saved in internal settings rather than XML file"
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
  - name: "The original car host supports touch"
    nameOld: "Touch data continuously sent"
    configKey: touchData
    control: checkbox
  - name: "Sound APK"
    configKey: eqVisible
    control: checkbox
  - name: "Weather APK"
    configKey: weatherVisible
    control: checkbox
  - name: "Bluetooth transmitter switch"
    configKey: doubleBtTransmit
    control: checkbox
  - name: "USB BT transmit"
    configKey: btTransmitVisible
    control: checkbox
  - name: "Automatically enter navigation upon startup"
    configKey: bootStartNavi
    control: checkbox
  - name: "Night brightness bar"
    configKey: backlightBrightnessNightShow
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
  - name: "Secondary screen application"
    configKey: sLauncherAppOverseas
    children:
      - name: "Domestic"
        configValue: 0
        control: radio
      - name: "Oveseas"
        configValue: 1
        control: radio
---
