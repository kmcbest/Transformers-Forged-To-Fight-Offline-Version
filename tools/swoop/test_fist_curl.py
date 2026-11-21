import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path
from mathutils import Quaternion, Vector, Euler

FBX_SRC = Path("e:/Agent/TFTF-blender/3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

arm = bpy.data.objects.get("Bip001")
mesh = bpy.data.objects.get("Swoop.001")

# Let's inspect the finger bones and their local axes
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')

print("Finger bones in Bip001:")
for pb in arm.pose.bones:
    if "Finger" in pb.name:
        print(f"  {pb.name}: rot_mode={pb.rotation_mode}, parent={pb.parent.name if pb.parent else None}")
