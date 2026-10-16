# Verification

Validation date: October 16, 2026. The current candidate uses Filament 1.77.3 and original 3D cabinet models. Captures of the earlier custom OpenGL prototype are rejected and are not evidence for this candidate. Public release is held pending final physical playback and motion review.

| Device | API | Evidence | Status |
| --- | --- | --- | --- |
| Google TV emulator, sdk_google_atv64_amati_arm64, host GPU | 34 | 1920x1080 native preview, three cabinet layouts, five themes, spinning reels, slow camera orbit, provider persistence, remote preview and Back, repeated renderer creation/destruction | Native PBR preview and test dream checked |
| Google TV emulator, SwiftShader | 34 | Filament first-frame fence stalled | Unsupported test backend; host GPU required for this emulator |
| Fire TV AFTDEC012E, physical | 30 | Previous prototype only | Current preview measured; uninterrupted test dream pending |
| Other Fire TV / Fire OS models | Untested | None | A volunteer with this device is needed |
| Android TV hardware | Untested | None | A volunteer with this device is needed |
| Google TV hardware | Untested | None | A volunteer with this device is needed |

A volunteer with an untested device can report model, OS/API, resolution, startup, remote exit, sleep/wake and sustained frame pacing through the device-testing issue form. No native 4K, reboot persistence, sleep/wake, unattended idle activation or sustained thermal result has been established for this candidate.

## Automated checks

Java tests enforce 100% line and branch coverage for the explicitly scoped `ReelOptions` and `ReelRound` logic. Twenty-four installer tests pass with 100% statement and branch coverage. Spotless and source privacy checks pass. Framework activities, providers, DreamService lifecycle and GPU code require native validation and are outside plain JVM coverage.

The built APK requests no Android permissions. Models, seasonal artwork and lighting maps are bundled. Filament and Kotlin runtime dependencies are pinned and checksum verified, with licenses included in the APK. No runtime content download or reporting client is used.

## Native checks

The three-reel classic, five-reel palace and sixteen-position five-reel garden models rendered on the API 34 host GPU emulator. Atrium, spring, summer, autumn and winter artwork loaded successfully. Successive preview creation and destruction reused the same app process without a recorded crash. The seasonal mipmap path requires explicit `GEN_MIPMAPPABLE` texture usage; the final source includes that flag.

D-pad/Select opened the settings preview and Back returned to settings. The initial PBR candidate used a 15-degree base camera yaw and f/11, 1/125 second, ISO 100 exposure. The updated candidate adds an approximately 90 second front orbit, independent camera target drift and larger framing. Reels now settle on actual symbol positions for simulated payline awards while the camera continues moving.

## Measurements

An 18.022-second 1920x1080 screen recording contained 536 frames, about 29.74 frames per second while recording. A separate SurfaceFlinger sample recorded 674 frames, 30.185 average FPS and zero dropped frames for the app SurfaceView. These are Apple M5 host GPU emulator results and do not establish physical TV performance. Private source measurements and motion recordings are under ignored `build/`.

## Capture provenance and release gates

Reviewed private captures `build/filament-classic-exposure-low.png` and `build/filament-winter-exposure-low.png` come from the running API 34 native preview. They show the current 3D models, physical materials and authored reel artwork. The latter shows the garden five-row layout with winter atlas and chrome trim. `build/filament-classic-motion.mp4` records actual native motion.

Committed screenshots and the small in-app preview now use reviewed native Filament captures. Final physical footage remains pending. Complete uninterrupted physical DreamService playback and remaining lifecycle checks, then review final moving output. Rebuild and verify the signed artifact and remote primary-branch CI before tagging a release. No current candidate is publicly released.

## Physical performance investigation

The initial full effects PBR build was rejected on the physical AFTDEC012E. Its 17.512 second screen recording contained only 29 video frames, about 1.66 captured FPS. A 1280x720 candidate with ambient occlusion, bloom and shadow casting disabled improved a separate SurfaceFlinger sample to 8.108 presented FPS, still below the release threshold. A diagnostic 960x540 surface reached 13.433 presented FPS and is not a release quality choice. These failed candidates remain private and are not compatibility passes.

The current optimization removes unnecessary clearcoat and rear face rendering from opaque materials, uses unlit matte lounge surfaces, and keeps cabinet and reel materials physically lit. Final physical measurements, visual inspection and moving output review remain pending. Preview holds its foreground display awake without changing device timers so an unrelated idle dream cannot invalidate measurements.

The subsequent private 720p candidate removes the full window transparent PBR sheet and accent spotlight while retaining cabinet and reel lighting. Classic preview reached 30.221 presented FPS in a separate SurfaceFlinger sample. The winter garden layout at bright lighting, lively reels and wide camera reached 27.891 presented FPS across 940 frames. A larger framing and approximately 90 second front camera orbit are being checked next; these numbers predate that adjustment.

