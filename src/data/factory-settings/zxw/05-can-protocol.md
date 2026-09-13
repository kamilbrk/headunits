---
section: "CAN Protocol"
settings:
  - name: "Current Selection"
    configKey: canProtocolSelection
    control: select
    optionsFrom:
      path: CANBusProtocol/Protocol
      attribute: id
    valueType: int
    description: "Choose CAN connection protocol, according to your vendor's recommendations"
---