"""Prove the arm split retains the published cabinet geometry and materials."""

import copy
import hashlib
import json
import math
import struct
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from tools.prepare_lever import prepare, split_lever

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "tests/lever-contract.json").read_text())


def unpack(raw):
    size = struct.unpack_from("<I", raw, 12)[0]
    return json.loads(raw[20 : 20 + size]), raw[28 + size :]


def pack(data, binary):
    text = json.dumps(data, separators=(",", ":")).encode()
    text += b" " * (-len(text) % 4)
    return (
        struct.pack(
            "<5I", 0x46546C67, 2, 28 + len(text) + len(binary), len(text), 0x4E4F534A
        )
        + text
        + struct.pack("<II", len(binary), 0x004E4942)
        + binary
    )


def original(game):
    after, binary = unpack(
        (ROOT / "assets/models" / (game + "_atrium.glb")).read_bytes()
    )
    contract = CONTRACT["games"][game]
    data = copy.deepcopy(after)
    data["nodes"] = data["nodes"][: contract["nodes"]]
    data["meshes"] = data["meshes"][: contract["meshes"]]
    grip = next(n for n in data["nodes"] if n.get("name") == "Lever_Grip")
    grip["name"] = "Cabinet_Grip"
    grip["translation"] = list(contract["grip_translation"])
    chrome = next(n for n in data["nodes"] if n.get("name") == "Cabinet_Chrome")
    data["meshes"][chrome["mesh"]]["primitives"][0]["indices"] = contract[
        "chrome_indices"
    ]
    data["accessors"] = data["accessors"][: contract["accessors"]]
    data["bufferViews"] = data["bufferViews"][: contract["buffer_views"]]
    data["buffers"] = contract["buffers"]
    data["scenes"][data.get("scene", 0)]["nodes"] = contract["scene_nodes"]
    return data, binary[: contract["original_binary_bytes"]]


def indices(data, binary, index):
    accessor = data["accessors"][index]
    view = data["bufferViews"][accessor["bufferView"]]
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    values = struct.unpack_from("<" + "H" * accessor["count"], binary, start)
    return Counter(tuple(values[i : i + 3]) for i in range(0, len(values), 3))


class LeverModelsTest(unittest.TestCase):
    def test_all_original_visual_bytes_and_other_assets_are_unchanged(self):
        for game, contract in CONTRACT["games"].items():
            data, binary = original(game)
            self.assertEqual(
                contract["original_binary_sha256"], hashlib.sha256(binary).hexdigest()
            )
            normalized = json.dumps(
                data, sort_keys=True, separators=(",", ":")
            ).encode()
            self.assertEqual(
                contract["original_json_sha256"], hashlib.sha256(normalized).hexdigest()
            )
            after = (ROOT / "assets/models" / (game + "_atrium.glb")).read_bytes()
            self.assertEqual(after, split_lever(pack(data, binary)))
        for name, sha in CONTRACT["unchanged_assets"].items():
            self.assertEqual(
                sha, hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), name
            )

    def test_triangle_partition_is_lossless_and_keeps_normals_uvs_material_and_winding(
        self,
    ):
        for game in CONTRACT["games"]:
            data, binary = unpack(
                (ROOT / "assets/models" / (game + "_atrium.glb")).read_bytes()
            )
            old, _ = original(game)
            chrome = next(n for n in data["nodes"] if n.get("name") == "Cabinet_Chrome")
            pivot = next(n for n in data["nodes"] if n.get("name") == "Lever_Pivot")
            children = [data["nodes"][i] for i in pivot["children"]]
            self.assertEqual(
                {"Lever_Grip", "Lever_Stem"}, {n["name"] for n in children}
            )
            stem = next(n for n in children if n["name"] == "Lever_Stem")
            kept = data["meshes"][chrome["mesh"]]["primitives"][0]
            moving = data["meshes"][stem["mesh"]]["primitives"][0]
            before = old["meshes"][chrome["mesh"]]["primitives"][0]
            self.assertEqual(before["attributes"], moving["attributes"])
            self.assertEqual(before["material"], moving["material"])
            self.assertEqual(
                indices(data, binary, before["indices"]),
                indices(data, binary, kept["indices"])
                + indices(data, binary, moving["indices"]),
            )
            self.assertEqual(48, sum(indices(data, binary, moving["indices"]).values()))
            self.assertNotIn("mesh", pivot)
            for axis in range(3):
                self.assertAlmostEqual(
                    chrome.get("translation", [0, 0, 0])[axis],
                    pivot["translation"][axis] + stem["translation"][axis],
                    places=7,
                )
            grip = next(n for n in children if n["name"] == "Lever_Grip")
            rest = [pivot["translation"][i] + grip["translation"][i] for i in range(3)]
            self.assertEqual(CONTRACT["games"][game]["grip_translation"], rest)
            angle = math.radians(70)
            pulled_y = (
                pivot["translation"][1]
                + grip["translation"][1] * math.cos(angle)
                - grip["translation"][2] * math.sin(angle)
            )
            pulled_z = (
                pivot["translation"][2]
                + grip["translation"][1] * math.sin(angle)
                + grip["translation"][2] * math.cos(angle)
            )
            self.assertLess(pulled_y, rest[1] - 0.30)
            self.assertGreater(pulled_z, rest[2] + 0.20)

    def test_file_preparation_writes_the_expected_animated_model(self):
        data, binary = original("classic")
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.glb"
            output = Path(folder) / "animated.glb"
            source.write_bytes(pack(data, binary))
            prepare(source, output)
            self.assertEqual(
                (ROOT / "assets/models/classic_atrium.glb").read_bytes(),
                output.read_bytes(),
            )

    def test_rejects_incomplete_or_unexpected_source_models(self):
        data, binary = original("classic")
        valid = pack(data, binary)
        for value in (b"BAD!" + valid[4:], valid[:-4]):
            with self.assertRaisesRegex(ValueError, "complete GLB"):
                split_lever(value)
        bad = bytearray(valid)
        size = struct.unpack_from("<I", bad, 12)[0]
        struct.pack_into("<I", bad, 24 + size, 0)
        with self.assertRaisesRegex(ValueError, "binary GLB"):
            split_lever(bad)
        with self.assertRaisesRegex(ValueError, "already"):
            split_lever((ROOT / "assets/models/classic_atrium.glb").read_bytes())
        chrome = next(n for n in data["nodes"] if n.get("name") == "Cabinet_Chrome")
        chrome["rotation"] = [0, 0, 0, 1]
        with self.assertRaisesRegex(ValueError, "translated chrome"):
            split_lever(pack(data, binary))
        chrome.pop("rotation")
        attribute = data["meshes"][chrome["mesh"]]["primitives"][0]["attributes"][
            "POSITION"
        ]
        accessor = data["accessors"][attribute]
        accessor["componentType"] = 5123
        with self.assertRaisesRegex(ValueError, "accessor format"):
            split_lever(pack(data, binary))
        accessor["componentType"] = 5126
        view = data["bufferViews"][accessor["bufferView"]]
        view["byteStride"] = 12
        with self.assertRaisesRegex(ValueError, "accessor format"):
            split_lever(pack(data, binary))
        view.pop("byteStride")
        grip = next(n for n in data["nodes"] if n.get("name") == "Cabinet_Grip")
        grip["translation"][0] += 10
        with self.assertRaisesRegex(ValueError, "48-triangle"):
            split_lever(pack(data, binary))
