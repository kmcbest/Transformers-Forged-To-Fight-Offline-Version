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

out_img = Path(r"C:\Users\Xiangli496\AppData\Local\Temp\vortex_blade_check.png")
scene.render.filepath = str(out_img)
bpy.ops.render.render(write_still=True)
print(f"Rendered blade check: {out_img}")
