---
section: "UI Configuration"
settings:
  - name: "Current Selection"
    configKey: uiSelection
    control: select
    optionsFrom:
      path: SupportUIList/Item
      attribute: id
      labelAttribute: ui
    valueType: int
    description: "Choose user interface theme from all possible options as found on Themes. This list can be adjusted in zxw_factory_config.xml file and its `<SupportUIList>` section"
---