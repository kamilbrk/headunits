---
section: "MIC Gain"
settings:
  - name: "MIC Gain (Android 10)"
    configKey: mic_gain_m501
    control: range
    min: 0
    max: 8
    description: "Adjust the signal strength from microphone. The screen shows one slider; on Android 10 it writes this key once the firmware has split it; earlier Android 10 builds use the single `Mic_gain`."
  - name: "MIC Gain (Android 12 and later)"
    configKey: mic_gain_m600
    control: range
    min: 0
    max: 20
    description: "Adjust the signal strength from microphone. The screen shows one slider; on Android 12 and later it writes this key. Android 11 firmware never splits the key and keeps the single `Mic_gain`. Android 10 and 12 builds from before the split also wrote `Mic_gain`. When the file is imported, this value is only applied on M600 builds."
---
