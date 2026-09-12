---
section: "Reverse exit time"
settings:
  - name: "Exit according to the original vehicle agreement"
    control: radio
    configKey: Reverse_time
    editable: false
    warning: "One `Reverse_time` element holds both halves of this setting, written as `enabled-seconds` — `0-0` is off, `1-10` is ten seconds. The file's own comment says do NOT set it to `0`, as that locks you out of factory settings. The bounds for every other combination are unknown, so this one stays a hand edit."
  - name: "Custom exit time"
    control: radio
    min: 0
    max: 10
    editable: false
---

