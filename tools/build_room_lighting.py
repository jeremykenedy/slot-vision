"""Build room reflection maps with neutral practical lights rather than a red color wash.

Run with Blender's Python. The visible environment plates remain unchanged. This
authors HDR lighting data for the moving cabinet and coins, not a scene image.
"""

from pathlib import Path
import os
import re
import shutil
import subprocess

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CMGEN = Path(os.environ.get("CMGEN", str(Path.home() /
    ".cache/screensaver-tools/filament-1.77.3/filament/bin/cmgen")))


def write_hdr(path, pixels):
    """Encode linear RGBE directly, without a display transform on lighting data."""
    height, width, _ = pixels.shape
    largest = pixels.max(axis=2)
    _, exponent = np.frexp(np.maximum(largest, 1e-32))
    scale = np.ldexp(np.ones_like(largest), 8 - exponent)
    encoded = np.empty((height, width, 4), dtype=np.uint8)
    encoded[:, :, :3] = np.minimum(pixels * scale[:, :, None], 255).astype(np.uint8)
    encoded[:, :, 3] = (exponent + 128).astype(np.uint8)
    encoded[largest < 1e-32] = 0
    with path.open("wb") as stream:
        stream.write(("#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n-Y %d +X %d\n" % (height, width)).encode())
        for row in encoded[::-1]:
            stream.write(bytes((2, 2, width >> 8, width & 255)))
            for channel in range(4):
                values = row[:, channel].tobytes()
                for start in range(0, width, 127):
                    part = values[start:start + 127]
                    stream.write(bytes((len(part),)))
                    stream.write(part)


def build(name):
    image = bpy.data.images.load(str(ROOT / "art/environments" / (name + "-panorama.png")))
    image.colorspace_settings.name = "Non-Color"
    width, height = image.size
    rgba = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(rgba)
    rgb = rgba.reshape(height, width, 4)[:, :, :3]
    rgb = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    radiance = rgb * 0.35
    longitude = np.linspace(-np.pi, np.pi, width, dtype=np.float32)[None, :]
    latitude = np.linspace(-np.pi / 2, np.pi / 2, height, dtype=np.float32)[:, None]

    def practical(x, y, half_width, half_height, strength, color):
        distance = np.abs((longitude - x + np.pi) % (2 * np.pi) - np.pi)
        shape = np.exp(-((distance / half_width) ** 12)
                       -((np.abs(latitude - y) / half_height) ** 12))
        radiance[:] += shape[:, :, None] * strength * np.asarray(color, dtype=np.float32)

    # Tall off-camera practicals make the manufactured bevels and tumbling coins
    # read as metal; a warmer opposite fill keeps them within the room's palette.
    practical(-0.70, 0.15, 0.12, 0.60, 15, (0.92, 0.97, 1.0))
    practical(0.90, 0.35, 0.17, 0.45, 12, (1.0, 0.90, 0.76))
    practical(0, 1.05, 0.60, 0.12, 14, (1.0, 0.96, 0.88))
    practical(2.80, 0.05, 0.15, 0.60, 4, (0.45, 0.78, 1.0))
    weights = np.maximum(np.cos(latitude), 0)
    luminance = radiance[:, :, 0] * 0.2126 + radiance[:, :, 1] * 0.7152 + radiance[:, :, 2] * 0.0722
    mean = float((luminance * weights).sum() / (weights.sum() * width))
    if not np.isfinite(radiance).all() or not 0.01 < mean < 20:
        raise ValueError("Invalid room radiance")
    radiance *= 0.96 / mean
    directory = ROOT / "build/room-lighting"
    directory.mkdir(parents=True, exist_ok=True)
    hdr = directory / (name + ".hdr")
    write_hdr(hdr, radiance)
    destination = directory / name
    command = [str(CMGEN), "-q", "--format=ktx", "--size=256", "--ibl-samples=256",
               "--deploy=" + str(destination), str(hdr)]
    subprocess.run(command, check=True)

    def diffuse_luminance(path):
        values = [float(value) for value in re.findall(r"[-+]?\d*\.\d+", path.read_text().splitlines()[0])]
        return sum(value * weight for value, weight in zip(values, (0.2126, 0.7152, 0.0722)))

    target = diffuse_luminance(ROOT / "assets/ibl/atrium_sh.txt")
    measured = diffuse_luminance(destination / "sh.txt")
    radiance *= target / measured
    write_hdr(hdr, radiance)
    subprocess.run(command, check=True)
    if abs(diffuse_luminance(destination / "sh.txt") - target) / target > 0.03:
        raise ValueError("Room illumination did not match the existing studio exposure")
    shutil.copy2(destination / (name + "_ibl.ktx"), ROOT / "assets/ibl" / (name + "_ibl.ktx"))


for name in ("casino", "lounge"):
    build(name)
