import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math
from pathlib import Path

ROBOT_BLEND = Path(r"E:\Agent\TFTF-blender\3rd-party-models\vortex\robot\vortex_robot.blend")
OUT_DIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\vortex")

bpy.ops.wm.open_mainfile(filepath=str(ROBOT_BLEND))

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.use_bloom = True
scene.render.resolution_x = 800
scene.render.resolution_y = 800

# World
world = bpy.data.worlds.new("World4V")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.05, 0.06, 1.0)
scene.world = world

# Sun Light
sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 4.0
sun_obj = bpy.data.objects.new(name="Sun", object_data=sun_data)
sun_obj.rotation_euler = (math.radians(45), math.radians(20), math.radians(-30))
bpy.context.collection.objects.link(sun_obj)

# Camera
cam_data = bpy.data.cameras.new(name="Cam")
cam_data.lens = 45
cam_obj = bpy.data.objects.new(name="Cam", object_data=cam_data)
bpy.context.collection.objects.link(cam_obj)
scene.camera = cam_obj

views = {
    "front_minus_y": ((0, -9.0, 2.8), (math.radians(90), 0, 0)),
    "front_plus_y": ((0, 9.0, 2.8), (math.radians(90), 0, math.radians(180))),
    "side_minus_x": ((-9.0, 0, 2.8), (math.radians(90), 0, math.radians(-90))),
    "side_plus_x": ((9.0, 0, 2.8), (math.radians(90), 0, math.radians(90))),
}

for vname, (loc, rot) in views.items():
    cam_obj.location = loc
    cam_obj.rotation_euler = rot
    out_p = OUT_DIR / f"test_{vname}.png"
    scene.render.filepath = str(out_p)
    bpy.ops.render.render(write_still=True)
    print(f"Rendered {vname} to {out_p}")
