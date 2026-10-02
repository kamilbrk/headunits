---
id: "Ksw-T-M700_OS_v1.3.5-ota"
vendor: ksw
platform: m700
android: 13
date: 2024-07-12T01:46:48Z
signatures:
  md5: 4ccb76ff810b63fbb04807a57fad9c63
  sha1: 8b6e7df967182578436b3c6a87821308011ece2e
  sha256: 985fe950e0859644e625475ab4dda595b6f63cfba42c9fa1ab90f8fa3e89146a
---
:::warning
Any app with `ms2160` in its package name can now record the screen without asking, and Android's install-time package verification is switched off. Apps that block screenshots and screen recording the common way (`addFlags(FLAG_SECURE)`) no longer can, which M700 already did before this release.
:::

#### Changes
- Same as in [M600 1.6.5](/updates/ksw/m600/ksw-t-m600_os_v165-ota), since both platforms are built from the same source and most diffs look exactly the same. Except that the `FLAG_SECURE` override, APKInstaller update, 360 camera fixes and `UI_NTG6_FY_V3` editor were already in [M700 1.3.1](/updates/ksw/m700/ksw-t-m700_os_v131-ota), and the M606 CPU detection only applies to M600.
