"""Build the original meter-scale cabinet, reels and lounge scene with Blender 4.5 LTS."""

import argparse
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument(
    "--game", choices=("classic", "palace", "garden"), default="classic"
)
parser.add_argument(
    "--season",
    choices=("atrium", "spring", "summer", "autumn", "winter"),
    default="atrium",
)
parser.add_argument("--render", action="store_true")
args = parser.parse_args(
    sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)


def material(name, color, metal=0, roughness=0.3, emission=0, alpha=1):
    result = bpy.data.materials.new(name)
    result.use_nodes = True
    bsdf = result.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, alpha)
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Roughness"].default_value = roughness
    result.use_backface_culling = True
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*color, 1)
        bsdf.inputs["Emission Strength"].default_value = emission
    if alpha < 1:
        bsdf.inputs["Alpha"].default_value = alpha
        result.surface_render_method = "DITHERED"
    return result


PALETTES = {
    "atrium": ((0.64, 0.38, 0.10), (0.04, 0.65, 0.49)),
    "spring": ((0.68, 0.43, 0.25), (0.62, 0.10, 0.30)),
    "summer": ((0.72, 0.43, 0.08), (0.015, 0.56, 0.65)),
    "autumn": ((0.55, 0.20, 0.055), (0.95, 0.22, 0.025)),
    "winter": ((0.56, 0.65, 0.73), (0.045, 0.32, 0.70)),
}
trim_color, accent_color = PALETTES[args.season]
trim = material("Trim", trim_color, 1, 0.19)
chrome = material("Chrome", (0.75, 0.79, 0.82), 1, 0.12)
cabinet = material("Cabinet", (0.012, 0.018, 0.017), 0.75, 0.18)
enamel = material("Enamel", (0.018, 0.027, 0.024), 0.35, 0.22)
black = material("Recess", (0.006, 0.007, 0.008), 0.12, 0.38)
accent = material("Accent", accent_color, 0.12, 0.21, 1.5)
warm = material("Warm light", (1, 0.62, 0.24), 0, 0.24, 3)
ivory = material("Ivory", (0.78, 0.72, 0.54), 0.15, 0.26)
glass = material("Glass", (0.055, 0.065, 0.07), 0.15, 0.10, alpha=0.075)
rubber = material("Rubber", (0.018, 0.009, 0.010), 0.05, 0.25)
grip = material("Grip", (0.19, 0.008, 0.016), 0.05, 0.15)
floor_mat = material("Lounge floor", (0.04, 0.025, 0.014), 0.0, 0.48)
velvet = material("Velvet", (0.025, 0.012, 0.013), 0.05, 0.66)
# Photographed wood gives the large floor a material scale and avoids a mirror-like studio wash.
wood_path = ROOT / "assets/materials/wood_floor_diff.jpg"
if wood_path.exists():
    nodes = floor_mat.node_tree.nodes
    links = floor_mat.node_tree.links
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = bpy.data.images.load(str(wood_path))
    coordinates = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (20, 24, 1)
    links.new(coordinates.outputs["UV"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], texture.inputs["Vector"])
    nodes.get("Principled BSDF").inputs["Base Color"].default_value = (
        0.20,
        0.20,
        0.20,
        1,
    )
    links.new(
        texture.outputs["Color"], nodes.get("Principled BSDF").inputs["Base Color"]
    )
    normal_texture = nodes.new("ShaderNodeTexImage")
    normal_texture.image = bpy.data.images.load(
        str(ROOT / "assets/materials/wood_floor_normal.jpg")
    )
    normal_texture.image.colorspace_settings.name = "Non-Color"
    links.new(mapping.outputs["Vector"], normal_texture.inputs["Vector"])
    normal = nodes.new("ShaderNodeNormalMap")
    normal.inputs["Strength"].default_value = 0.3
    links.new(normal_texture.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], nodes.get("Principled BSDF").inputs["Normal"])


def finish(obj, name, mat, bevel=0, smooth=True):
    obj.name = name
    obj.data.materials.append(mat)
    if bevel:
        modifier = obj.modifiers.new("Machined edge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 6
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    if smooth:
        for poly in obj.data.polygons:
            poly.use_smooth = True
        modifier = obj.modifiers.new("Weighted surface normals", "WEIGHTED_NORMAL")
        modifier.keep_sharp = True
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    return obj


def box(name, location, dimensions, mat, bevel=0.008):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, name, mat, bevel)


