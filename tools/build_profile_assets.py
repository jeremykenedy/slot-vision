#!/usr/bin/env python3
"""Keep original assets and add floor-shader-only variants for local GPU comparisons."""
import json
from pathlib import Path
import shutil
import struct
import sys

source, target = (Path(value).resolve() for value in sys.argv[1:])
if target == source or target.parent.name != "build":
    raise ValueError("Diagnostic output must be a separate build directory")
if target.exists():
    shutil.rmtree(target)
shutil.copytree(source, target)
for game in ("classic", "palace", "garden"):
    path = source / "models" / (game + "_atrium.glb")
    raw = path.read_bytes()
    length, chunk = struct.unpack_from("<II", raw, 12)
    if raw[:4] != b"glTF" or chunk != 0x4e4f534a:
        raise ValueError("A valid GLB is required")
    model = json.loads(raw[20:20 + length])
    count = 0
    for material in model["materials"]:
        if material.get("name", "").endswith(" woven carpet"):
            material.setdefault("extensions", {})["KHR_materials_unlit"] = {}
            count += 1
    if count != 2:
        raise ValueError("Both reviewed room floor materials are required")
    encoded = json.dumps(model, separators=(",", ":")).encode()
    encoded += b" " * (-len(encoded) % 4)
    remainder = raw[20 + length:]
    output = (struct.pack("<III", 0x46546c67, 2, 20 + len(encoded) + len(remainder))
              + struct.pack("<II", len(encoded), chunk) + encoded + remainder)
    (target / "models" / (game + "_atrium_profile_unlit_floor.glb")).write_bytes(output)
