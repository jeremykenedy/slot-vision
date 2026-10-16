# Installation

Enable ADB debugging using the TV's own developer settings, connect ADB and use an explicit device serial. The installer lists only authorized devices and requires a choice when several are connected.

```sh
python3 install.py --serial TV_IP:5555
python3 install.py --serial TV_IP:5555 --apk build/reel-atrium.apk
```

Without `--apk`, the installer downloads the latest release from this repository, validates HTTPS release URLs and allowed asset redirects, and verifies SHA-256 before using `adb install -r`. Updates preserve preferences. `--yes` confirms installation for scripts. An unavailable device, failed checksum or ADB error exits with a failure.

Select the saver in platform settings or with Fire TV Toolkit. The installer does not alter selection, timers, sleep settings, firmware updates or other applications. No platform rollback protection is claimed.

Before uninstalling, select another screensaver. Run `python3 install.py --serial TV_IP:5555 --uninstall`. Scripted removal requires `--uninstall --yes --force`. Removal deletes the app's preferences. Install a prior same-signer version only where the platform permits downgrades; it may require uninstalling first, which loses preferences.