def sphere(name, location, radius, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=32, ring_count=20, radius=radius, location=location
    )
    return finish(bpy.context.object, name, mat)


def cylinder(name, location, radius, depth, mat, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=48, radius=radius, depth=depth, location=location, rotation=rotation
    )
    return finish(bpy.context.object, name, mat, 0.0015)


def tube(name, points, radius, mat):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = radius
    curve.bevel_resolution = 4
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, xyz in zip(spline.points, points):
        point.co = (*xyz, 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    curve.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    obj.select_set(False)
    return obj


def frame(name, x, y, z, width, height, corner, radius, mat):
    points = []
    for cx, cz, start in (
        (width / 2 - corner, height / 2 - corner, 0),
        (-width / 2 + corner, height / 2 - corner, 90),
        (-width / 2 + corner, -height / 2 + corner, 180),
        (width / 2 - corner, -height / 2 + corner, 270),
    ):
        for step in range(13):
            angle = math.radians(start + step * 90 / 12)
            points.append(
                (
                    x + cx + corner * math.cos(angle),
                    y,
                    z + cz + corner * math.sin(angle),
                )
            )
    points.append(points[0])
    return tube(name, points, radius, mat)


width = 0.91 if args.game == "classic" else 1.06
window_width = width - 0.18
window_height = (
    0.70 if args.game == "classic" else 0.63 if args.game == "palace" else 0.76
)
center_z = 1.035
top = center_z + window_height / 2
bottom = center_z - window_height / 2

# The opening is an actual cavity. Side cheeks, rear shell and front panels surround the reels.
box("Rear shell", (0, 0.39, 0.88), (width, 0.15, 1.42), cabinet, 0.065)
for side in (-1, 1):
    box(
        "Sculpted side cheek",
        (side * (width / 2 - 0.055), 0.015, 0.90),
        (0.11, 0.75, 1.47),
        cabinet,
        0.046,
    )
    box(
        "Side enamel inset",
        (side * (width / 2 + 0.002), 0.04, 0.90),
        (0.012, 0.59, 1.19),
        enamel,
        0.005,
    )
    for inset in (-0.22, 0.22):
        tube(
            "Side brass inlay",
            [
                (side * (width / 2 + 0.009), inset, 0.36),
                (side * (width / 2 + 0.009), inset, 1.43),
            ],
            0.0025,
            trim,
        )
box(
    "Upper door",
    (0, -0.16, (top + 1.57) / 2),
    (width - 0.075, 0.39, 1.57 - top),
    cabinet,
    0.025,
)
box(
    "Lower door",
    (0, -0.15, (0.19 + bottom) / 2),
    (width - 0.075, 0.40, bottom - 0.19),
    enamel,
    0.028,
)
box(
    "Reel chamber rear",
    (0, 0.34, center_z),
    (window_width, 0.018, window_height + 0.06),
    black,
)
frame(
    "Machined reel surround",
    0,
    -0.366,
    center_z,
    window_width + 0.046,
    window_height + 0.045,
    0.055,
    0.018,
    chrome,
)
frame(
    "Inset brass seal",
    0,
    -0.375,
    center_z,
    window_width + 0.015,
    window_height + 0.015,
    0.044,
    0.007,
    trim,
)
frame(
    "Inner black gasket",
    0,
    -0.367,
    center_z,
    window_width - 0.01,
    window_height - 0.01,
    0.041,
    0.008,
    black,
)

# Large rounded crown and translucent marquee sit above the mechanical window.
box("Rounded crown", (0, 0.015, 1.575), (width + 0.035, 0.76, 0.27), cabinet, 0.063)
box("Crown front brass", (0, -0.378, 1.575), (width - 0.055, 0.025, 0.175), trim, 0.035)
box(
    "Crown dark glass", (0, -0.395, 1.575), (width - 0.095, 0.022, 0.137), enamel, 0.028
)
for side in (-1, 1):
    for line in range(8):
        x = side * (0.12 + line * 0.027)
        tube(
            "Marquee sunburst etching",
            [(x, -0.409, 1.535), (x * 0.79, -0.409, 1.615)],
            0.0013,
            trim,
        )
cylinder(
    "Marquee medallion rim", (0, -0.416, 1.575), 0.050, 0.012, trim, (math.pi / 2, 0, 0)
)
cylinder(
    "Marquee medallion enamel",
    (0, -0.424, 1.575),
    0.043,
    0.009,
    accent,
    (math.pi / 2, 0, 0),
)
for side in (-1, 1):
    tube(
        "Cabinet running light",
        [
            (side * (width / 2 - 0.038), -0.375, 0.23),
            (side * (width / 2 - 0.038), -0.375, 1.44),
        ],
        0.0038,
        accent,
    )

# A projected, beveled control shelf carries actual angled buttons and a coin return.
box("Control shelf brass", (0, -0.42, 0.584), (width + 0.035, 0.24, 0.105), trim, 0.026)
box(
    "Control shelf enamel",
    (0, -0.463, 0.618),
    (width - 0.035, 0.16, 0.048),
    enamel,
    0.015,
)
for index in range(5):
    x = -0.28 + index * 0.105
    cylinder(
        "Button chrome rim",
        (x, -0.513, 0.645),
        0.034,
        0.012,
        chrome,
        (math.pi / 6, 0, 0),
    )
    cylinder(
        "Button inset",
        (x, -0.518, 0.653),
        0.027,
        0.010,
        accent if index == 4 else ivory,
        (math.pi / 6, 0, 0),
    )
box("Coin intake chrome", (0.32, -0.516, 0.642), (0.095, 0.045, 0.023), chrome, 0.006)
box("Coin intake slot", (0.32, -0.536, 0.646), (0.067, 0.006, 0.007), black, 0.002)
box("Return tray recess", (0, -0.36, 0.345), (width * 0.65, 0.048, 0.105), black, 0.017)
box(
    "Return tray lower chrome",
    (0, -0.395, 0.299),
    (width * 0.66, 0.10, 0.018),
    chrome,
    0.008,
)
frame("Return tray rim", 0, -0.390, 0.347, width * 0.66, 0.105, 0.025, 0.0045, trim)
frame("Lower service door", 0, -0.361, 0.418, width - 0.17, 0.34, 0.035, 0.003, trim)
for side in (-1, 1):
    for z in (0.24, 0.51):
        cylinder(
            "Service screw",
            (side * (width / 2 - 0.10), -0.365, z),
            0.004,
            0.003,
            chrome,
            (math.pi / 2, 0, 0),
        )
box("Plinth chrome", (0, 0.01, 0.145), (width + 0.08, 0.84, 0.075), chrome, 0.025)
box("Plinth black", (0, 0.01, 0.092), (width + 0.115, 0.88, 0.055), black, 0.021)
tube(
    "Plinth warm strip",
    [(-width / 2, -0.439, 0.10), (width / 2, -0.439, 0.10)],
    0.003,
    warm,
)
for x in (-width * 0.35, width * 0.35):
    box("Rubber leveling foot", (x, 0.20, 0.035), (0.10, 0.10, 0.06), rubber, 0.012)

lever_x = width / 2 + 0.065
cylinder(
    "Handle pivot chrome",
    (lever_x, -0.02, 0.93),
    0.055,
    0.12,
    chrome,
    (0, math.pi / 2, 0),
)
sphere("Handle pivot cap", (lever_x + 0.065, -0.02, 0.93), 0.044, cabinet)
tube(
    "Chrome pull lever",
    [
        (lever_x + 0.07, -0.02, 0.93),
        (lever_x + 0.105, -0.08, 1.02),
        (lever_x + 0.105, -0.17, 1.26),
    ],
    0.012,
    chrome,
)
sphere("Polished handle grip", (lever_x + 0.105, -0.17, 1.29), 0.046, grip)

# Full cylinders rotate about their true axle, rather than sliding a picture behind a window.
atlas_name = "classic" if args.game == "classic" else args.season
atlas_path = ROOT / "assets/textures" / ("symbols_" + atlas_name + ".png")
paper = material("ReelPaper", (0.91, 0.87, 0.72), 0.05, 0.32)
if atlas_path.exists():
    image_node = paper.node_tree.nodes.new("ShaderNodeTexImage")
    image_node.image = bpy.data.images.load(str(atlas_path))
    image_node.extension = "REPEAT"
    paper.node_tree.links.new(
        image_node.outputs["Color"],
        paper.node_tree.nodes.get("Principled BSDF").inputs["Base Color"],
    )
columns = 3 if args.game == "classic" else 5
slots = 16 if args.game == "garden" else 8
radius = 0.405 if args.game == "garden" else 0.38 if args.game == "classic" else 0.34
segments = slots * 16
for index in range(columns):
    reel_width = (window_width - 0.025) / columns
    x = (index - (columns - 1) / 2) * reel_width
    parent = bpy.data.objects.new("Reel_" + str(index), None)
    bpy.context.collection.objects.link(parent)
    parent.location = (x, 0.04, center_z)
    vertices, faces, uv_faces = [], [], []
    for step in range(segments + 1):
        angle = step / segments * math.tau
        for side in (-1, 1):
            vertices.append(
                (
                    side * (reel_width - 0.008) / 2,
                    -radius * math.cos(angle),
                    radius * math.sin(angle),
                )
            )
    for step in range(segments):
        faces.append((step * 2, step * 2 + 1, step * 2 + 3, step * 2 + 2))
        v0 = step / segments * (slots / 8) + 0.5 / 8
        v1 = (step + 1) / segments * (slots / 8) + 0.5 / 8
        uv_faces.append(((0, v0), (1, v0), (1, v1), (0, v1)))
    mesh = bpy.data.meshes.new("Machined cylindrical reel")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv = mesh.uv_layers.new(name="Reel print")
    for polygon, coordinates in zip(mesh.polygons, uv_faces):
        polygon.use_smooth = True
        for loop, xy in zip(polygon.loop_indices, coordinates):
            uv.data[loop].uv = xy
    reel = bpy.data.objects.new("Printed reel " + str(index), mesh)
    bpy.context.collection.objects.link(reel)
    reel.data.materials.append(paper)
    reel.parent = parent
    if index:
        tube(
            "Reel separator chrome",
            [
                (x - reel_width / 2, -0.379, bottom + 0.015),
                (x - reel_width / 2, -0.379, top - 0.015),
            ],
            0.003,
            chrome,
        )

box(
    "Protective reel glass",
    (0, -0.394, center_z),
    (window_width - 0.025, 0.003, window_height - 0.025),
    glass,
    0.012,
)

# Both environments are modeled geometry. Static objects are merged by material.
environment_start = set(bpy.data.objects)
box("Lounge floor", (0, 0, -0.018), (8, 10, 0.025), floor_mat, 0.001)
box("Velvet wall", (0, 1.12, 1.7), (8, 0.09, 3.5), velvet, 0.015)
for x in (-2.2, -1.65, -1.1, -0.55, 0, 0.55, 1.1, 1.65, 2.2):
    box("Padded wall panel", (x, 1.055, 1.6), (0.50, 0.055, 2.9), velvet, 0.035)
    tube(
        "Wall brass bead",
        [(x - 0.265, 1.015, 0.10), (x - 0.265, 1.015, 3.1)],
        0.0018,
        trim,
    )
for side in (-1, 1):
    x = side * 1.02
    cylinder("Sconce stem", (x, 0.92, 1.35), 0.015, 0.48, trim)
    for z in (1.15, 1.55):
        globe = sphere("Frosted sconce globe", (x, 0.92, z), 0.072, warm)
        globe.scale = (0.68, 0.68, 1)


shadow_material = material("Contact shadow", (0, 0, 0), 0, 1, alpha=0.5)
shadow_image = shadow_material.node_tree.nodes.new("ShaderNodeTexImage")
shadow_image.image = bpy.data.images.load(
    str(ROOT / "assets/textures/contact_shadow.png")
)
shadow_bsdf = shadow_material.node_tree.nodes.get("Principled BSDF")
shadow_material.node_tree.links.new(
    shadow_image.outputs["Color"], shadow_bsdf.inputs["Base Color"]
)
shadow_material.node_tree.links.new(
    shadow_image.outputs["Alpha"], shadow_bsdf.inputs["Alpha"]
)


def contact_shadow(x, y, width=0.92, depth=0.86):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y, 0.001))
    obj = bpy.context.object
    obj.scale = (width, depth, 1)
    return finish(obj, "Contact shadow", shadow_material)


