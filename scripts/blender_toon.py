"""Run with Blender: blender --background --python blender_toon.py -- model.glb preview.png"""

import sys

import bpy
from mathutils import Vector


def toon_material(material):
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    principled = next((node for node in nodes if node.type == "BSDF_PRINCIPLED"), None)
    original_color = None
    if principled:
        color_input = principled.inputs["Base Color"]
        if color_input.is_linked:
            original_color = color_input.links[0].from_socket
        color = tuple(color_input.default_value)
    else:
        color = tuple(material.diffuse_color)

    output = next((node for node in nodes if node.type == "OUTPUT_MATERIAL"), None)
    if output is None:
        output = nodes.new("ShaderNodeOutputMaterial")
    diffuse = nodes.new("ShaderNodeBsdfDiffuse")
    light = nodes.new("ShaderNodeShaderToRGB")
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.45, 0.45, 0.55, 1.0)
    middle = ramp.color_ramp.elements.new(0.38)
    middle.color = (0.78, 0.78, 0.84, 1.0)
    highlight = ramp.color_ramp.elements.new(0.72)
    highlight.color = (1.0, 1.0, 1.0, 1.0)
    multiply = nodes.new("ShaderNodeMixRGB")
    multiply.blend_type = "MULTIPLY"
    multiply.inputs[0].default_value = 1.0
    emission = nodes.new("ShaderNodeEmission")
    links.new(diffuse.outputs[0], light.inputs[0])
    links.new(light.outputs[0], ramp.inputs[0])
    links.new(ramp.outputs[0], multiply.inputs[2])
    if original_color is not None:
        links.new(original_color, multiply.inputs[1])
    else:
        multiply.inputs[1].default_value = color
    links.new(multiply.outputs[0], emission.inputs[0])
    links.new(emission.outputs[0], output.inputs["Surface"])


def main(model_path, output_path):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=model_path)
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("GLB 没有网格")

    for obj in meshes:
        if not obj.data.materials:
            obj.data.materials.append(bpy.data.materials.new("toon-default"))
        for material in obj.data.materials:
            toon_material(material)

    corners = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    minimum = Vector(tuple(min(point[i] for point in corners) for i in range(3)))
    maximum = Vector(tuple(max(point[i] for point in corners) for i in range(3)))
    center = (minimum + maximum) / 2
    size = max(maximum - minimum)
    if size <= 0:
        raise RuntimeError("GLB 网格尺寸无效")

    camera_data = bpy.data.cameras.new("toon-camera")
    camera = bpy.data.objects.new("toon-camera", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = center + Vector((1.8, -3.2, 2.0)).normalized() * size * 3
    direction = center - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = size * 1.65
    bpy.context.scene.camera = camera

    light_data = bpy.data.lights.new("toon-key", "AREA")
    light = bpy.data.objects.new("toon-key", light_data)
    bpy.context.scene.collection.objects.link(light)
    light.location = center + Vector((-2, -3, 5)).normalized() * size * 3
    light.rotation_euler = (center - light.location).to_track_quat("-Z", "Y").to_euler()
    light_data.energy = 800
    light_data.shape = "DISK"
    light_data.size = size * 3

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 768
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = True
    scene.render.use_freestyle = True
    bpy.context.view_layer.use_freestyle = True
    lineset = bpy.context.view_layer.freestyle_settings.linesets[0]
    lineset.linestyle.color = (0.07, 0.05, 0.11)
    lineset.linestyle.thickness = 2.5
    scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1 :]
    if len(args) != 2:
        raise SystemExit("需要 model.glb 和 preview.png")
    main(*args)
