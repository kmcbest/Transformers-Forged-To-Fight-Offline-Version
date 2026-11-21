import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Matrix, Vector, Euler
import math

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

arm = bpy.data.objects.get("Bip001")
swoop = bpy.data.objects.get("Swoop.001")

# Start from idle01 frame 1
act = bpy.data.actions.get("Bip001|idle01|Base Layer")
if act and arm.animation_data:
    arm.animation_data.action = act
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()

# Clear action to make pose editable or keep pose
# To preserve the evaluated pose as base pose:
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')
# Copy current pose to a new action or bake it
# In pose mode, let's see current rotations of L arm vs R arm
pb_lua = arm.pose.bones.get("Bone_L_UpperArm")
pb_lfa = arm.pose.bones.get("Bone_L_Forearm")
pb_lh  = arm.pose.bones.get("Bone_L_Hand")

pb_rua = arm.pose.bones.get("Bone_R_UpperArm")
pb_rfa = arm.pose.bones.get("Bone_R_Forearm")
pb_rh  = arm.pose.bones.get("Bone_R_Hand")

print(f"R UpperArm rot: {pb_rua.rotation_quaternion}, L: {pb_lua.rotation_quaternion}")
print(f"R ForeArm  rot: {pb_rfa.rotation_quaternion}, L: {pb_lfa.rotation_quaternion}")

# To mirror right arm to left arm in quaternion:
# For X-mirroring: q = (w, x, y, z) -> (w, x, -y, -z) or depending on bone roll
# Let's inspect right hand world pos vs left hand world pos
scale_factor = 340.1627
w_rh = arm.matrix_world @ pb_rh.head * scale_factor
w_lh = arm.matrix_world @ pb_lh.head * scale_factor
print(f"R Hand pos: {w_rh}")
print(f"L Hand pos: {w_lh}")