The first physical testDream attempt bound the service but failed during Fire OS DreamService.attach with a SecurityException because Reel was not the selected active dream package. The platform then showed the underlying Netflix profile chooser. Its 91 frame recording over 3.022 seconds is a failed test setup, not playback evidence. A valid physical check must temporarily select Reel through the existing settings guard, start the dream, then restore the exact live component and enabled state recorded immediately before that test. No TV timer was changed.

The preview surface is capped at 1280x720 and composed into the 1920x1080 display. Captures at 1920x1080 are display screenshots, not a native 1080 rendering claim. The complete traditional symbol, payout and coin candidate reached 29.607 presented FPS across 307 frames in a separate SurfaceFlinger sample before the interrupted dream check.

## Current emulator candidate

The refined casino and contact shadow build ran as the real DreamService on the API 34 host GPU emulator through the AIDL testDream entry point. The Dream Manager identified the exact ReelAtriumDreamService component in preview mode. Its 46.995 second recording contains 1126 frames, about 23.96 captured FPS while recording. A separate Back check confirmed mCurrentDream=null after a three second wake interval, with the app process still healthy. The original selected component and enabled state were restored. This establishes manual native dream playback on this emulator, not unattended activation or physical Fire OS persistence.

Native recording of the first decorative jackpot shows center 777 symbols stopping before proportional beveled gold coins cross the foreground. The beacon alternates bright and dark intervals while the camera continues its front orbit. Invalid background values are rejected without changing the persisted provider settings; all seven settings fit the native remote settings view.

A subsequent guarded physical test selected Reel successfully and displayed its DreamActivity. At 21:09:16 the platform gently woke the dream, then an unrelated DocumentsUI picker and StreamVault activity took foreground. At 21:10:24 StreamVault launched another OPEN_DOCUMENT request. That recording is not an uninterrupted playback or performance result. The app was later killed as a cached background process under memory pressure. Exact selected component, enabled state and all app settings were restored. No new Reel exception occurred in that attempt. Final physical playback and worst case measurements remain pending a coordinated TV window.

The renamed Slot Vision candidate adds cabinet/fullscreen/random view selection and ten-second jackpot coin showers, recycling at most 64 instanced coins. Pure outcome tests verify that every configured speed leaves enough time for the complete jackpot celebration before the next spin. Fullscreen classic center 777 and the shower were captured in the native API 34 preview. A 24.001 second emulator recording contains 377 frames, approximately 15.71 captured FPS under host contention; this is not a physical performance pass. Initial cold fullscreen material compilation briefly shows a black surface and still needs startup timing. Final physical tests must include fullscreen, casino scenery and sustained coins.

Fullscreen palace and garden default-atrium scenes were captured on the API34 host-GPU emulator after explicitly rebinding their atlas with horizontal clamping. Garden shows five rows plus partial edge rows. Palace icon proportions and cold material startup remain under visual review; these captures are not final release acceptance. Physical final-candidate playback remains pending.


## Casino room rebuild

The casino background now has modeled machine banks, upholstered chairs, columns, recessed ceiling coves, tiered chandeliers and an original woven carpet. Static diffuse illumination is baked into vertex colors; champagne metal retains live PBR reflections. Exported material albedos are explicitly retained and the baked color layer replaces the unused white export layer. The first export lost those albedos and was rejected after native inspection.

The corrected room was reviewed in a running API34 host-GPU native preview at a 1920x1080 display size, with a 1280x720 rendering surface. The private `build/casino-native-polished` captures and 12-second motion recording belong to signed candidate `569acfe9c5668bd38960a8f291b905656ddb3bb849900e25302560e4c15c02c8`. All seven app preferences, selected dream and enabled state were preserved. This is emulator visual evidence, not physical TV performance acceptance.

A subsequent 30-second fullscreen recording confirmed whole-frame classic reels and visible rotating payout coins. Review found the jackpot too concentrated around the center. The next candidate increases the bounded jackpot pool to 192 instances across three bounded draws and spreads fullscreen coins across more of the frame. Smaller wins retain payout-scaled counts up to 64; jackpot emission lasts ten seconds. Fresh native motion and physical performance checks were initially pending. Historical 64-coin recordings above do not verify the revised effect.

The first 192-instance prototype failed native construction because Filament caps local transforms at 64 per renderable. That rejected APK is not a working candidate. The corrected revision shares coin geometry across three 64-instance renderables; ordinary wins activate one batch. The corrected signed candidate `f73586b1e529c15c5e2c6f4ac31ccb592ffc640f3c4509999eccb31d26c0e093` subsequently rendered the complete 30-second fullscreen recording in `build/fullscreen-jackpot-batched-native/motion.mp4`. Native movie playback at approximately five and twelve seconds shows a broad moving coin fountain over settled 777 reels. All seven preferences were restored. Physical performance remains pending.

The refreshed casino gallery image is the reviewed native polished-room capture above. The fullscreen gallery image is a frame extracted at6.5 seconds from the corrected native30-second recording, without viewer controls or artwork overlays. Other native scenes retain their prior verified captures because their visible source assets did not change in this room/coin revision. Public README browser review remains pending source push.
