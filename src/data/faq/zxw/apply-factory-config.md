---
question: 'How to apply zxw_factory_config.xml file?'
---
Before making any changes, make sure you have a [backup of your original file](/headunits/faq/zxw/pull-factory-config). Once you apply a new file, it will persist even through a factory reset.

1. Use a USB drive with FAT32 formatted partition.
2. On the root of the USB drive, create a folder called `OEM`.
3. Copy your file into `OEM` folder, so that it's accessible under `/OEM/zxw_factory_config.xml` location.
4. Plug in the USB drive into Head Unit. If you have two USB connectors, use the one without CarPlay label.
5. Start (or restart) the Head Unit, your file should be automatically detected. Wait for a toast message indicating that settings were applied. 
6. Alternatively, go to Factory settings, "Profile Import" and tap on "Update" button to load the file manually.