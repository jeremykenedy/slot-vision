# Visible arm candidate, Android code 15

This isolated candidate starts from public primary commit
`38546fccb9cb8ee844107740a79a4ccde40d177b`. It brings the lever stroke and first-scene
readiness fence from the independently tested code 11 work, without the room,
floor, lighting or material experiments in the separate casino rework.

The existing cabinet arm pulls through 70 degrees, holds briefly at the bottom
and returns to rest. Cabinet reels wait until the bottom of the stroke before
every spin. A nonblocking GPU fence and 350ms presentation interval prevent the
first pull from completing while the cabinet is still loading. Fullscreen reels
retain their original timing and camera drift; they do not display a cabinet arm.

All three cabinet models retain their original binary payload bytes. The change
partitions the existing 48 stem triangles from the static chrome batch, appends
index lists, and parents that stem and the existing grip to a hinge. Original
vertices, normals, UVs, textures, materials, reel axles, room geometry and triangle
multiplicities are preserved. The grip and stem occupy the same world positions
at rest. No photograph replaces the cabinet. Fullscreen models, all seasonal
atlases, lighting assets, payout coins, beacon, settings and release signer remain
unchanged.

The two desired surface dimensions are explicitly changed from the public
1280x720 buffer to 1920x1080. The old public physical result of about 30 presented
frames per second applies only to 720p. It is not evidence for this candidate.
The 1080p postprocessing cost measured in the separate rework is a performance
risk; no floor simplification, coin reduction, disabled postprocessing or dynamic
resolution is included. This candidate is held for native image, first-pull,
repeat-pull, payout and clean physical pacing checks. Preserving public assets is
not a claim that the owner's requested casino realism has been accepted.

## Checks

Java tests verify the lever stroke, return continuity, spin delay at every
supported speed, unchanged outcomes and the 192-coin, ten-second jackpot. Geometry
checks verify exact source binary hashes, lossless triangle partitioning,
materials and attributes, rest transforms, a visible downward/forward grip
stroke, unchanged other assets, and rejection of unrelated model layouts. The
split tool and installer are included in the 100% Python statement/branch gate.
The renderer, Android lifecycle and first-frame fence require native checks.

`tools.prepare_lever.prepare(source, destination)` derives the three animated
models from the original published cabinet GLBs. `tests/lever-contract.json`
records the source identity and allowed model changes. The normal APK build uses
the committed models and does not run Blender or the derivation tool.

Native evidence must confirm the actual buffer size, lever visibility before the
first reel movement, full return, repeated spins, all games/seasons, fullscreen,
coins/beacon and lifecycle. Compare code 15 with the public renderer separately
from the held casino/floor experiments. No release, host integration or device
compatibility beyond the existing public evidence is established by this build.
