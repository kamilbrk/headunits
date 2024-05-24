---
section: "Vehicle"
settings:
  - name: "Car Without OEM Monitor"
    configKey: notHaveScreen
    control: checkbox
    description: "Selecting the \"CAR\" menu option will display a clock instead of OEM system. Choose this option on cars without OEM screen, e.g. old BMW X1."
  - name: "Knob Type"
    configKey: iDriverType
    children:
      - name: "Knob_A"
        configValue: 0
        control: radio
      - name: "Knob_B"
        configValue: 1
        control: radio
  - name: "360 Camera"
    configKey: cameraType
    children:
      - name: "CVBS Camera"
        configValue: 0
        control: radio
      - name: "VGA Camera"
        configValue: 1
        control: radio
  - name: "Gear Selection"
    configKey: gearType
    children:
    - name: "Gear Type 1"
      configValue: 0
      control: radio
    - name: "Gear Type 2"
      configValue: 1
      control: radio
    - name: "Gear Type 3"
      configValue: 2
      control: radio
  - name: "Steering Wheel Track Selection"
    configKey: wheelTrack
    children:
    - name: "Track 1"
      configValue: 0
      control: radio
    - name: "Track 2"
      configValue: 1
      control: radio
  - name: "Reverse exit time"
    configKey: backcarTimeSelection
    children:
      - name: "Opt out under original vehicle agreement"
        configValue: 0
        control: radio
      - name: "Custom exit time"
        configValue: 1
        control: radio
        # configKey: backcarTime
        min: 0
        max: 10
  - name: "Driver seat"
    configKey: driverSeat
    children:
      - name: "Driver seat on the left"
        configValue: 0
        control: radio
      - name: "Driver seat on the right"
        configValue: 1
        control: radio
  - name: "Number of doors"
    configKey: doorAmount
    children:
      - name: "4 doors"
        configValue: 0
        control: radio
      - name: "2 doors"
        configValue: 1
        control: radio
      - name: "Hide doors"
        configValue: 2
        control: radio
  - name: "Speed type selection"
    configKey: speedType
    children:
      - name: "Speed type 1"
        configValue: 0
        control: radio
      - name: "Speed type 2"
        configValue: 1
        control: radio
  - name: "360 boot camera"
    configKey: bootCamera
    children:
      - name: "Do not use a camera"
        configValue: 0
        control: radio
      - name: "Install camera"
        configValue: 1
        control: radio
      - name: "Original camera"
        configValue: 2
        control: radio
  - name: "Cornering lamp control"
    configKey: corneringLampControl
    children:
      - name: "Uncontrolled"
        configValue: 0
        control: radio
      - name: "Controlled"
        configValue: 1
        control: radio
  - name: "Switching between external and internal microphones"
    configKey: micType
    children:
      - name: "External microphone"
        configValue: 0
        control: radio
      - name: "Built-in microphone"
        configValue: 1
        control: radio
  - name: "Splitting machine LVDS mode"
    children:
      - name: "VESA"
        control: radio
      - name: "JEIDA"
        control: radio
---
