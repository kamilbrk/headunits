---
section: "Vehicle"
settings:
  - name: "Car without Original Display"
    nameOld: "Car Without OEM Monitor"
    configKey: CarDisplay
    control: checkbox
    description: "Selecting the \"CAR\" menu option will display a clock instead of OEM system. Choose this option on cars without OEM screen, e.g. old BMW X1."
  - name: "AUX Switching Modes"
    configKey: CarAux_Operate
    children:
    - name: "Automatic Switching"
      nameOld: "Automatic"
      configValue: 0
      control: radio
    - name: "Manual Switching"
      nameOld: "Manual"
      configValue: 1
      control: radio
  - name: "AUX Auto Switching Scheme"
    nameOld: "AUX auto switching"
    configKey: CarAux_auto_method
    children:
    - name: "Alpine"
      configValue: 1
      control: radio
    - name: "Harman"
      configValue: 2
      control: radio
    - name: "Other"
      configValue: 3
      control: radio
  - name: "Knob Type"
    configKey: CCC_IDrive
    children:
    - name: "Knob_A"
      configValue: 0
      control: radio
    - name: "Knob_B"
      configValue: 1
      control: radio
  - name: "Driver's seat"
    children:
    - name: "Driver's Seat on Left"
      nameOld: "Left driver's seat"
      control: radio
    - name: "Driver's Seat on Right"
      nameOld: "Right driver's seat"
      control: radio
  - name: "Number of doors"
    configKey: CarDoorSelect
    children:
    - name: "4 Doors"
      configValue: 0
      control: radio
    - name: "2 Doors"
      configValue: 1
      control: radio
    - name: "Do Not Display Doors"
      nameOld: "Hide doors"
      configValue: 2
      control: radio
  - name: "Speedometer Selection"
    configKey: Dashboard_MaxSpeed # UnitImperial+Value1=160mph, UnitImperial+Value3=180mph, UnitMetric+Value1=280kmph, UnitMetric+Value3=280kmph, UnitMetric+Value2+Vendor3Audi=300kmph, ELSE=Value1=260kmph
    children:
    - name: "260km/h"
      control: radio
    - name: "280km/h"
      control: radio
  - name: "Gear Selection"
    children:
    - name: "Gear Type 1"
      control: radio
    - name: "Gear Type 2"
      control: radio
    - name: "Gear Type 3"
      control: radio
  - name: "MAP Key Selection"
    configKey: Map_key
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
    configKey: Mode_key
    children:
    - name: "Active"
      nameOld: "Enable"
      configValue: 0
      control: radio
    - name: "Inactive"
      nameOld: "Disable"
      configValue: 1
      control: radio
  - name: "Use Left Front Speaker or Not?"
    nameOld: "FL Speaker Enable"
    configKey: Front_left
    children:
    - name: "Enable"
      configValue: 0
      control: radio
    - name: "Disable"
      configValue: 1
      control: radio
  - name: "Speed Type Selection"
    configKey: Speed_type
    children:
    - name: "Speed Type 1"
      configValue: 0
      control: radio
    - name: "Speed Type 2"
      configValue: 1
      control: radio
  - name: "Voice Key Selection"
    configKey: Voice_key
    children:
    - name: "No function"
      nameOld: "Not used"
      configValue: 0
      control: radio
    - name: "Short Press: No Function, Long Press: Navigation"
      nameOld: "Short press does nothing, Long press opens NAVI"
      configValue: 1
      control: radio
    - name: "Short Press: Voice Command, Long Press: Navigation"
      nameOld: "Short press opens Voice Command, Long press opens NAVI"
      configValue: 2
      control: radio
    - name: "Short Press: Navigation, Long Press: No Function"
      nameOld: "Short press opens NAVI, Long press does nothing"
      configValue: 3
      control: radio
    - name: "HiCar Voice Command Key"
      nameOld: "HiCar voice function key"
      configValue: 4
      control: radio
  - name: "Phone Key Selection"
    configKey: phone_key
    children:
    - name: "Original Car Function"
      nameOld: "Original vehicle function"
      configValue: 0
      control: radio
    - name: "Android Bluetooth Function"
      nameOld: "Android Bluetooth feature"
      configValue: 1
      control: radio
    - name: "Undefined"
      configValue: 2
      control: radio
  - name: "CAN Bus Data Acquisition"
    nameOld: "Collect CAN Bus Data"
    control: checkbox
    children:
      - name: "Can1"
        control: radio
      - name: "Can2"
        control: radio
  - name: "Steering wheel track selection" # drive_track_selected in strings, rdg_track for radios
    configKey: DirtTravelSelection # KeyConfig.DRIVE_TRACK
    children:
    - name: "track1" # 0
      control: radio
    - name: "track2" # 1
      control: radio
  - name: "360 boot up camera"
    configKey: BootUpCamera
    children:
    - name: "No camera use"
      control: radio
    - name: "Retrofit camera"
      control: radio
    - name: "Original car camera"
      control: radio
  - name: "Turn signal control"
    children:
    - name: "Uncontrolled"
      control: radio
    - name: "Controlled"
      control: radio
  - name: "MIC external built-in toggle switch"
    configKey: MicControl
    children:
    - name: "External"
      control: radio
    - name: "Built-in"
      control: radio
  - name: "Original radar display reverse"
    children:
    - name: "Normal"
      control: radio
    - name: "Reverse"
      control: radio
---
