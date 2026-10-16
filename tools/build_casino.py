"""Create the casino room and bake its static lighting for an inexpensive TV scene."""

import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]


def material(name, color, roughness=0.5, emission=0):
    result = bpy.data.materials.new(name)
    result.use_nodes = True
    result["casino_albedo"] = [*color, 1]
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Emission Color"].default_value = (*color, 1)
    shader.inputs["Emission Strength"].default_value = emission
    return result


def box(name, location, dimensions, surface, bevel=0.015, subdivisions=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(surface)
    if subdivisions:
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.subdivide(number_cuts=subdivisions)
        bpy.ops.object.mode_set(mode="OBJECT")
    if bevel:
        modifier = obj.modifiers.new("Soft manufactured edges", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    return obj


def cylinder(name, location, radius, depth, surface, vertices=24):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=depth, location=location
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(surface)
    for face in obj.data.polygons:
        face.use_smooth = len(face.vertices) == 4
    return obj


def area(location, target, energy, color, size):
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.data.energy = energy
    light.data.color = color
    light.data.size = size
    light.rotation_euler = (
        (Vector(target) - light.location).to_track_quat("-Z", "Y").to_euler()
    )


def build():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    graphite = material("Graphite cabinet", (0.025, 0.029, 0.034), 0.24)
    bronze = material("Brushed champagne bronze", (0.32, 0.21, 0.095), 0.3)
    black = material("Recessed black glass", (0.008, 0.012, 0.018), 0.17)
    leather = material("Oxblood leather", (0.105, 0.018, 0.025), 0.4)
    wall = material("Warm woven wall panels", (0.13, 0.105, 0.075), 0.9)
    ceiling = material("Recessed charcoal ceiling", (0.045, 0.039, 0.035), 0.9)
    gold_light = material("Warm cove glow", (1.0, 0.59, 0.20), 0.5, 2)
    screen = material("Original reel displays", (1, 1, 1), 0.6, 0.4)
    texture = screen.node_tree.nodes.new("ShaderNodeTexImage")
    texture.image = bpy.data.images.load(
        str(ROOT / "assets/textures/casino_screen.png")
    )
    shader = screen.node_tree.nodes.get("Principled BSDF")
    screen.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    screen.node_tree.links.new(
        texture.outputs["Color"], shader.inputs["Emission Color"]
    )
    carpet = material("Woven casino carpet", (1, 1, 1), 0.95)
    texture = carpet.node_tree.nodes.new("ShaderNodeTexImage")
    texture.image = bpy.data.images.load(
        str(ROOT / "assets/materials/casino_carpet.png")
    )
    carpet.node_tree.links.new(
        texture.outputs["Color"],
        carpet.node_tree.nodes.get("Principled BSDF").inputs["Base Color"],
    )
    floor = box("Carpet", (0, 2, -0.035), (11, 14, 0.06), carpet, 0, 48)
    for loop in floor.data.loops:
        co = floor.data.vertices[loop.vertex_index].co
        floor.data.uv_layers.active.data[loop.index].uv = (co.x / 1.8, co.y / 1.8)
    box("Ceiling", (0, 2.5, 3.25), (11, 13, 0.12), ceiling, 0, 14)
    box("Rear wall", (0, 7.5, 1.6), (11, 0.15, 3.2), wall, 0, 20)
    for side in (-1, 1):
        box("Outer wall", (side * 5.3, 2, 1.6), (0.12, 12, 3.2), wall, 0, 16)
        for y in (-1, 1, 3, 5, 7):
            box("Wall pilaster", (side * 5.16, y, 1.5), (0.12, 0.15, 3), bronze)
        for row in range(5):
            x, y = side * (1.35 + row * 0.13), 0.25 + row * 1.32
            body = box(
                "Slot cabinet", (x, y, 0.86), (0.73, 0.64, 1.63), graphite, 0.045
            )
            body.rotation_euler.z = side * -0.07
            box("Lower inset", (x, y - 0.335, 0.37), (0.58, 0.035, 0.51), black)
            box(
                "Screen bronze reveal",
                (x, y - 0.343, 1.13),
                (0.67, 0.055, 0.94),
                bronze,
            )
            display = box(
                "Reel screen", (x, y - 0.378, 1.13), (0.56, 0.018, 0.81), screen, 0
            )
            for face in display.data.polygons:
                for index in face.loop_indices:
                    co = display.data.vertices[
                        display.data.loops[index].vertex_index
                    ].co
                    display.data.uv_layers.active.data[index].uv = (
                        co.x / 0.56 + 0.5,
                        co.z / 0.81 + 0.5,
                    )
            box("Button deck", (x, y - 0.43, 0.61), (0.69, 0.29, 0.09), graphite)
            for button in range(4):
                cylinder(
                    "Illuminated control",
                    (x - 0.22 + button * 0.145, y - 0.48, 0.665),
                    0.028,
                    0.012,
                    gold_light,
                    12,
                )
            box("Crown", (x, y - 0.32, 1.78), (0.72, 0.06, 0.21), black)
            box(
                "Crown light",
                (x, y - 0.356, 1.78),
                (0.63, 0.018, 0.10),
                gold_light,
                0.01,
            )
            for offset in (-0.355, 0.355):
                box(
                    "Cabinet edge light",
                    (x + offset, y - 0.36, 1.1),
                    (0.012, 0.015, 1.29),
                    gold_light,
                    0.004,
                )
            cylinder("Chair pedestal", (x, y - 0.95, 0.05), 0.28, 0.055, bronze)
            cylinder("Chair stem", (x, y - 0.95, 0.30), 0.045, 0.49, graphite)
            cylinder("Cushioned seat", (x, y - 0.95, 0.57), 0.24, 0.115, leather)
            box(
                "Curved chair back",
                (x, y - 1.14, 0.84),
                (0.43, 0.10, 0.46),
                leather,
                0.045,
            )
            area((x, y - 0.30, 1.40), (x, y - 1, 0), 16, (0.52, 0.65, 1), 0.6)
        for y in (0.4, 3.0, 5.8):
            cylinder("Fluted room column", (side * 3.6, y, 1.5), 0.19, 3.0, bronze, 32)
            cylinder("Column foot", (side * 3.6, y, 0.10), 0.24, 0.16, graphite)
            cylinder("Column capital", (side * 3.6, y, 2.93), 0.26, 0.13, bronze)
            box(
                "Ceiling cove",
                (side * 2.6, y, 3.05),
                (3.5, 0.028, 0.025),
                gold_light,
                0,
            )
    for y in (-0.4, 2.5, 5.6):
        cylinder("Chandelier stem", (0, y, 2.91), 0.035, 0.55, bronze)
        for radius, height in ((0.56, 2.74), (0.40, 2.56), (0.24, 2.39)):
            cylinder(
                "Chandelier bronze tier", (0, y, height), radius, 0.025, bronze, 48
            )
            for i in range(20):
                angle = i * math.tau / 20
                cylinder(
                    "Warm crystal drop",
                    (
                        math.cos(angle) * radius,
                        y + math.sin(angle) * radius,
                        height - 0.075,
                    ),
                    0.018,
                    0.14,
                    gold_light,
                    6,
                )
        area((0, y, 2.66), (0, y, 0), 180, (1, 0.75, 0.47), 1.5)
    area((0, -2, 2.8), (0, 1, 0), 120, (0.72, 0.79, 1), 3)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 4
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.world.use_nodes = True
    scene.world.node_tree.nodes.get("Background").inputs["Color"].default_value = (
        0.12,
        0.15,
        0.2,
        1,
    )
    scene.world.node_tree.nodes.get("Background").inputs[
        "Strength"
    ].default_value = 0.12
    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
        obj.data.color_attributes.new(
            name="CasinoLight", type="FLOAT_COLOR", domain="CORNER"
        )
    bpy.context.view_layer.objects.active = meshes[0]
    scene.render.bake.target = "VERTEX_COLORS"
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"})
    for surface in [graphite, bronze, black, leather, wall, ceiling, carpet]:
        nodes, links = surface.node_tree.nodes, surface.node_tree.links
        shader = nodes.get("Principled BSDF")
        base = shader.inputs["Base Color"]
        previous = base.links[0].from_socket if base.is_linked else None
        light = nodes.new("ShaderNodeVertexColor")
        light.layer_name = "CasinoLight"
        multiply = nodes.new("ShaderNodeMixRGB")
        multiply.blend_type = "MULTIPLY"
        multiply.inputs[0].default_value = 1
        multiply.inputs[1].default_value = base.default_value
        if previous:
            links.new(previous, multiply.inputs[1])
        links.new(light.outputs["Color"], multiply.inputs[2])
        links.new(multiply.outputs["Color"], base)
    for obj in meshes:
        obj.name = "Casino_" + obj.name
    for surface in bpy.data.materials:
        surface.name = "Casino " + surface.name
    destination = ROOT / "build/casino_environment.glb"
    destination.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(destination),
        export_format="GLB",
        export_lights=False,
        export_cameras=False,
        export_extras=True,
        use_selection=True,
    )
    print("Exported", destination)


if __name__ == "__main__":
    build()
