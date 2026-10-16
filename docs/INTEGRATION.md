# Host integration contract

| Field | Value |
| --- | --- |
| Toolkit ID | `slot-vision` |
| Repository | `jeremykenedy/slot-vision` |
| Package | `com.jeremykenedy.reelatrium` |
| Dream | `com.jeremykenedy.reelatrium/.ReelAtriumDreamService` |
| Settings | `com.jeremykenedy.reelatrium/.SettingsActivity` |
| Preview | `com.jeremykenedy.reelatrium/.PreviewActivity` |
| Minimum API | 23 |
| Intended release | `v1.0.0` |
| APK | `slot-vision.apk` |
| Checksum | `slot-vision.apk.sha256` |
| APK SHA-256 | `0ee21b586f3b306e6da57cacc149bebece35a01e6ef2c7af1512c0ddc51354e4` |
| APK bytes | `62076478` |
| Settings schema | `content://com.jeremykenedy.reelatrium.settings/schema` |
| Current settings | `content://com.jeremykenedy.reelatrium.settings/settings` |
| Preview source | `art/screenshots/casino-classic-androidtv.png` |
| Embedded preview | `res/drawable-nodpi/screensaver_preview.png` |

Release availability must be verified after publication. Preserve the existing package and signing key when updating Reel Atrium installations; the displayed name is Slot Vision. All seven stored setting keys remain stable. No app data migration is required.

Toolkit installs the signed release and selects the exact dream component. Fire TV UI discovers installed protected DreamServices and opens the app-owned settings activity. Its download catalog needs the exact published tag, URL, checksum and byte count above. Use the existing normalized-component thumbnail filename helper for the bundled host image. Capture provenance is in `art/screenshots/capture-provenance.json`.

The seven validated options are game, season, speed, brightness, camera, background and view. The provider schema is authoritative for accepted values and defaults. Fullscreen removes the cabinet and environment while retaining slow drift, spins and payout-scaled coin effects. See [configuration](CONFIGURATION.md) and [verification](VERIFICATION.md).
