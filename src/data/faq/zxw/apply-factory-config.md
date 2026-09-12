---
question: 'How to apply zxw_factory_config.xml file?'
---
A factory config survives a factory reset. If the file you apply is wrong for your unit, the only way back is applying your own backup the same way — so [pull your original file](/faq/zxw/pull-factory-config) first and keep it somewhere you can reach from the car. See [before you change anything](/safety).

1. Use a USB drive with FAT32 formatted partition.
2. On the root of the USB drive, create a folder called `OEM`.
3. Copy your file into `OEM` folder, so that it's accessible under `/OEM/zxw_factory_config.xml` location.
4. Plug in the USB drive into Head Unit. If you have two USB connectors, use the one without CarPlay label.
5. Start (or restart) the Head Unit, your file should be automatically detected. Wait for a toast message indicating that settings were applied. 
6. Alternatively, go to Factory settings, "Profile Import" and tap on "Update" button to load the file manually.