contact_shadow(0, 0, 1.35, 1.3)

lounge_objects = set(bpy.data.objects) - environment_start
for obj in lounge_objects:
    obj.name = "Lounge_" + obj.name

casino_start = set(bpy.data.objects)
carpet = floor_mat.copy()
carpet.name = "Casino floor"
wall = material("Casino wall", (0.012, 0.018, 0.028), 0, 0.8)
blue_screen = material("Casino blue screen", (0.008, 0.09, 0.21), 0, 0.45, 0.8)
red_screen = material("Casino reel display", (0.75, 0.75, 0.75), 0, 0.45, 0.1)
screen_image = red_screen.node_tree.nodes.new("ShaderNodeTexImage")
screen_image.image = bpy.data.images.load(
    str(ROOT / "assets/textures/casino_screen.png")
)
red_screen.node_tree.links.new(
    screen_image.outputs["Color"],
    red_screen.node_tree.nodes.get("Principled BSDF").inputs["Base Color"],
)
casino_gold = material("Casino gold light", (0.42, 0.20, 0.035), 0.8, 0.32, 0.3)
box("Carpet", (0, 0, -0.023), (10, 14, 0.025), carpet, 0.001)
box("Rear wall", (0, 5.7, 2), (12, 0.15, 4), wall, 0.02)
for side in (-1, 1):
    box("Side wall", (side * 4.8, 2.1, 2), (0.15, 9, 4), wall, 0.02)
    for row in range(4):
        x, y = side * (1.65 + 0.34 * row), 0.75 + row * 0.93
        box("Neighbor cabinet", (x, y, 0.78), (0.66, 0.58, 1.48), cabinet, 0.035)
        box("Neighbor bezel", (x, y - 0.306, 1.02), (0.58, 0.045, 0.83), trim, 0.018)
        display = box(
            "Neighbor screen",
            (x, y - 0.334, 1.02),
            (0.49, 0.018, 0.73),
            red_screen,
            0.006,
        )
        uv = display.data.uv_layers.active
        for polygon in display.data.polygons:
            for loop in polygon.loop_indices:
                vertex = display.data.vertices[display.data.loops[loop].vertex_index].co
                uv.data[loop].uv = (vertex.x / 0.49 + 0.5, vertex.z / 0.73 + 0.5)
        box("Neighbor deck", (x, y - 0.36, 0.52), (0.59, 0.22, 0.065), chrome, 0.012)
        for button in range(3):
            cylinder(
                "Neighbor button",
                (x + (button - 1) * 0.13, y - 0.40, 0.565),
                0.026,
                0.012,
                accent,
            )
        box("Neighbor plinth", (x, y, 0.09), (0.72, 0.65, 0.10), black, 0.016)
        box(
            "Neighbor crown",
            (x, y - 0.30, 1.57),
            (0.61, 0.04, 0.11),
            casino_gold,
            0.015,
        )
    for z in (2.18, 2.30):
        tube("Ceiling cove", [(side * 0.72, 0, z), (side * 3.9, 5, z)], 0.012, warm)
    for y in (1.6, 3.5, 5.1):
        cylinder("Column", (side * 3.3, y, 1.5), 0.14, 3, trim)
        cylinder("Column collar", (side * 3.3, y, 2.76), 0.19, 0.07, casino_gold)
