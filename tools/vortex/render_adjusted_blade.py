import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math
import mathutils
from pathlib import Path

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Vortex\vortex_prepared.fbx")

mesh = bpy.data.objects["cha_vortex_gs_00"]
for side, s_sign in [("L", -1.0), ("R", 1.0)]:
    offset = 11706 if side == "L" else 11706 + 2834
    indices = list(range(offset, offset + 2834))
    pivot = mathutils.Vector((s_sign * 2.571, -0.049, 5.746))
    rot_x = mathutils.Matrix.Rotation(math.radians(12.0), 4, 'X')
    scale_m = mathutils.Matrix.Diagonal((0.75, 0.75, 0.65, 1.0))
    T = mathutils.Matrix.Translation(pivot)
    T_inv = mathutils.Matrix.Translation(-pivot)
    M = T @ rot_x @ scale_m @ T_inv
    for i in indices:
        v = mesh.data.vertices[i]
        v.co = M @ v.co

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1200
scene.render.resolution_y = 1200
if not scene.world:
    scene.world = bpy.data.worlds.new("W")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.15, 0.16, 0.18, 1.0)

cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.data.lens = 45.0
scene.collection.objects.link(cam)
scene.camera = cam

def look_at(obj, pos, target):
    obj.location = mathutils.Vector(pos)
    obj.rotation_euler = (mathutils.Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()

look_at(cam, (0, 16, 5.5), (0, 0, 5.0))
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN'))
sun.data.energy = 3.5
scene.collection.objects.link(sun)
look_at(sun, (5, 12, 10), (0, 0, 5.0))

out_img = Path(r"C:\Users\Xiangli496\AppData\Local\Temp\vortex_blade_adjusted.png")
scene.render.filepath = str(out_img)
bpy.ops.render.render(write_still=True)
print(f"Rendered adjusted blade check: {out_img}")
