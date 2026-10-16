# Verification

Validation date: October 16, 2026. Slot Vision uses Filament 1.77.3, original modeled cabinets and three-dimensional spinning reels. The published release remains pending the final source and artifact checks below.

| Device | API | Evidence | Status |
| --- | --- | --- | --- |
| Google TV emulator, host GPU | 34 | Native cabinet and fullscreen layouts, seasonal artwork, camera movement, actual test dream, Settings/Preview/Back and provider persistence | Checked; current material and beacon gallery captured |
| Fire TV AFTDEC012E, physical | 30 | Cabinet garden with jackpot coins and fullscreen classic, native preview playback, SurfaceFlinger present timestamps, Back and settings restoration | About 30 presented buffers per second in both measured scenes |
| Other Fire TV, Android TV and Google TV hardware | Untested | None | A volunteer with the device is needed |

The rendering surface is 1280x720, composed into the 1920x1080 display capture. These screenshots do not establish native 1080 or 4K rendering. No final-candidate reboot persistence, unattended idle activation, long thermal soak or physical 4K result has been established. Report model, OS/API, output resolution, remote behavior and sustained pacing when testing another device.

## Automated checks

The scoped `ReelOptions` and `ReelRound` Java tests enforce 100% line and branch coverage. Installer tests enforce 100% statement and branch coverage. Spotless and source privacy checks pass. Android lifecycle and GPU code require native verification and are outside JVM coverage.

The APK requests no Android permissions. Models, seasonal artwork and lighting are bundled. Filament and Kotlin dependencies are pinned and checksum verified; required licenses are bundled. The app has no runtime content downloads, analytics or reporting client.

## Rendering and animation

Classic has three reels, palace has five reels and three visible rows, and garden has five reels and five visible rows. Atrium and all four seasonal atlases are supported. Classic artwork intentionally includes requested BAR and 7 symbols. Other incidental words and watermarks are absent from the scene.

Cabinet view uses a slow approximately 90-second front orbit and independent target drift. Fullscreen uses real reel geometry without the machine, a slight slow whole-frame drift and overscan to keep edges filled. Simulated payline results trigger payout-scaled coin counts. Jackpots emit up to 192 animated instances in three batches of 64 for ten seconds and pulse the top lamp. This is decorative animation without wagering or transactions.

Static cabinet pieces are batched by material. Untextured opaque surfaces use a compiled lit Filament material with base color, metallic, roughness and emission parameters. This preserves lighting and reflections while avoiding the cost of the generic glTF shader. Textured reels and the baked casino surfaces retain their original material paths. ACES tone mapping and FXAA remain enabled. Ambient occlusion, bloom, transparent cabinet glazing and real-time shadows are disabled on this profile.

## Physical pacing and preservation

Signed candidate `c53ea6fcbf48baab21d95460917005c151732dc88c12355aef7ea8de6cbb0588` was installed as an update on the physical AFTDEC012E. At eight seconds, the garden cabinet with the casino background and jackpot shower presented 126 buffers at 29.9995 per second. Fullscreen classic presented 127 buffers at 30.0002 per second. Median intervals were approximately 33.33 milliseconds. These are SurfaceFlinger actual-present timestamps, not screen-recording frame rates. The samples cover approximately four seconds each; 25-second native recordings provide additional visual evidence but do not establish a long-duration thermal result.

All seven app preferences and five screensaver/sleep settings were compared before and after the check and restored exactly. The TV returned to its original asleep state. Back from each directly launched preview returned to the underlying Fire TV UI. Earlier Settings/Preview/Back testing separately verified return to app settings.

Final rendering candidate `b1989a2ad94409fb952db95867a1c53d193b076f98ba507e7aa9cc4bb078b40e` reduces the lamp emission and retains its pulsing celebration. Its physical garden sample presented 125 buffers at 29.5224 per second, with a 33.33 millisecond median interval; fullscreen classic presented 127 buffers at 29.9999 per second. Twelve-second native movies and six current API 34 gallery scenes were captured. All seven app preferences and five system values were restored exactly, and the TV returned asleep. The lamp appears red in the emulator and bright warm during the physical jackpot pulse. No cross-device color equivalence is claimed.

## Native dream and limits

Earlier guarded physical and API34 checks established actual service binding and moving output. The API34 Dream Manager identified `com.jeremykenedy.reelatrium.ReelAtriumDreamService`; Back ended the dream. Selected component and enabled state were restored. A direct activity launch is not evidence of automatic idle activation.

Private rejected experiments include expensive full effects, TAA with dynamic resolution, direct rendering without tone mapping, and an invalid single 192-transform renderable. None is shipped as a passing configuration. The final renderer uses three supported 64-instance batches, fixed resolution, FXAA and the compiled solid material.

## Rebuilding visual assets

Use `tools/build_casino.py` for the original baked casino environment and `tools/build_cabinet.py` for each cabinet and fullscreen layout. Exporting the garden atrium cabinet also writes `assets/materials/solid-surfaces.json`, including glTF emissive-strength multipliers. This descriptor is shared by the cabinet variants. Compile `assets/materials/solid-surfaces.mat` with Filament 1.77.3 `matc -p mobile -a opengl -o assets/materials/solid-surfaces.filamat assets/materials/solid-surfaces.mat` when changing that material. Model generation requires Blender; normal APK builds use the committed assets.

The release-resource APK is `0ee21b586f3b306e6da57cacc149bebece35a01e6ef2c7af1512c0ddc51354e4` (62076478 bytes). Its 38 code, native library, model, reel texture, compiled material and lighting entries are byte-identical to the physically tested b198 candidate. Changes are the native captured preview/banner and asset provenance text. Resource-only build equivalence was checked against the installed TV APK.
