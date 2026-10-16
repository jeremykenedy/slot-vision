# Building

Install JDK 21, Android SDK platform 36 and build-tools 36.0.0. Set `ANDROID_HOME` when the SDK is outside `~/Library/Android/sdk`.

```sh
bash build.sh
bash test.sh
```

The standalone build uses aapt2, javac and the checksum pinned R8 tool. Filament 1.77.3, its glTF and Android utilities, Kotlin and coroutines runtime dependencies are fetched from official Maven repositories and verified against pinned SHA256 digests. The APK bundles all required native libraries, models, textures and dependency licenses. Release APKs appear at `build/slot-vision.apk` with a sibling SHA-256 file. A unique RSA signing key and its password live in `~/.android/reel-atrium.jks` and `~/.android/reel-atrium.pass`; preserve both outside source control. `SLOT_VISION_KEYSTORE` and `SLOT_VISION_KEYPASS` override those paths.

CI sets `UNSIGNED=1` and produces an unsigned review APK. Do not publish or install that artifact over a signed release. `VERSION_NAME` and `VERSION_CODE` configure release metadata; the first release uses `1.0.0` and `1`.
