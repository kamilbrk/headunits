---
question: 'How to pull zxw_factory_config.xml file from Head Unit?'
---
The `zxw_factory_config.xml` file is a device/vendor specific configuration file that gets shipped with your Head Unit. Before you make any changes, please make a backup of the original file, so that you can always revert to it.

1. Download ADB from [Android SDK Platform Tools](https://developer.android.com/tools/releases/platform-tools)
2. Create a Wi-Fi hotspot on your phone
3. Connect Head Unit and your laptop to that Wi-Fi hotspot
4. Connect to the Head Unit with ADB
    ```sh
    adb connect IP:PORT
    ```
5. Pull the file into your laptop
    ```sh
    adb pull /mnt/privdata1/zxw_factory_config.xml
    ```
    If this command fails with a "Permission Denied" error, you will need to change the permissions on the file in order to pull/copy it:
    ```sh
    adb shell
    su
    chmod +r /mnt/privdata1/zxw_factory_config.xml
    exit
    exit
    ```
   Then re-run the `adb pull` command above
6. Disconnect
    ```sh
    adb disconnect
    ```
