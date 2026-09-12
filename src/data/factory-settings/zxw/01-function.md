---
section: "Function"
settings:  
  - name: "USB HOST"
    configKey: usbHostMode
    control: checkbox
    onValue: 1
    offValue: 0
  - name: "Hicar"
    configKey: hicarVisible
    control: checkbox
    onValue: 1
    offValue: 0
  - name: "Google Apps"
    configKey: googleVisible
    control: checkbox
    onValue: 1
    offValue: 0
  # - name: "Google Voice"
  #   configKey: googleVoiceSwitch
  #   control: checkbox
  #   description: "This seems to be saved in internal settings rather than XML file"
  - name: "AUX"
    configKey: auxVisible
    control: checkbox
    onValue: 1
    offValue: 0
  - name: "DTV"
    configKey: dtvVisible
    control: checkbox
    onValue: 1
    offValue: 0
  - name: "F_CAM"
    configKey: frontCamera
    control: checkbox
    onValue: 1
    offValue: 0
  - name: "screen cast-MS9120"
    configKey: screenCastVisible
    control: checkbox
    onValue: 1
    offValue: 0
  - name: "The original car host supports touch"
    nameOld: "Touch data continuously sent"
    configKey: touchData
    control: checkbox
    onValue: 1
    offValue: 0
  - name: "Sound APK"
    configKey: eqVisible
    control: checkbox
    onValue: 1
    offValue: 0
  - name: "Weather APK"
    configKey: weatherVisible
    control: checkbox
    onValue: 1
    offValue: 0
  - name: "Bluetooth transmitter switch"
    configKey: doubleBtTransmit
    control: checkbox
    onValue: 1
    offValue: 0
  - name: "USB BT transmit"
    configKey: btTransmitVisible
    control: checkbox
    onValue: 1
    offValue: 0
  - name: "Automatically enter navigation upon startup"
    configKey: bootStartNavi
    control: checkbox
    onValue: 1
    offValue: 0
  - name: "Night brightness bar"
    configKey: backlightBrightnessNightShow
    control: checkbox
    onValue: 1
    offValue: 0
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
