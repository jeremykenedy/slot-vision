# Releasing

Finish native visual review and host checks before publication. Set semantic version name/code, update changelog and release notes, refresh real native captures, and run the complete CI suite. Review manifest permissions, package, DreamService metadata, signing certificate and APK contents.

Publish from the verified remote primary branch tip only. Fetch `origin main`, confirm `HEAD` equals `origin/main`, tag that exact commit and verify the remote tag. Build a signed APK with the preserved unique signing key and generate SHA-256 from its final bytes. Attach `reel-atrium.apk` and `reel-atrium.apk.sha256`; never publish CI's unsigned artifact. Download both release assets and verify the checksum again.

Set GitHub About, website and relevant topics to describe tested capabilities accurately. Review the README gallery and light/dark/reduced-motion banners in a browser. Record the device matrix and limitations in release notes. Toolkit/UI integration consumes the exact package, dream component, release assets and real preview listed in CONFIGURATION.md.