for row in range(6):
    y = 0.25 + row * 0.8
    for side in (-1, 1):
        tube(
            "Carpet inlay",
            [
                (side * 0.72, y, 0.0),
                (side * 1.10, y + 0.18, 0.0),
                (side * 0.72, y + 0.36, 0.0),
            ],
            0.004,
            casino_gold,
        )
contact_shadow(0, 0, 1.35, 1.3)
for side in (-1, 1):
    for row in range(4):
        contact_shadow(side * (1.65 + 0.34 * row), 0.75 + row * 0.93)
casino_objects = set(bpy.data.objects) - casino_start
casino_materials = {}
for obj in casino_objects:
    obj.name = "Casino_" + obj.name
    if hasattr(obj.data, "materials"):
        for index, original in enumerate(obj.data.materials):
            if original.name not in casino_materials:
                duplicate = original.copy()
                duplicate.name = "Casino " + original.name
                casino_materials[original.name] = duplicate
            obj.data.materials[index] = casino_materials[original.name]

# One static renderable per material keeps rows of scenery inexpensive on TV GPUs.
for label, objects in (("Lounge", lounge_objects), ("Casino", casino_objects)):
    groups = {}
    for obj in objects:
        if obj.type == "CURVE":
            bpy.ops.object.select_all(action="DESELECT")
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.convert(target="MESH")
            obj.select_set(False)
        if obj.type == "MESH":
            groups.setdefault(obj.data.materials[0].name, []).append(obj)
    for name, members in groups.items():
        bpy.ops.object.select_all(action="DESELECT")
        for obj in members:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = members[0]
        bpy.ops.object.join()
        bpy.context.object.name = label + "_" + name

