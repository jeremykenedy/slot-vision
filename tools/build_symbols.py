"""Render original PBR reel symbols with Blender 4.5 Cycles.

Run: blender --background --threads 2 --python tools/build_symbols.py
REEL_REBUILD_SYMBOLS=1 rerenders cached cells. REEL_SYMBOL_ONLY selects comma-separated names.
REEL_SYMBOL_SAMPLES controls samples; REEL_STUDIO_HDR supplies an alternate studio HDR.
Atlas index zero occupies the bottom 512-pixel cell, matching UV v=0..0.125.
"""

from pathlib import Path
import math
import os
import subprocess
import sys
import shutil
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/textures"
WORK = ROOT / "build/symbol-renders"
OUT.mkdir(parents=True, exist_ok=True)
WORK.mkdir(parents=True, exist_ok=True)
HDR = Path(
    os.environ.get(
        "REEL_STUDIO_HDR",
        str(Path.home() / ".cache/screensaver-tools/studio_small_09_1k.hdr"),
    )
)


def material(name, color, metallic=0, roughness=0.24, coat=0.3, transmission=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Roughness"].default_value = roughness
    p.inputs["Coat Weight"].default_value = coat
    p.inputs["Coat Roughness"].default_value = 0.12
    p.inputs["Transmission Weight"].default_value = transmission
    return m


def noise(m, scale, strength):
    nodes = m.node_tree.nodes
    texture = nodes.new("ShaderNodeTexNoise")
    texture.inputs["Scale"].default_value = scale
    texture.inputs["Detail"].default_value = 3
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = 0.025
    m.node_tree.links.new(texture.outputs["Fac"], bump.inputs["Height"])
    m.node_tree.links.new(
        bump.outputs["Normal"], nodes.get("Principled BSDF").inputs["Normal"]
    )


GOLD = material("Brushed champagne gold", (0.70, 0.40, 0.095), 0.83, 0.19)
SILVER = material("Polished platinum", (0.72, 0.80, 0.88), 0.93, 0.16)
RED = material("Cherry lacquer", (0.43, 0.006, 0.014), 0.06, 0.18, 0.65)
GREEN = material("Waxed emerald leaf", (0.025, 0.17, 0.045), 0.02, 0.30, 0.4)
STEM = material("Dark chestnut stem", (0.12, 0.045, 0.012), 0.05, 0.40)
PURPLE = material("Plum skin", (0.11, 0.012, 0.19), 0.03, 0.24, 0.45)
ORANGE = material("Orange peel", (0.78, 0.08, 0.001), 0.01, 0.34, 0.24)
PINK = material("Rose porcelain", (0.83, 0.24, 0.37), 0.08, 0.23, 0.5)
PEARL = material("Pearl shell", (0.92, 0.75, 0.63), 0.23, 0.24, 0.55)
DARK = material("Recess shadow", (0.035, 0.022, 0.012), 0.12, 0.36)
WHITE = material("Winter ivory", (0.91, 0.92, 0.96), 0.25, 0.18, 0.6)
noise(ORANGE, 95, 0.30)
noise(PURPLE, 85, 0.075)


def finish(obj, mat, smooth=True):
    obj.data.materials.append(mat)
    if smooth and hasattr(obj.data, "polygons"):
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
    return obj


def sphere(location, scale, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=location)
    o = bpy.context.object
    o.scale = scale
    return finish(o, mat)


def tube(points, radius, mat):
    curve = bpy.data.curves.new("Shaped wire", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 24
    curve.bevel_depth = radius
    curve.bevel_resolution = 4
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for b, co in zip(spline.bezier_points, points):
        b.co = co
        b.handle_left_type = b.handle_right_type = "AUTO"
    obj = bpy.data.objects.new("Curved detail", curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def polygon(points, mat, depth=0.14, bevel=0.045, z=0.10):
    n = len(points)
    vertices = [(x, y, z + side * depth / 2) for side in (-1, 1) for x, y in points]
    faces = [tuple(reversed(range(n))), tuple(range(n, n * 2))]
    faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    mesh = bpy.data.meshes.new("Sculpted silhouette")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("Beveled solid", mesh)
    bpy.context.collection.objects.link(obj)
    finish(obj, mat, False)
    mod = obj.modifiers.new("Soft machined edges", "BEVEL")
    mod.width = bevel
    mod.segments = 3
    mod = obj.modifiers.new("Weighted face normals", "WEIGHTED_NORMAL")
    mod.keep_sharp = True
    return obj


def torus(location, major, minor, mat, rotation=(0, 0, 0), scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_torus_add(
        major_segments=64,
        minor_segments=12,
        location=location,
        major_radius=major,
        minor_radius=minor,
        rotation=rotation,
    )
    o = bpy.context.object
    o.scale = scale
    return finish(o, mat)


def leaf(x, y, length=0.7, angle=0, mat=GREEN, toothed=False):
    # A curved, solid leaf with a raised midrib, rather than a printed polygon.
    vertices = []
    steps = 16
    for i in range(steps + 1):
        t = i / steps
        center = (t - 0.5) * length
        width = math.sin(math.pi * t) * length * 0.27
        if toothed:
            width *= 0.72 + 0.28 * math.cos(t * math.pi * 8)
        for side in (-1, 0, 1):
            lx, ly = side * width, center
            vertices.append(
                (
                    x + lx * math.cos(angle) - ly * math.sin(angle),
                    y + lx * math.sin(angle) + ly * math.cos(angle),
                    0.21 + 0.13 * math.sin(math.pi * t) - 0.045 * abs(side),
                )
            )
    faces = []
    for i in range(steps):
        for j in range(2):
            a = i * 3 + j
            faces.append((a, a + 1, a + 4, a + 3))
    mesh = bpy.data.meshes.new("Curved leaf surface")
    mesh.from_pydata(vertices, [], faces)
    o = bpy.data.objects.new("Living leaf", mesh)
    bpy.context.collection.objects.link(o)
    finish(o, mat)
    solid = o.modifiers.new("Leaf thickness", "SOLIDIFY")
    solid.thickness = 0.018
    tube(
        [
            (
                x + math.sin(angle) * length * 0.44,
                y - math.cos(angle) * length * 0.44,
                0.235,
            ),
            (x, y, 0.35),
            (
                x - math.sin(angle) * length * 0.44,
                y + math.cos(angle) * length * 0.44,
                0.235,
            ),
        ],
        0.009,
        GOLD,
    )


def cherries():
    sphere((-0.32, -0.28, 0.18), (0.39, 0.42, 0.38), RED)
    sphere((0.32, -0.31, 0.21), (0.40, 0.43, 0.39), RED)
    tube([(-0.32, 0.02, 0.25), (-0.23, 0.46, 0.20), (0.16, 0.77, 0.17)], 0.035, STEM)
    tube([(0.32, 0.04, 0.27), (0.37, 0.38, 0.19), (0.16, 0.77, 0.17)], 0.033, STEM)
    leaf(0.37, 0.61, 0.57, -0.95)


def bell():
    rings = [
        (-0.62, 0.63),
        (-0.55, 0.60),
        (-0.45, 0.50),
        (-0.20, 0.38),
        (0.15, 0.30),
        (0.43, 0.23),
        (0.52, 0.12),
    ]
    vertices = [
        (r * math.cos(a * math.tau / 64), y, 0.04 + r * math.sin(a * math.tau / 64))
        for y, r in rings
        for a in range(64)
    ]
    faces = [
        (
            j * 64 + a,
            j * 64 + (a + 1) % 64,
            (j + 1) * 64 + (a + 1) % 64,
            (j + 1) * 64 + a,
        )
        for j in range(len(rings) - 1)
        for a in range(64)
    ]
    mesh = bpy.data.meshes.new("Cast bell body")
    mesh.from_pydata(vertices, [], faces)
    o = bpy.data.objects.new("Golden bell", mesh)
    bpy.context.collection.objects.link(o)
    finish(o, GOLD)
    solid = o.modifiers.new("Cast wall", "SOLIDIFY")
    solid.thickness = 0.045
    torus((0, -0.58, 0.04), 0.61, 0.045, GOLD, (math.pi / 2, 0, 0))
    torus((0, 0.39, 0.04), 0.25, 0.022, GOLD, (math.pi / 2, 0, 0))
    sphere((0, -0.68, 0.13), (0.115, 0.15, 0.115), GOLD)
    torus((0, 0.66, 0.08), 0.12, 0.035, GOLD)


def jewel(ruby=False):
    colors = [(0.48, 0.006, 0.035)] if ruby else [(0.35, 0.75, 0.95)]
    mats = [
        material(
            "Cut ruby crystal" if ruby else "Cut diamond crystal",
            c,
            0.10,
            0.055,
            0.65,
            0.60,
        )
        for c in colors
    ]
    mats[0].node_tree.nodes.get("Principled BSDF").inputs["IOR"].default_value = 1.78
    outline = [(-0.69, 0.25), (-0.40, 0.61), (0.40, 0.61), (0.69, 0.25), (0, -0.73)]
    if ruby:
        outline = [
            (math.sin(i * math.tau / 8) * 0.61, math.cos(i * math.tau / 8) * 0.75)
            for i in range(8)
        ]
    n = len(outline)
    vertices = (
        [(x, y, 0.10) for x, y in outline]
        + [(x * 0.55, y * 0.52, 0.43) for x, y in outline]
        + [(0, 0, -0.19)]
    )
    faces = [tuple(range(n, n * 2))]
    for i in range(n):
        faces.extend(
            [
                (i, (i + 1) % n, (i + 1) % n + n),
                (i, (i + 1) % n + n, i + n),
                (i, n * 2, (i + 1) % n),
            ]
        )
    mesh = bpy.data.meshes.new("Cut crystal facets")
    mesh.from_pydata(vertices, [], faces)
    o = bpy.data.objects.new("Faceted ruby" if ruby else "Brilliant diamond", mesh)
    bpy.context.collection.objects.link(o)
    for m in mats:
        o.data.materials.append(m)
    for i, face in enumerate(o.data.polygons):
        face.material_index = i % len(mats)
    bezel = tube(
        [(x, y, 0.09) for x, y in outline + [outline[0]]],
        0.035,
        GOLD if ruby else SILVER,
    )
    for point in bezel.data.splines[0].bezier_points:
        point.handle_left_type = point.handle_right_type = "VECTOR"
    o.rotation_euler = (0.10, -0.10, -0.06)
    bezel.rotation_euler = o.rotation_euler


def plum():
    sphere((0, -0.10, 0.16), (0.58, 0.69, 0.47), PURPLE)
    tube([(0.01, 0.51, 0.15), (0.06, 0.72, 0.16), (0.20, 0.79, 0.13)], 0.035, STEM)
    leaf(0.27, 0.60, 0.55, -0.9)
    tube(
        [(0, -0.72, 0.18), (-0.05, -0.22, 0.625), (0, 0.47, 0.24)],
        0.008,
        material("Plum seam", (0.065, 0.008, 0.10), 0, 0.42),
    )


def horseshoe():
    points = [(-0.61, 0.70), (-0.61, -0.05)]
    points += [
        (
            0.61 * math.cos(math.pi + i * math.pi / 24),
            -0.05 + 0.61 * math.sin(math.pi + i * math.pi / 24),
        )
        for i in range(1, 25)
    ]
    points += [(0.61, 0.70), (0.31, 0.70), (0.31, -0.05)]
    points += [
        (0.31 * math.cos(-i * math.pi / 24), -0.05 + 0.31 * math.sin(-i * math.pi / 24))
        for i in range(1, 25)
    ]
    points += [(-0.31, 0.70)]
    polygon(points, GOLD, 0.24, 0.045)
    for x in [-0.46, 0.46]:
        for y in [-0.08, 0.19, 0.46]:
            sphere((x, y, 0.236), (0.044, 0.062, 0.012), DARK)


def star():
    points = [
        (
            math.sin(i * math.pi / 5) * (0.81 if i % 2 == 0 else 0.36),
            math.cos(i * math.pi / 5) * (0.81 if i % 2 == 0 else 0.36),
        )
        for i in range(10)
    ]
    polygon(points, GOLD, 0.23, 0.065)
    sphere((0, 0, 0.25), (0.21, 0.21, 0.075), GOLD)


def orange():
    sphere((0, -0.10, 0.18), (0.62, 0.61, 0.55), ORANGE)
    sphere((0, 0.49, 0.22), (0.075, 0.065, 0.05), STEM)
    leaf(0.31, 0.57, 0.65, -1.0)


def flower():
    for i in range(8):
        a = i * math.tau / 8
        o = sphere(
            (math.sin(a) * 0.42, math.cos(a) * 0.42, 0.12),
            (0.22, 0.40, 0.14),
            PINK if i % 2 else WHITE,
        )
        o.rotation_euler[2] = -a
    sphere((0, 0, 0.30), (0.25, 0.25, 0.17), GOLD)
    for i in range(12):
        a = i * math.tau / 12
        sphere(
            (math.sin(a) * 0.14, math.cos(a) * 0.14, 0.45),
            (0.025, 0.025, 0.025),
            ORANGE,
        )
    leaf(0.48, -0.55, 0.59, -0.8)


def sprig():
    tube([(-0.3, -0.72, 0.05), (0, 0, 0.10), (0.28, 0.72, 0.12)], 0.025, STEM)
    for x, y, a in [
        (-0.25, -0.35, 0.8),
        (0.25, -0.1, -0.8),
        (-0.12, 0.23, 0.8),
        (0.28, 0.46, -0.4),
    ]:
        leaf(x, y, 0.64, a)
    sphere((-0.25, -0.62, 0.23), (0.12, 0.12, 0.12), PINK)


def sun():
    sphere((0, 0, 0.12), (0.53, 0.53, 0.27), GOLD)
    for i in range(12):
        a = i * math.tau / 12

        def pt(r, d):
            return (math.sin(a + d) * r, math.cos(a + d) * r)

        polygon([pt(0.61, -0.13), pt(0.88, 0), pt(0.61, 0.13)], GOLD, 0.13, 0.035)


def shell():
    rings, steps = 20, 64
    vertices = []
    for j in range(rings + 1):
        r = 0.025 + 0.975 * j / rings
        for i in range(steps + 1):
            a = math.pi * i / steps
            vertices.append(
                (
                    r * math.cos(a) * 0.8,
                    r * math.sin(a) * 1.15 - 0.55,
                    0.08
                    + 0.27 * math.sin(math.pi * r)
                    + 0.032 * math.cos(a * 16) * math.sin(math.pi * r),
                )
            )
    faces = []
    for j in range(rings):
        for i in range(steps):
            p = j * (steps + 1) + i
            faces.append((p, p + 1, p + steps + 2, p + steps + 1))
    mesh = bpy.data.meshes.new("Sculpted scallop shell")
    mesh.from_pydata(vertices, [], faces)
    o = bpy.data.objects.new("Pearlescent shell", mesh)
    bpy.context.collection.objects.link(o)
    finish(o, PEARL)
    mod = o.modifiers.new("Shell thickness", "SOLIDIFY")
    mod.thickness = 0.045
    for i in range(17):
        a = math.pi * i / 16
        pts = [
            (
                r * math.cos(a) * 0.8,
                r * math.sin(a) * 1.15 - 0.55,
                0.10 + 0.27 * math.sin(math.pi * r) + 0.032 * math.sin(math.pi * r),
            )
            for r in [0.07, 0.3, 0.55, 0.8, 1]
        ]
        tube(pts, 0.012, WHITE)
    sphere((0, -0.54, 0.15), (0.18, 0.14, 0.10), GOLD)


def pumpkin():
    vertices, faces = [], []
    for j in range(33):
        p = math.pi * j / 32
        for i in range(64):
            a = math.tau * i / 64
            r = math.sin(p) * (0.60 + 0.055 * math.cos(a * 10))
            vertices.append(
                (r * math.cos(a), math.cos(p) * 0.60 - 0.10, r * math.sin(a) + 0.12)
            )
    for j in range(32):
        for i in range(64):
            faces.append(
                (
                    j * 64 + i,
                    j * 64 + (i + 1) % 64,
                    (j + 1) * 64 + (i + 1) % 64,
                    (j + 1) * 64 + i,
                )
            )
    mesh = bpy.data.meshes.new("Lobed pumpkin")
    mesh.from_pydata(vertices, [], faces)
    o = bpy.data.objects.new("Harvest pumpkin", mesh)
    bpy.context.collection.objects.link(o)
    finish(o, ORANGE)
    tube([(0, 0.45, 0.13), (0.03, 0.69, 0.15), (0.17, 0.75, 0.13)], 0.075, STEM)
    leaf(0.33, 0.58, 0.56, -1.0)


def maple_leaf():
    points = [
        (0, 0.86),
        (0.17, 0.45),
        (0.45, 0.65),
        (0.41, 0.28),
        (0.81, 0.32),
        (0.54, -0.02),
        (0.69, -0.21),
        (0.22, -0.30),
        (0.08, -0.55),
        (-0.08, -0.55),
        (-0.22, -0.30),
        (-0.69, -0.21),
        (-0.54, -0.02),
        (-0.81, 0.32),
        (-0.41, 0.28),
        (-0.45, 0.65),
        (-0.17, 0.45),
    ]
    maple = material("Autumn maple enamel", (0.64, 0.085, 0.012), 0.12, 0.27, 0.45)
    polygon(points, maple, 0.085, 0.035, 0.12)
    tube([(0, -0.78, 0.17), (0, -0.2, 0.20), (0, 0.71, 0.20)], 0.018, GOLD)
    for x, y in [
        (0.60, 0.23),
        (-0.60, 0.23),
        (0.40, 0.51),
        (-0.40, 0.51),
        (0.48, -0.18),
        (-0.48, -0.18),
    ]:
        tube([(0, -0.18, 0.20), (x * 0.6, y * 0.6, 0.20), (x, y, 0.20)], 0.009, GOLD)


def acorn():
    brown = material("Acorn mahogany", (0.25, 0.075, 0.018), 0.02, 0.31, 0.35)
    cap = material("Textured acorn cup", (0.13, 0.055, 0.016), 0.03, 0.48)
    noise(cap, 38, 0.7)
    sphere((0, -0.23, 0.13), (0.47, 0.61, 0.42), brown)
    sphere((0, 0.22, 0.11), (0.55, 0.32, 0.46), cap)
    torus((0, 0.09, 0.11), 0.48, 0.035, GOLD, (math.pi / 2, 0, 0))
    tube([(0, 0.44, 0.13), (0.03, 0.68, 0.13), (0.16, 0.78, 0.12)], 0.055, STEM)


def snowflake():
    for i in range(6):
        a = i * math.tau / 6

        def point(r, angle, z=0.14):
            return (math.sin(angle) * r, math.cos(angle) * r, z)

        tube([point(0.03, a), point(0.85, a)], 0.035, SILVER)
        for r in [0.35, 0.60]:
            start = Vector(point(r, a))
            for sign in [-1, 1]:
                end = start + Vector(point(0.23, a + sign * 0.80, 0))
                tube([start, end], 0.025, SILVER)
        sphere(point(0.85, a), (0.058, 0.058, 0.04), WHITE)
    sphere((0, 0, 0.19), (0.14, 0.14, 0.07), WHITE)


def ornament():
    sphere((0, -0.13, 0.12), (0.62, 0.64, 0.55), RED)
    polygon(
        [(-0.15, 0.47), (0.15, 0.47), (0.15, 0.63), (-0.15, 0.63)],
        GOLD,
        0.18,
        0.025,
        0.12,
    )
    torus((0, 0.76, 0.12), 0.11, 0.026, GOLD)
    for y in [-0.40, -0.15, 0.10]:
        r = math.sqrt(max(0.01, 1 - ((y + 0.13) / 0.64) ** 2))
        tube(
            [(-0.54 * r, y, 0.35), (0, y + 0.025, 0.675), (0.54 * r, y, 0.35)],
            0.017,
            GOLD,
        )


def gift():
    polygon(
        [(-0.60, -0.56), (0.60, -0.56), (0.60, 0.46), (-0.60, 0.46)],
        RED,
        0.44,
        0.075,
        0.06,
    )
    polygon(
        [(-0.10, -0.56), (0.10, -0.56), (0.10, 0.49), (-0.10, 0.49)],
        GOLD,
        0.025,
        0.012,
        0.30,
    )
    polygon(
        [(-0.61, -0.08), (0.61, -0.08), (0.61, 0.10), (-0.61, 0.10)],
        GOLD,
        0.025,
        0.012,
        0.30,
    )
    for sign in [-1, 1]:
        tube(
            [
                (0, 0.48, 0.29),
                (sign * 0.27, 0.78, 0.26),
                (sign * 0.43, 0.58, 0.25),
                (0, 0.48, 0.29),
            ],
            0.055,
            GOLD,
        )
    sphere((0, 0.49, 0.31), (0.10, 0.08, 0.07), GOLD)


def holly():
    for x, y, a in [(-0.38, 0.31, -0.85), (0.39, 0.31, 0.85), (0, -0.39, 0)]:
        leaf(x, y, 0.95, a, toothed=True)
    for x, y in [(-0.16, 0.02), (0.17, 0.03), (0, -0.20)]:
        sphere((x, y, 0.38), (0.19, 0.20, 0.18), RED)


def tulip():
    tube([(0, -0.78, 0.1), (0.03, -0.3, 0.12), (0, 0.22, 0.13)], 0.038, GREEN)
    leaf(-0.20, -0.39, 0.72, 0.55)
    leaf(0.22, -0.18, 0.66, -0.55)
    for x, y, z in [(-0.22, 0.30, 0.13), (0.22, 0.30, 0.13), (0, 0.31, 0.27)]:
        sphere((x, y, z), (0.25, 0.46, 0.17), PINK)


def butterfly():
    blue = material("Butterfly turquoise enamel", (0.01, 0.31, 0.43), 0.17, 0.20, 0.65)
    for sign in [-1, 1]:
        o = sphere((sign * 0.37, 0.24, 0.10), (0.38, 0.49, 0.14), blue)
        o.rotation_euler[2] = -sign * 0.35
        o = sphere((sign * 0.32, -0.33, 0.11), (0.31, 0.32, 0.13), PINK)
        o.rotation_euler[2] = sign * 0.2
        sphere((sign * 0.43, 0.29, 0.255), (0.14, 0.19, 0.025), GOLD)
        sphere((sign * 0.33, -0.32, 0.25), (0.10, 0.13, 0.025), GOLD)
    sphere((0, -0.02, 0.24), (0.085, 0.51, 0.10), GOLD)
    sphere((0, 0.48, 0.23), (0.11, 0.12, 0.09), STEM)
    for sign in [-1, 1]:
        tube(
            [(0, 0.51, 0.23), (sign * 0.10, 0.70, 0.22), (sign * 0.22, 0.73, 0.21)],
            0.014,
            GOLD,
        )


def blossom():
    for i in range(5):
        a = math.tau * i / 5
        o = sphere(
            (math.sin(a) * 0.38, math.cos(a) * 0.38, 0.12), (0.30, 0.39, 0.13), PINK
        )
        o.rotation_euler[2] = -a
    sphere((0, 0, 0.26), (0.17, 0.17, 0.08), WHITE)
    for i in range(10):
        a = math.tau * i / 10
        tube(
            [(0, 0, 0.30), (math.sin(a) * 0.21, math.cos(a) * 0.21, 0.37)], 0.009, GOLD
        )
        sphere(
            (math.sin(a) * 0.21, math.cos(a) * 0.21, 0.37), (0.026, 0.026, 0.026), GOLD
        )


def citrus():
    sphere((0, 0, 0.08), (0.73, 0.73, 0.13), ORANGE)
    pith = material("Fresh citrus pith", (0.95, 0.81, 0.48), 0, 0.42)
    sphere((0, 0, 0.20), (0.66, 0.66, 0.055), pith)
    for i in range(10):
        a = i * math.tau / 10
        points = [
            (math.cos(a + d) * r, math.sin(a + d) * r)
            for r, d in [
                (0.09, 0.08),
                (0.60, 0.06),
                (0.62, 0.29),
                (0.60, 0.55),
                (0.09, 0.53),
            ]
        ]
        polygon(points, ORANGE, 0.05, 0.018, 0.26)
    sphere((0, 0, 0.30), (0.075, 0.075, 0.025), pith)
    leaf(0.65, 0.64, 0.40, -0.7)


def palm():
    tube(
        [
            (-0.14, -0.80, 0.10),
            (-0.03, -0.3, 0.11),
            (0.12, 0.24, 0.13),
            (0.12, 0.42, 0.13),
        ],
        0.085,
        STEM,
    )
    for x, y, a in [
        (-0.48, 0.30, 1.1),
        (0.51, 0.30, -1.1),
        (-0.40, 0.57, 0.8),
        (0.43, 0.59, -0.8),
        (0, 0.70, 0),
    ]:
        leaf(x, y, 0.78, a, toothed=True)
    for x, y in [(-0.03, 0.31), (0.20, 0.28), (0.09, 0.16)]:
        sphere((x, y, 0.23), (0.11, 0.12, 0.10), STEM)


def starfish():
    coral = material("Coral starfish", (0.72, 0.12, 0.035), 0.02, 0.39, 0.1)
    noise(coral, 55, 0.36)
    points = [
        (
            math.sin(i * math.pi / 5) * (0.83 if i % 2 == 0 else 0.37),
            math.cos(i * math.pi / 5) * (0.83 if i % 2 == 0 else 0.37),
        )
        for i in range(10)
    ]
    polygon(points, coral, 0.22, 0.13, 0.10)
    for arm in range(5):
        a = arm * math.tau / 5
        for r in [0.12, 0.26, 0.4, 0.54, 0.67]:
            sphere(
                (math.sin(a) * r, math.cos(a) * r, 0.23), (0.023, 0.023, 0.017), PEARL
            )


def mushroom():
    sphere((0, -0.32, 0.08), (0.23, 0.51, 0.23), PEARL)
    sphere((0, 0.22, 0.10), (0.70, 0.40, 0.40), RED)
    for x, y, z, scale in [
        (-0.35, 0.25, 0.41, 0.085),
        (0.17, 0.40, 0.44, 0.10),
        (0.42, 0.15, 0.42, 0.07),
        (-0.05, 0.13, 0.50, 0.075),
    ]:
        sphere((x, y, z), (scale, scale, 0.025), WHITE)
    leaf(0.43, -0.54, 0.47, -0.9)


def pear():
    yellow = material("Golden pear skin", (0.59, 0.39, 0.025), 0.02, 0.34, 0.2)
    noise(yellow, 100, 0.16)
    profile = [
        (-0.74, 0.02),
        (-0.66, 0.29),
        (-0.42, 0.51),
        (-0.10, 0.47),
        (0.23, 0.29),
        (0.54, 0.18),
        (0.65, 0.035),
    ]
    vertices = [
        (r * math.cos(i * math.tau / 64), y, 0.10 + r * math.sin(i * math.tau / 64))
        for y, r in profile
        for i in range(64)
    ]
    faces = [
        (
            j * 64 + i,
            j * 64 + (i + 1) % 64,
            (j + 1) * 64 + (i + 1) % 64,
            (j + 1) * 64 + i,
        )
        for j in range(len(profile) - 1)
        for i in range(64)
    ]
    mesh = bpy.data.meshes.new("Pear silhouette")
    mesh.from_pydata(vertices, [], faces)
    o = bpy.data.objects.new("Golden pear", mesh)
    bpy.context.collection.objects.link(o)
    finish(o, yellow)
    mod = o.modifiers.new("Smooth fruit profile", "SUBSURF")
    mod.levels = 2
    tube([(0, 0.61, 0.10), (0.06, 0.77, 0.12), (0.19, 0.82, 0.11)], 0.035, STEM)
    leaf(0.32, 0.61, 0.51, -0.9)


def mitten():
    wool = material("Red knitted wool", (0.46, 0.008, 0.025), 0, 0.65, 0)
    noise(wool, 80, 0.60)
    polygon(
        [
            (-0.35, -0.65),
            (0.37, -0.65),
            (0.45, -0.1),
            (0.73, 0.05),
            (0.77, 0.30),
            (0.61, 0.42),
            (0.38, 0.22),
            (0.35, 0.60),
            (0.13, 0.76),
            (-0.19, 0.72),
            (-0.40, 0.51),
        ],
        wool,
        0.28,
        0.10,
        0.10,
    )
    polygon(
        [(-0.38, -0.70), (0.40, -0.70), (0.40, -0.43), (-0.38, -0.43)],
        WHITE,
        0.32,
        0.055,
        0.10,
    )
    for x in [-0.27, -0.16, -0.05, 0.06, 0.17, 0.28]:
        tube([(x, -0.65, 0.29), (x, -0.47, 0.29)], 0.013, SILVER)


def traditional_bar(count=1):
    spacing = 0.52 if count == 2 else 0.44
    height = 0.62 if count == 1 else 0.43 if count == 2 else 0.36
    for i in range(count):
        y = (i - (count - 1) / 2) * spacing
        polygon(
            [
                (-0.83, y - height / 2),
                (0.83, y - height / 2),
                (0.83, y + height / 2),
                (-0.83, y + height / 2),
            ],
            GOLD,
            0.12,
            0.045,
            0.08,
        )
        polygon(
            [
                (-0.77, y - height / 2 + 0.045),
                (0.77, y - height / 2 + 0.045),
                (0.77, y + height / 2 - 0.045),
                (-0.77, y + height / 2 - 0.045),
            ],
            DARK,
            0.13,
            0.022,
            0.11,
        )
        curve = bpy.data.curves.new("Embossed BAR lettering", "FONT")
        curve.body = "BAR"
        curve.align_x = "CENTER"
        curve.align_y = "CENTER"
        curve.size = height * 0.80
        curve.extrude = 0.016
        curve.bevel_depth = 0.006
        curve.bevel_resolution = 3
        obj = bpy.data.objects.new("Traditional BAR", curve)
        bpy.context.collection.objects.link(obj)
        obj.location = (0, y, 0.205)
        obj.data.materials.append(WHITE)


def traditional_seven():
    points = [
        (-0.69, 0.76),
        (0.66, 0.76),
        (0.66, 0.45),
        (-0.08, -0.77),
        (-0.53, -0.77),
        (0.19, 0.37),
        (-0.69, 0.37),
    ]
    polygon([(x * 1.07, y * 1.07) for x, y in points], GOLD, 0.18, 0.05, 0.06)
    polygon(points, RED, 0.21, 0.035, 0.12)


SYMBOLS = dict(
    bar=traditional_bar,
    double_bar=lambda: traditional_bar(2),
    triple_bar=lambda: traditional_bar(3),
    seven=traditional_seven,
    cherries=cherries,
    bell=bell,
    diamond=jewel,
    ruby=lambda: jewel(True),
    plum=plum,
    horseshoe=horseshoe,
    star=star,
    orange=orange,
    flower=flower,
    sprig=sprig,
    sun=sun,
    shell=shell,
    pumpkin=pumpkin,
    maple=maple_leaf,
    acorn=acorn,
    snowflake=snowflake,
    ornament=ornament,
    gift=gift,
    holly=holly,
    tulip=tulip,
    butterfly=butterfly,
    blossom=blossom,
    citrus=citrus,
    palm=palm,
    starfish=starfish,
    mushroom=mushroom,
    pear=pear,
    mitten=mitten,
)
ATLASES = {
    "classic": [
        "cherries",
        "bell",
        "bar",
        "double_bar",
        "triple_bar",
        "seven",
        "horseshoe",
        "diamond",
    ],
    "atrium": [
        "cherries",
        "bell",
        "diamond",
        "ruby",
        "plum",
        "horseshoe",
        "star",
        "orange",
    ],
    "spring": [
        "flower",
        "sprig",
        "tulip",
        "butterfly",
        "blossom",
        "cherries",
        "diamond",
        "bell",
    ],
    "summer": [
        "sun",
        "shell",
        "citrus",
        "palm",
        "starfish",
        "cherries",
        "orange",
        "diamond",
    ],
    "autumn": ["pumpkin", "maple", "acorn", "mushroom", "pear", "bell", "ruby", "plum"],
    "winter": [
        "snowflake",
        "ornament",
        "gift",
        "holly",
        "mitten",
        "diamond",
        "bell",
        "star",
    ],
}


def setup():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = int(os.environ.get("REEL_SYMBOL_SAMPLES", "32"))
    scene.cycles.use_denoising = True
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    world = bpy.data.worlds.new("Soft studio reflection")
    world.use_nodes = True
    env = world.node_tree.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(str(HDR), check_existing=True)
    background = world.node_tree.nodes.get("Background")
    background.inputs["Strength"].default_value = 0.45
    world.node_tree.links.new(env.outputs["Color"], background.inputs["Color"])
    scene.world = world
    for location, energy, size in [((-3, 2, 5), 420, 4), ((3, -1, 4), 280, 3)]:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.rotation_euler = (
            (Vector((0, 0, 0.1)) - light.location).to_track_quat("-Z", "Y").to_euler()
        )
    bpy.ops.object.camera_add(location=(0, -0.50, 7))
    camera = bpy.context.object
    camera.rotation_euler = (
        (Vector((0, 0, 0)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    )
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 2.28
    scene.camera = camera
    paper = material("Warm ivory reel paper", (0.90, 0.855, 0.735), 0, 0.58, 0)
    noise(paper, 180, 0.07)
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.50))
    finish(bpy.context.object, paper)
    # Thin metallic registration border leaves generous paper around every symbol.
    border = tube(
        [
            (-1.02, -0.99, -0.48),
            (-1.02, 0.99, -0.48),
            (1.02, 0.99, -0.48),
            (1.02, -0.99, -0.48),
            (-1.02, -0.99, -0.48),
        ],
        0.003,
        GOLD,
    )
    for point in border.data.splines[0].bezier_points:
        point.handle_left_type = point.handle_right_type = "VECTOR"
    return set(bpy.data.objects)


base = setup()
for name, build in SYMBOLS.items():
    selected = os.environ.get("REEL_SYMBOL_ONLY", "").split(",")
    if selected != [""] and name not in selected:
        continue
    path = WORK / (name + ".png")
    if not path.exists() or os.environ.get("REEL_REBUILD_SYMBOLS") == "1":
        for obj in list(bpy.data.objects):
            if obj not in base:
                bpy.data.objects.remove(obj, do_unlink=True)
        build()
        import bmesh

        for obj in bpy.data.objects:
            if obj not in base and obj.type == "MESH":
                mesh = bmesh.new()
                mesh.from_mesh(obj.data)
                bmesh.ops.recalc_face_normals(mesh, faces=list(mesh.faces))
                mesh.to_mesh(obj.data)
                mesh.free()
        bpy.context.scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        print("SYMBOL COMPLETE: " + name, flush=True)

# Pillow only assembles genuine Blender renders; it never draws or substitutes symbols.
compose = """from PIL import Image
from pathlib import Path
import json,sys
root=Path(sys.argv[1]); atlases=json.loads(sys.argv[2])
for season,names in atlases.items():
 atlas=Image.new('RGB',(512,4096))
 for index,name in enumerate(names):
  cell=Image.open(root/'build/symbol-renders'/f'{name}.png').convert('RGB')
  assert cell.size==(512,512)
  atlas.paste(cell,(0,(7-index)*512))
 destination=root/'assets/textures'/f'symbols_{season}.png'
 temporary=destination.with_name(destination.stem+'.pending.png')
 atlas.save(temporary,optimize=True)
 temporary.replace(destination)
"""
import json

python = shutil.which("python3")
if not python:
    raise RuntimeError("Host Python3 with Pillow is required to assemble atlas PNGs")
subprocess.run([python, "-c", compose, str(ROOT), json.dumps(ATLASES)], check=True)
(OUT / "symbols.json").write_text(
    json.dumps(
        {
            "width": 512,
            "height": 4096,
            "cell_size": 512,
            "index_zero": "bottom, UV v=0..0.125",
            "symbols": ATLASES,
            "art": "Original procedural 3D symbol models rendered with Blender Cycles; Traditional BAR lettering and 7 are intentional game symbols; no logos or watermarks.",
        },
        indent=2,
    )
    + "\n"
)
print("ALL SYMBOL ATLASES COMPLETE", flush=True)
