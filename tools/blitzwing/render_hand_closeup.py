import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'stderr'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math
from pathlib import Path

SRC = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Blitzwing_EW\01_source\H_shandian_G1_M_LOD.fbx")
OUT_IMG = Path(r"E:\Agent\TFTF-blender\tools\blitzwing\renders\hand_source_closeup.png")
OUT_IMG.parent.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SRC))

mesh = bpy.data.objects['H_shandian_G1_M_Lod']
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]

# Focus camera on Left Hand
# In source FBX, LeftHand is around (1.7, 4.4, -0.05)
cam_data = bpy.data.cameras.new("Cam")
cam_obj = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

cam_obj.location = (2.6, 3.8, 0.4)
# Look at Left Hand (1.7, 4.4, 0.1)
cam_obj.rotation_euler = (math.radians(65), 0, math.radians(130))

# Add sun light
light_data = bpy.data.lights.new("Sun", 'SUN')
light_obj = bpy.data.objects.new("Sun", light_data)
bpy.context.scene.collection.objects.link(light_obj)
light_obj.location = (5, 2, 5)
light_data.energy = 3.0

bpy.context.scene.render.resolution_x = 800
bpy.context.scene.render.resolution_y = 800
bpy.context.scene.render.filepath = str(OUT_IMG)
bpy.ops.render.render(write_still=True)
print(f"Saved hand closeup to {OUT_IMG}")