beacon_mat = material("Jackpot beacon", (0.30, 0.008, 0.004), 0.05, 0.17, 0.05)
cylinder("Beacon chrome base", (0, 0.02, 1.725), 0.065, 0.024, chrome)
cylinder("Jackpot beacon", (0, 0.02, 1.781), 0.051, 0.09, beacon_mat)
sphere("Beacon crown", (0, 0.02, 1.825), 0.051, beacon_mat).scale = (1, 1, 0.30)
cylinder("Beacon silver band", (0, 0.02, 1.754), 0.053, 0.006, chrome)


# Camera and area lights are used for offline geometry inspection only.
def aim(obj, target):
    obj.rotation_euler = (
        (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    )


bpy.ops.object.camera_add(location=(0.42, -3.5, 1.04))
camera = bpy.context.object
camera.name = "Inspection camera"
camera.data.lens = 35
aim(camera, (0, 0, 0.87))
bpy.context.scene.camera = camera
for location, energy, color, size in [
    ((-1.6, -2.2, 3), 350, (1, 0.83, 0.63), 2),
    ((1.6, -0.8, 2.1), 240, (0.70, 0.82, 1), 1.5),
]:
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.data.energy = energy
    light.data.color = color
    light.data.shape = "DISK"
    light.data.size = size
    aim(light, (0, 0, 0.9))

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
world = bpy.data.worlds.new("Studio reflections")
scene.world = world
world.use_nodes = True
hdr = Path.home() / ".cache/screensaver-tools/studio_small_09_1k.hdr"
if hdr.exists():
    environment = world.node_tree.nodes.new("ShaderNodeTexEnvironment")
    environment.image = bpy.data.images.load(str(hdr))
    world.node_tree.links.new(
        environment.outputs["Color"],
        world.node_tree.nodes.get("Background").inputs["Color"],
    )
    world.node_tree.nodes.get("Background").inputs["Strength"].default_value = 0.4

destination = ROOT / "assets/models" / (args.game + "_" + args.season + ".glb")
destination.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(
    filepath=str(destination),
    export_format="GLB",
    export_yup=True,
    export_cameras=False,
    export_lights=False,
    export_apply=True,
    export_materials="EXPORT",
    export_normals=True,
    export_tangents=False,
)
import json
import struct

raw = destination.read_bytes()
json_size = struct.unpack_from("<I", raw, 12)[0]
model = json.loads(raw[20 : 20 + json_size])
for entry in model.get("materials", []):
    entry["doubleSided"] = entry.get("name") == "Glass"
    entry.get("extensions", {}).pop("KHR_materials_clearcoat", None)
    if entry.get("name") in ("Lounge floor", "Velvet", "Contact shadow") or (
        entry.get("name", "").startswith("Casino ")
        and entry.get("name")
        not in ("Casino Trim", "Casino Chrome", "Casino Casino gold light")
    ):
        entry.setdefault("extensions", {})["KHR_materials_unlit"] = {}
    if entry.get("name") == "Lounge floor":
        entry["pbrMetallicRoughness"]["baseColorFactor"] = [0.20, 0.20, 0.20, 1]
model["extensionsUsed"] = sorted(
    set(model.get("extensionsUsed", []) + ["KHR_materials_unlit"])
)
encoded = json.dumps(model, separators=(",", ":")).encode()
encoded += b" " * ((-len(encoded)) % 4)
remaining = raw[20 + json_size :]
destination.write_bytes(
    struct.pack("<III", 0x46546C67, 2, 20 + len(encoded) + len(remaining))
    + struct.pack("<II", len(encoded), 0x4E4F534A)
    + encoded
    + remaining
)
print("Exported", destination)
if args.render:
    scene.render.filepath = str(
        ROOT / "build" / ("cabinet-" + args.game + "-" + args.season + ".png")
    )
    bpy.ops.render.render(write_still=True)
