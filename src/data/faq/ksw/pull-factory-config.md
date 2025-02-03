---
question: 'How to pull factory_config.xml file from Head Unit?'
---
The `factory_config.xml` file is a device/vendor specific configuration file that gets shipped with your Head Unit. Before you make any changes, please make a backup of the original file, so that you can always revert to it.

1. Download ADB from [Android SDK Platform Tools](https://developer.android.com/tools/releases/platform-tools)
2. Create a Wi-Fi hotspot on your phone
3. Connect Head Unit and your laptop to that Wi-Fi hotspot
4. Connect to the Head Unit by using a terminal emulator of your choice and ADB:
    ```sh
    adb connect IP:PORT
    ```
5. Pull the file into your device:
    ```sh
    adb pull /mnt/vendor/persist/OEM/factory_config.xml
    ```
6. Disconnect:
    ```sh
    adb disconnect
    ```

Note: You might need to [configure your environment variables](https://developer.android.com/tools#environment-variables) to access `adb` command from all locations, alternatively you can `cd` into the `platform-tools` folder and run it from there, perhaps with `./adb` path instead. This is not specific to these head units and therefore out of scope for this guide. Please look up other instructions online to learn more about installation and usage of ADB, and command line utilities in general.
