---
section: "UI Configuration"
settings:
  - name: "UI Selection"
    configKey: UI_type
    control: select
    optionsFrom:
      path: SupportUIList/Item
      attribute: name
      labelAttribute: display
    valueType: string
    description: "Choose user interface theme from all possible options as found on Themes. This list can be adjusted in factory_config.xml file and its `<SupportUIList>` section"
---

