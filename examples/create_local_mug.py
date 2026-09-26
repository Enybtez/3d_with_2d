"""Render a locally made mug image for the offline model run."""

import math
import sys

import bpy
from mathutils import Vector


output = sys.argv[-1]
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

profile = [
    (0.0, 0.10), (0.68, 0.10), (0.78, 0.16), (0.82, 0.28),
    (0.89, 1.85), (0.90, 1.96), (0.87, 2.01), (0.78, 2.01),
    (0.75, 1.93), (0.72, 0.37), (0.0, 0.37),
]
segments = 96
vertices = [
    (radius * math.cos(2 * math.pi * i / segments),
     radius * math.sin(2 * math.pi * i / segments), height)
    for radius, height in profile for i in range(segments)
]
faces = [
    (j * segments + i, j * segments + (i + 1) % segments,
     (j + 1) * segments + (i + 1) % segments, (j + 1) * segments + i)
    for j in range(len(profile) - 1) for i in range(segments)
]
mesh = bpy.data.meshes.new("mug-body")
mesh.from_pydata(vertices, [], faces)
mesh.update()
body = bpy.data.objects.new("red ceramic mug", mesh)
bpy.context.collection.objects.link(body)
for polygon in mesh.polygons:
    polygon.use_smooth = True

red = bpy.data.materials.new("glazed red ceramic")
red.diffuse_color = (0.72, 0.018, 0.025, 1)
red.use_nodes = True
shader = red.node_tree.nodes.get("Principled BSDF")
shader.inputs["Base Color"].default_value = red.diffuse_color
shader.inputs["Roughness"].default_value = 0.23
body.data.materials.append(red)

curve = bpy.data.curves.new("handle path", "CURVE")
curve.dimensions = "3D"
curve.resolution_u = 32
curve.bevel_depth = 0.115
curve.bevel_resolution = 5
spline = curve.splines.new("BEZIER")
points = [
    (0.85, 0.0, 1.70), (1.34, 0.0, 1.73), (1.90, 0.0, 1.56),
    (2.12, 0.0, 1.20), (2.04, 0.0, 0.82), (1.75, 0.0, 0.61),
    (0.84, 0.0, 0.67),
]
spline.bezier_points.add(len(points) - 1)
for point, coordinate in zip(spline.bezier_points, points):
    point.co = coordinate
    point.handle_left_type = "AUTO"
    point.handle_right_type = "AUTO"
handle = bpy.data.objects.new("mug handle", curve)
bpy.context.collection.objects.link(handle)
handle.data.materials.append(red)

def area_light(name, location, energy, size):
    lamp = bpy.data.lights.new(name, "AREA")
    lamp.energy = energy
    lamp.shape = "DISK"
    lamp.size = size
    obj = bpy.data.objects.new(name, lamp)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector((0.4, 0, 1.0)) - obj.location).to_track_quat("-Z", "Y").to_euler()


area_light("large softbox", (1, -4, 5), 650, 5)
area_light("side light", (-3, 2, 4), 420, 3)
area_light("rim light", (3, 3, 3), 480, 2)

camera = bpy.data.cameras.new("camera")
camera.type = "ORTHO"
camera.ortho_scale = 3.7
camera_obj = bpy.data.objects.new("camera", camera)
bpy.context.collection.objects.link(camera_obj)
camera_obj.location = (4, -6, 3.5)
camera_obj.rotation_euler = (Vector((0.55, 0, 1.05)) - camera_obj.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = camera_obj

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 24
scene.view_layers[0].cycles.use_denoising = False
scene.render.film_transparent = True
scene.render.resolution_x = 768
scene.render.resolution_y = 768
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = output
bpy.ops.render.render(write_still=True)
