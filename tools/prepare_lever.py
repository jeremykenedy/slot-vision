"""Separate the original cabinet's lever without rebuilding its visual assets."""

import copy
import json
import struct


def split_lever(raw):
    magic, version, length, size, chunk = struct.unpack_from("<5I", raw)
    if (magic, version, length, chunk) != (0x46546C67, 2, len(raw), 0x4E4F534A):
        raise ValueError("Expected a complete GLB 2 model")
    data = json.loads(raw[20 : 20 + size])
    binary_size, binary_type = struct.unpack_from("<II", raw, 20 + size)
    binary = bytearray(raw[28 + size :])
    if binary_type != 0x004E4942 or binary_size != len(binary):
        raise ValueError("Expected one complete binary GLB chunk")
    if any(node.get("name") == "Lever_Pivot" for node in data["nodes"]):
        raise ValueError("The cabinet already has an animated lever")
    chrome = next(
        node for node in data["nodes"] if node.get("name") == "Cabinet_Chrome"
    )
    grip = next(node for node in data["nodes"] if node.get("name") == "Cabinet_Grip")
    if any(key in chrome for key in ("rotation", "scale", "matrix")):
        raise ValueError("Expected the original translated chrome batch")
    primitive = data["meshes"][chrome["mesh"]]["primitives"][0]

    def values(index, code, dimensions, component_type):
        accessor = data["accessors"][index]
        view = data["bufferViews"][accessor["bufferView"]]
        if accessor["componentType"] != component_type or "byteStride" in view:
            raise ValueError("Unexpected original cabinet accessor format")
        offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        count = accessor["count"]
        return list(
            struct.iter_unpack(
                "<" + code * dimensions,
                binary[offset : offset + count * dimensions * struct.calcsize(code)],
            )
        )

    positions = values(primitive["attributes"]["POSITION"], "f", 3, 5126)
    indices = [value[0] for value in values(primitive["indices"], "H", 1, 5123)]
    offset = chrome.get("translation", [0, 0, 0])
    world = [tuple(position[i] + offset[i] for i in range(3)) for position in positions]
    pivot = [grip["translation"][0] - 0.035, 0.93, 0.02]
    # The stem is the one complete tube extending above the fixed pivot hardware.
    # Select entire triangles; never cut a face or alter a vertex/normal/UV.
    parents = list(range(len(positions)))

    def root(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    welded = {}
    for index, position in enumerate(positions):
        key = tuple(round(value, 6) for value in position)
        if key in welded:
            parents[root(index)] = root(welded[key])
        else:
            welded[key] = index
    for index in range(0, len(indices), 3):
        a, b, c = indices[index : index + 3]
        parents[root(b)] = root(a)
        parents[root(c)] = root(a)
    components = {}
    for index in range(0, len(indices), 3):
        triangle = indices[index : index + 3]
        components.setdefault(root(triangle[0]), []).extend(triangle)
    selected = []
    kept = []
    for component in components.values():
        stem = max(world[v][1] for v in component) > 1.2 and all(
            pivot[0] - 0.014 <= world[v][0] <= pivot[0] + 0.049
            and 0.918 <= world[v][1] <= 1.273
            and 0.008 <= world[v][2] <= 0.183
            for v in component
        )
        (selected if stem else kept).extend(component)
    if len(selected) != 144:
        raise ValueError("The original 48-triangle lever stem was not isolated exactly")

    def append_indices(indices):
        binary.extend(b"\0" * (-len(binary) % 4))
        start = len(binary)
        binary.extend(struct.pack("<" + "H" * len(indices), *indices))
        data["bufferViews"].append(
            {
                "buffer": 0,
                "byteOffset": start,
                "byteLength": len(indices) * 2,
                "target": 34963,
            }
        )
        data["accessors"].append(
            {
                "bufferView": len(data["bufferViews"]) - 1,
                "componentType": 5123,
                "count": len(indices),
                "type": "SCALAR",
            }
        )
        return len(data["accessors"]) - 1

    stem = copy.deepcopy(primitive)
    primitive["indices"] = append_indices(kept)
    stem["indices"] = append_indices(selected)
    data["meshes"].append({"name": "Lever_Stem", "primitives": [stem]})
    grip_index = data["nodes"].index(grip)
    grip["name"] = "Lever_Grip"
    grip["translation"] = [grip["translation"][i] - pivot[i] for i in range(3)]
    stem_index = len(data["nodes"])
    data["nodes"].append(
        {
            "name": "Lever_Stem",
            "mesh": len(data["meshes"]) - 1,
            "translation": [offset[i] - pivot[i] for i in range(3)],
        }
    )
    pivot_index = len(data["nodes"])
    data["nodes"].append(
        {
            "name": "Lever_Pivot",
            "translation": pivot,
            "children": [grip_index, stem_index],
        }
    )
    scene = data["scenes"][data.get("scene", 0)]["nodes"]
    scene.remove(grip_index)
    scene.append(pivot_index)
    data["buffers"][0]["byteLength"] = len(binary)
    encoded = json.dumps(data, separators=(",", ":")).encode()
    encoded += b" " * (-len(encoded) % 4)
    binary += b"\0" * (-len(binary) % 4)
    return (
        struct.pack(
            "<5I",
            0x46546C67,
            2,
            28 + len(encoded) + len(binary),
            len(encoded),
            0x4E4F534A,
        )
        + encoded
        + struct.pack("<II", len(binary), 0x004E4942)
        + binary
    )


def prepare(source, destination):
    destination.write_bytes(split_lever(source.read_bytes()))
