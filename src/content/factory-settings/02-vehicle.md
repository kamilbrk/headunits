---
section: "Vehicle"
settings:
  - name: "Car Without OEM Monitor"
    control: checkbox
    description: "Selecting the \"CAR\" menu option will display a clock instead of OEM system"
  - name: "AUX Switching Modes"
    children:
    - name: "Automatic"
      control: radio
    - name: "Manual"
      control: radio
  - name: "AUX auto switching"
    children:
    - name: "Alpine"
      control: radio
    - name: "Harman"
      control: radio
    - name: "Other"
      control: radio
  - name: "Knob Type"
    children:
    - name: "Knob_A"
      control: radio
    - name: "Knob_B"
      control: radio
  - name: "Driver's seat"
    children:
    - name: "Left driver's seat"
      control: radio
    - name: "Right driver's seat"
      control: radio
  - name: "Number of doors"
    children:
    - name: "4 doors"
      control: radio
    - name: "2 doors"
      control: radio
    - name: "Hide doors"
      control: radio
  - name: "Speedometer Selection"
    children:
    - name: "260km/h"
      control: radio
    - name: "280km/h"
      control: radio
  - name: "Gear Selection"
    children:
    - name: "Gear type 1"
      control: radio
    - name: "Gear type 2"
      control: radio
    - name: "Gear type 3"
      control: radio
  - name: "MAP Key Selection"
    description: "Choose what happens when \"Map\" key is pressed on either iDrive controller or steering wheel"
    children:
    - name: "Android Navi"
      control: radio
      description: "Open selected navigation app in Android"
    - name: "Car Navi"
      control: radio
      description: "Open OEM car navigation"
  - name: "MODE Key Selection"
    children:
    - name: "Enable"
      control: radio
    - name: "Disable"
      control: radio
  - name: "FL Speaker Enable"
    children:
    - name: "Enable"
      control: radio
    - name: "Disable"
      control: radio
  - name: "Speed Type Selection"
    children:
    - name: "Speed Type 1"
      control: radio
    - name: "Speed Type 2"
      control: radio
  - name: "Voice Key Selection"
    children:
    - name: "Not used"
      control: radio
    - name: "Short press does nothing, Long press opens NAVI"
      control: radio
    - name: "Short press opens Voice Command, Long press opens NAVI"
      control: radio
    - name: "Short press opens NAVI, Long press does nothing"
      control: radio
    - name: "HiCar voice function key"
      control: radio
  - name: "Phone Key Selection"
    children:
    - name: "Original vehicle function"
      control: radio
    - name: "Android Bluetooth feature"
      control: radio
    - name: "Undefined"
      control: radio
  - name: "Collect CAN Bus Data"
    control: checkbox
    children:
      - name: "Can1"
        control: radio
      - name: "Can2"
        control: radio
  - name: "Steering wheel track selection"
    children:
    - name: "track1"
      control: radio
    - name: "track2"
      control: radio
  - name: "360 boot up camera"
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
