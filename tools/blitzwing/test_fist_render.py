import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import os
from pathlib import Path
import math
import bpy
from mathutils import Vector, Matrix, Quaternion, Euler

ROOT = Path("E:/Agent/TFTF-blender")
OUT_IMG = ROOT / "renders/blitzwing/test_hand_fist.png"
OUT_IMG.parent.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)

# Import source model
fbx_path = ROOT / "3rd-party-models/Blitzwing_EW/01_source/H_shandian_G1_M_LOD.fbx"
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

arm_obj = None
mesh_obj = None
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        arm_obj = obj
    elif obj.type == 'MESH':
        mesh_obj = obj

# Det=+1 alignment: Rz(-90 deg)
arm_obj.rotation_euler = (0, 0, math.radians(-90))
mesh_obj.rotation_euler = (0, 0, math.radians(-90))
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.transform_apply(rotation=True)

# Ground Z=0
min_z = min(v.co.z for v in mesh_obj.data.vertices)
mesh_obj.location.z -= min_z
arm_obj.location.z -= min_z
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Scale
SCALE = 149.1728
mesh_obj.scale = (SCALE, SCALE, SCALE)
arm_obj.scale = (SCALE, SCALE, SCALE)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Attach Armature modifier
mesh_obj.modifiers.clear()
mesh_obj.parent = arm_obj
arm_mod = mesh_obj.modifiers.new("Armature", "ARMATURE")
arm_mod.object = arm_obj

# Pose mode
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='POSE')

# Let's inspect the local axes of Bip001 L Finger1 in pose mode
pb_f1 = arm_obj.pose.bones["Bip001 L Finger1"]
pb_f2 = arm_obj.pose.bones["Bip001 L Finger2"]
pb_f0 = arm_obj.pose.bones["Bip001 L Finger0"]

print("Pose bone L Finger1 rotation mode:", pb_f1.rotation_mode)
print("Pose bone L Finger1 bone matrix_local:", pb_f1.bone.matrix_local)

# Let's test rotating Bip001 L Finger1 around its local axes
# In Blender, local rotation on a pose bone with Euler or Quaternion:
# If rotation_mode = 'XYZ', pb.rotation_euler = (x, y, z) rotates around bone local axes.
# Let's see what happens if we curl Finger1..4 and Finger0
