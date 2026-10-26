"""Keep the existing animated reel and fullscreen contracts during scenery changes."""

import hashlib
import json
from pathlib import Path
import struct
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = "38546fccb9cb8ee844107740a79a4ccde40d177b"


def model(raw):
    return json.loads(raw[20:20 + struct.unpack_from("<I", raw, 12)[0]])


class ModelCompatibilityTest(unittest.TestCase):
    def test_every_game_retains_its_original_reel_axles(self):
        for game in ("classic", "palace", "garden"):
            filename = "assets/models/" + game + "_atrium.glb"
            before = model(subprocess.check_output(["git", "show", BASE + ":" + filename], cwd=ROOT))
            after = model((ROOT / filename).read_bytes())
            def axles(data):
                return {node["name"]: {key: value for key, value in node.items() if key not in ("children", "name")}
                        for node in data["nodes"] if node.get("name", "").startswith("Reel_")}
            self.assertEqual(3 if game == "classic" else 5, len(axles(after)))
            self.assertEqual(axles(before), axles(after))

    def test_fullscreen_reels_are_not_changed_by_environment_rebuild(self):
        for game in ("classic", "palace", "garden"):
            filename = "assets/models/fullscreen_" + game + "_atrium.glb"
            before = subprocess.check_output(["git", "show", BASE + ":" + filename], cwd=ROOT)
            self.assertEqual(hashlib.sha256(before).digest(),
                             hashlib.sha256((ROOT / filename).read_bytes()).digest())
