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
---
