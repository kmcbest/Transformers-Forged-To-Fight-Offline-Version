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

act = bpy.data.actions.get("Bip001|idle01|Base Layer")
if act and arm.animation_data:
    arm.animation_data.action = act
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()

# Unlink action and keep pose
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')

# Let's inspect local rotation of Bone_L_UpperArm and Bone_L_Forearm
lua = arm.pose.bones.get("Bone_L_UpperArm")
lfa = arm.pose.bones.get("Bone_L_Forearm")
lh  = arm.pose.bones.get("Bone_L_Hand")

# Test rotating Bone_L_UpperArm around local axes
for axis in ['X', 'Y', 'Z']:
    for deg in [-60, -45, -30, 30, 45, 60]:
        lua.rotation_mode = 'XYZ'
        lua.rotation_euler = Euler((0, 0, 0), 'XYZ')
        if axis == 'X': lua.rotation_euler.x = math.radians(deg)
        elif axis == 'Y': lua.rotation_euler.y = math.radians(deg)
        elif axis == 'Z': lua.rotation_euler.z = math.radians(deg)
        bpy.context.view_layer.update()
        w_lh = (arm.matrix_world @ lh.head) * 340.16
        if w_lh.x > 1.5:
            print(f"Axis {axis} {deg:+3d} deg: L_Hand pos = ({w_lh.x:+.2f}, {w_lh.y:+.2f}, {w_lh.z:+.2f})")
