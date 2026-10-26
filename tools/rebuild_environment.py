"""Replace the coarse room with photographic surroundings and a projected contact floor.

Run in Blender. Original cabinets are read from build/cabinet-sources, leaving their
reel axles and geometry intact. The surrounding image is scenery, never a cabinet.
"""

import json
import math
from pathlib import Path
import struct
import subprocess

import bpy

ROOT = Path(__file__).resolve().parents[1]
EYE = (0, -3.10, 1.08)
BASE = "38546fccb9cb8ee844107740a79a4ccde40d177b"


def uv(point):
    x, y, z = (point[i] - EYE[i] for i in range(3))
    length = math.sqrt(x * x + y * y + z * z)
    # The photographic plate covers the complete permitted front-camera arc.
    # Use its detail in that field instead of spreading it behind the camera.
    return (0.5 + math.atan2(x, y) / math.radians(150),
            0.5 + math.asin(z / length) / math.radians(90))


def surface(label, image):
    material = bpy.data.materials.new(label + " photographic surroundings")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes.get("Principled BSDF")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = bpy.data.images.load(str(image), check_existing=True)
    links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    shader.inputs["Roughness"].default_value = 1
    return material


def mesh(label, vertices, faces, material):
    data = bpy.data.meshes.new(label)
    data.from_pydata(vertices, [], faces)
    data.update()
    layer = data.uv_layers.new(name="Environment projection")
    for polygon in data.polygons:
        coordinates = [uv(vertices[data.loops[index].vertex_index]) for index in polygon.loop_indices]
        # Avoid interpolating across the longitude seam.
        if max(p[0] for p in coordinates) - min(p[0] for p in coordinates) > 0.5:
            coordinates = [(u + (1 if u < 0.5 else 0), v) for u, v in coordinates]
        for index, coordinate in zip(polygon.loop_indices, coordinates):
            layer.data[index].uv = coordinate
    obj = bpy.data.objects.new(label, data)
    bpy.context.collection.objects.link(obj)
    data.materials.append(material)


def room(label, image):
    material = surface(label, image)
    vertices, faces = [], []
    rings, segments, radius = 32, 96, 22
    for ring in range(rings + 1):
        latitude = -math.pi / 2 + ring * math.pi / rings
        for segment in range(segments + 1):
            longitude = -math.pi + segment * math.tau / segments
            vertices.append((
                EYE[0] + radius * math.cos(latitude) * math.sin(longitude),
                EYE[1] + radius * math.cos(latitude) * math.cos(longitude),
                EYE[2] + radius * math.sin(latitude),
            ))
    for ring in range(rings):
        for segment in range(segments):
            index = ring * (segments + 1) + segment
            faces.append((index, index + 1, index + segments + 2, index + segments + 1))
    mesh(label + "_Surround", vertices, faces, material)
    # A real floor, projected from the same origin, supplies contact and nearby
    # parallax without a visible join to the surrounding room.
    vertices, faces = [], []
    size = 32
    for row in range(size + 1):
        for column in range(size + 1):
            vertices.append((-8 + column * 0.5, -8 + row * 0.5, -0.002))
    for row in range(size):
        for column in range(size):
            index = row * (size + 1) + column
            faces.append((index, index + 1, index + size + 2, index + size + 1))
    mesh(label + "_Floor", vertices, faces, material)


def finalize(path):
    raw = path.read_bytes()
    length = struct.unpack_from("<I", raw, 12)[0]
    model = json.loads(raw[20:20 + length])
    for material in model.get("materials", []):
        if "photographic surroundings" in material.get("name", ""):
            material.setdefault("extensions", {})["KHR_materials_unlit"] = {}
            material["doubleSided"] = True
    model["extensionsUsed"] = sorted(set(model.get("extensionsUsed", []) + ["KHR_materials_unlit"]))
    encoded = json.dumps(model, separators=(",", ":")).encode()
    encoded += b" " * (-len(encoded) % 4)
    remaining = raw[20 + length:]
    path.write_bytes(struct.pack("<III", 0x46546C67, 2, 20 + len(encoded) + len(remaining))
                     + struct.pack("<II", len(encoded), 0x4E4F534A) + encoded + remaining)


for game in ("classic", "palace", "garden"):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    source = ROOT / "build/cabinet-sources" / (game + "_atrium.glb")
    source.parent.mkdir(parents=True, exist_ok=True)
    # Rebuild from the pinned cabinet, not a previously projected output.
    source.write_bytes(subprocess.check_output(
        ["git", "show", BASE + ":assets/models/" + source.name], cwd=ROOT))
    bpy.ops.import_scene.gltf(filepath=str(source))
    for obj in list(bpy.data.objects):
        if obj.name.startswith("Lounge_Contact shadow"):
            obj.name = "Cabinet contact shadow"
        elif obj.name.startswith(("Casino_", "Lounge_")):
            bpy.data.objects.remove(obj, do_unlink=True)
    for label in ("Casino", "Lounge"):
        room(label, ROOT / "assets/environments" / (label.lower() + ".jpg"))
    path = ROOT / "assets/models" / (game + "_atrium.glb")
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", export_yup=True,
                             export_cameras=False, export_lights=False, export_apply=True)
    finalize(path)
