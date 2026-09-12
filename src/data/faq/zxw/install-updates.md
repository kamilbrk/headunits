---
question: 'How to install OTA firmware updates?'
---
:::warning
Installing an OTA that was not built for your platform can leave the unit stuck at boot with
no user-accessible recovery. Check [which platform you have](/platforms/zxw) before copying
anything to the USB drive, and read [before you change anything](/safety).
:::

1. Download suitable firmware OTA update. Check Discord or forums for links.
2. Compare file signatures with values from [Updates](/updates/zxw) page (if available) to make sure file is not corrupted.
3. Copy the `update[...].zip` archive directly to the root of the USB drive.
4. Plug in the USB drive into Head Unit. If you have two USB connectors, use the one without CarPlay label.
5. Head Unit should automatically detect the file and ask if you want to update, select Yes.

Note: GT6 devices will detect `update13.zip` file name, whereas GT7 devices require `update13_2.zip`. You can also use `_force` suffix (e.g. `update13_2_force.zip`) to skip the confirmation prompt.