"""Keep the existing animated reel and fullscreen contracts during scenery changes."""

import hashlib
import json
from pathlib import Path
import struct
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "tests/model-contract.json").read_text())


def model(raw):
    return json.loads(raw[20:20 + struct.unpack_from("<I", raw, 12)[0]])


class ModelCompatibilityTest(unittest.TestCase):
    def test_each_cabinet_has_a_separate_lever_parent(self):
        for game in ("classic", "palace", "garden"):
            data = model((ROOT / "assets/models" / (game + "_atrium.glb")).read_bytes())
            pivot = next(node for node in data["nodes"] if node.get("name") == "Lever_Pivot")
            children = [data["nodes"][index] for index in pivot["children"]]
            self.assertEqual({"Lever_Grip", "Lever_Stem"}, {node["name"] for node in children})
            self.assertTrue(all("mesh" in node for node in children))
            self.assertNotIn("mesh", pivot)
            self.assertAlmostEqual(.93, pivot["translation"][1], places=5)

    def test_shrunk_apk_retains_native_frame_history_fields(self):
        apk = ROOT / "build/slot-vision.apk"
        if not apk.exists():
            self.skipTest("Build the APK to check the native frame-history contract.")
        expected = {"frameId", "gpuFrameDuration", "denoisedGpuFrameDuration", "beginFrame",
                    "endFrame", "backendBeginFrame", "backendEndFrame", "gpuFrameComplete",
                    "vsync", "displayPresent", "presentDeadline", "displayPresentInterval",
                    "compositionToPresentLatency", "expectedPresentLatency", "frameScheduleTime"}
        fields = set()
        with ZipFile(apk) as archive:
            for name in archive.namelist():
                if not name.endswith(".dex"):
                    continue
                dex = archive.read(name)
                count, offset = struct.unpack_from("<II", dex, 0x38)
                strings = []
                for i in range(count):
                    position = struct.unpack_from("<I", dex, offset + i * 4)[0]
                    while dex[position] & 0x80:
                        position += 1
                    position += 1
                    strings.append(dex[position:dex.index(0, position)].decode("utf-8", "replace"))
                count, offset = struct.unpack_from("<II", dex, 0x40)
                types = [strings[struct.unpack_from("<I", dex, offset + i * 4)[0]] for i in range(count)]
                count, offset = struct.unpack_from("<II", dex, 0x50)
                for i in range(count):
                    owner, _, field = struct.unpack_from("<HHI", dex, offset + i * 8)
                    if types[owner] == "Lcom/google/android/filament/Renderer$FrameInfo;":
                        fields.add(strings[field])
        self.assertFalse(expected - fields, "R8 removed fields accessed by Filament JNI: " + str(expected - fields))

    def test_nearby_floor_blends_away_before_background_furniture(self):
        raw = (ROOT / "assets/models/classic_atrium.glb").read_bytes()
        data = model(raw)
        binary = raw[28 + struct.unpack_from("<I", raw, 12)[0]:]
        floor = next(mesh for mesh in data["meshes"] if mesh["name"] == "Casino_Floor")
        primitive = floor["primitives"][0]
        self.assertEqual("BLEND", data["materials"][primitive["material"]]["alphaMode"])
        color = data["accessors"][primitive["attributes"]["COLOR_0"]]
        view = data["bufferViews"][color["bufferView"]]
        offset = view.get("byteOffset", 0) + color.get("byteOffset", 0)
        code, size, maximum = {5121: ("B", 1, 255), 5123: ("H", 2, 65535)}[color["componentType"]]
        alpha = [struct.unpack_from("<" + code, binary, offset + (index * 4 + 3) * size)[0]
                 for index in range(color["count"])]
        self.assertEqual(0, min(alpha))
        self.assertEqual(maximum, max(alpha))

    def test_every_game_retains_its_original_reel_axles(self):
        for game in ("classic", "palace", "garden"):
            filename = "assets/models/" + game + "_atrium.glb"
            after = model((ROOT / filename).read_bytes())
            def axles(data):
                return {node["name"]: {key: value for key, value in node.items() if key not in ("children", "name")}
                        for node in data["nodes"] if node.get("name", "").startswith("Reel_")}
            self.assertEqual(3 if game == "classic" else 5, len(axles(after)))
            self.assertEqual(CONTRACT["games"][game]["axles"], axles(after))

    def test_fullscreen_reels_are_not_changed_by_environment_rebuild(self):
        for game in ("classic", "palace", "garden"):
            filename = "assets/models/fullscreen_" + game + "_atrium.glb"
            self.assertEqual(CONTRACT["games"][game]["fullscreen_sha256"],
                             hashlib.sha256((ROOT / filename).read_bytes()).hexdigest())
