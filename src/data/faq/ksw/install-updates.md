---
question: 'How to install OTA firmware updates?'
---
Installing an OTA that was not built for your platform, or installing one out of order, can
leave the unit stuck at boot with no user-accessible recovery. Check
[which platform you have](/platforms/ksw) and the [upgrade path](/faq/ksw/upgrade-path)
before copying anything to the USB drive, and read [before you change anything](/safety).

1. Download suitable firmware OTA update. Check Discord or forums for links.
2. Compare file signatures with values from [Updates](/updates/ksw) page (if available) to make sure file is not corrupted.
3. Copy the `Ksw-[...]_OS_v[...]-ota.zip` archive directly to the root of the USB drive.
4. Plug in the USB drive into Head Unit. If you have two USB connectors, use the one without CarPlay label.
5. Head Unit should automatically detect the file and ask if you want to update, select Yes.