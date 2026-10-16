# Testing

`bash test.sh` checks shell syntax and source privacy, runs 24 Python installer tests with 100% statement and branch coverage, then runs JUnit movement/settings tests, Java formatting and JaCoCo coverage enforcement.

The host Java boundary is explicitly `ReelOptions.java`: settings validation, fallback/random resolution, layouts, ordered presets, monotonic staged reel movement and cycle continuity. Both Java line and branch coverage must be 100%. The build excludes no methods within that boundary. Android framework activities/provider/dream lifecycle and GPU rendering cannot execute as plain JVM code; their evidence is recorded as native checks, not counted as host coverage.

The installer suite covers ambiguous/disconnected devices, confirmation and destructive removal, malformed checksums, bounded downloads, restricted redirects, update/install errors and temporary download cleanup. Coverage reports live under `build/coverage/` and `build/coverage-gradle/reports/`.

Native checks must cover settings persistence and invalid provider values, D-pad focus/Select/Back, real DreamService startup, moving frames, pause/resume, surface recreation, clean remote exit, aspect ratio, scene framing and privacy from the packaged manifest. Emulator checks do not establish Fire OS idle activation, reboot/sleep persistence, hardware frame pacing, thermals or 4K composition.
