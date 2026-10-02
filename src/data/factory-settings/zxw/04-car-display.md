---
section: "Car Display"
settings:
  - name: "Current Selection"
    configKey: carTypeSelection
    control: select
    optionsFrom:
      path: CarDisplayParam/model
      attribute: id
    valueType: int
    description: "Choose car display type, according to your vendor's recommendations"
  - name: "DCLK H"
    nameOld: "LCD CLK polarity"
    configKey: lcdClkPolarity
    control: checkbox
    onValue: 1
    offValue: 0
    description: "The label beside the box shows the current polarity: DCLK L when unticked, DCLK H when ticked."
---
