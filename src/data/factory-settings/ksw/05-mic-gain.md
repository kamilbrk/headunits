---
section: "MIC Gain"
settings:
  - name: "MIC Gain (Android 10)"
    configKey: mic_gain_m501
    control: range
    min: 0
    max: 8
    description: "Adjust the signal strength from microphone. The screen shows one slider; on Android 10 it writes this key."
  - name: "MIC Gain (Android 11 and later)"
    configKey: mic_gain_m600
    control: range
    min: 0
    max: 20
    description: "Adjust the signal strength from microphone. The screen shows one slider; on every Android version except 10 it writes this key. Older firmware used a single `Mic_gain` key. When the file is imported, this value is only applied on M600 builds."
---
