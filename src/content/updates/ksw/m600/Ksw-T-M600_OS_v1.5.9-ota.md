---
id: "Ksw-T-M600_OS_v1.5.9-ota"
vendor: ksw
platform: m600
date: 2024-04-08T07:09:31Z
signatures:
  md5: e8038251c34ed45d9ba0f3a4d7f81459
  sha1: cccd86121d58beeee12b26efefcc0a4fd2be0e5c
  sha256: 0eac76a8e3d9f970a41ea673935422eccc6112aafb465f9663def2769ecaf347
---
Summary:
- New theme [`UI_NTG6_FY_V3`](/headunits/themes/ksw/ui_ntg6_fy_v3)

Changes since `Ksw-T-M600_OS_v1.5.8-ota` built 21 days earlier:
- New theme [`UI_NTG6_FY_V3`](/headunits/themes/ksw/ui_ntg6_fy_v3) with 8 colour schemes, possibly with similar popup/overlay functionality to [`UI_GS_ID8`](/headunits/themes/ksw/ui_gs_id8) and [`UI_PEMP_ID8`](/headunits/themes/ksw/ui_pemp_id8) themes since it appears to have its own custom music state observer like the other two. To activate it, add `<Item id="1" name="UI_NTG6_FY_V3" display="Benz NTG6 FY V3" />` to your `factory_config.xml` file.
- Extended Zlink broadcast receiver to handle wired and wireless Huawei HiCar