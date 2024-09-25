---
section: "Vehicle Button"
settings:
  - name: "MAP Key Selection"
    configKey: mapSelection
    description: "Choose what happens when \"Map\" key is pressed on either iDrive controller or steering wheel"
    children:
      - name: "Android Navi"
        configValue: 0
        control: radio
        description: "Opens selected Android navigation app"
      - name: "Car Navi"
        configValue: 1
        control: radio
        description: "Opens OEM car navigation"
  - name: "MODE Key Selection"
    configKey: modeSelection
    children:
      - name: "Enable"
        configValue: 0
        control: radio
      - name: "Disable"
        configValue: 1
        control: radio
  - name: "Voice Key Selection"
    configKey: voiceSelection
    children:
      - name: "Not used"
        configValue: 0
        control: radio
      - name: "Short press does nothing, long press to navigate"
        configValue: 1
        control: radio
      - name: "Short press for voice, long press for navigation"
        configValue: 2
        control: radio
      - name: "Short press to navigate, long press has no effect"
        configValue: 3
        control: radio
      - name: "HiCar voice function button"
        configValue: 4
        control: radio
  - name: "Phone Key Selection"
    configKey: phoneSelection
    children:
      - name: "Original vehicle function"
        configValue: 0
        control: radio
      - name: "Android Bluetooth function"
        configValue: 1
        control: radio
      - name: "Undefined"
        configValue: 2
        control: radio
---
