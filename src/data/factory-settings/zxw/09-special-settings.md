---
section: "Special Settings"
settings:
  - name: "Original vehicle LVDS chip type"
    configKey: originalLvdsChipType
    description: "Shown on the Mercedes-Benz and Audi pages. Some Audi layouts label the same two choices MIB_LOW and MIB_HIGHT."
    children:
      - name: "NTG5.0"
        configValue: 0
        control: radio
      - name: "NTG5.5"
        configValue: 1
        control: radio
  - name: "Mercedes Benz Vito bottom status bar style"
    configKey: benzVitoBottomStyle
    unverified: true
    description: "Only shown with the `KSW_BENZ_VITO` theme."
    children:
      - name: "Default"
        configValue: 0
        control: radio
      - name: "Temperature control"
        configValue: 1
        control: radio
---
