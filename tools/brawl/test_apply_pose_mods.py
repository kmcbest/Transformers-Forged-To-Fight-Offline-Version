import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math
from mathutils import Vector, Matrix, Euler, Quaternion
from pathlib import Path

fbx_path = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

armature = bpy.data.objects.get("brawl_ARM")
bpy.context.view_layer.objects.active = armature
bpy.ops.object.mode_set(mode='POSE')

# Pose Left Arm inward
pb_u_L = armature.pose.bones["bip_upperArm_L"]
pb_l_L = armature.pose.bones["bip_lowerArm_L"]
curr_vec_L = pb_l_L.head - pb_u_L.head
target_vec_L = Vector((curr_vec_L.x, 0.0, -curr_vec_L.length))
q_L = curr_vec_L.rotation_difference(target_vec_L)
w_u_L = armature.matrix_world @ pb_u_L.matrix
head_u_L = w_u_L.translation.copy()
M_new_L = Matrix.Translation(head_u_L) @ q_L.to_matrix().to_4x4() @ Matrix.Translation(-head_u_L) @ w_u_L
pb_u_L.matrix = armature.matrix_world.inverted() @ M_new_L

# Pose Right Arm inward
pb_u_R = armature.pose.bones["bip_upperArm_R"]
pb_l_R = armature.pose.bones["bip_lowerArm_R"]
curr_vec_R = pb_l_R.head - pb_u_R.head
target_vec_R = Vector((curr_vec_R.x, 0.0, -curr_vec_R.length))
q_R = curr_vec_R.rotation_difference(target_vec_R)
w_u_R = armature.matrix_world @ pb_u_R.matrix
head_u_R = w_u_R.translation.copy()
M_new_R = Matrix.Translation(head_u_R) @ q_R.to_matrix().to_4x4() @ Matrix.Translation(-head_u_R) @ w_u_R
pb_u_R.matrix = armature.matrix_world.inverted() @ M_new_R

bpy.context.view_layer.update()
bpy.ops.object.mode_set(mode='OBJECT')

brawl_mesh_names = [
    'RB_Brawl_CHARSKEL_Head.mo.dmx',
    'RB_Brawl_CHARSKEL_Chest.mo.dmx',
    'RB_Brawl_CHARSKEL_CapL.mo.dmx',
    'RB_Brawl_CHARSKEL_CapR.mo.dmx',
    'RB_Brawl_CHARSKEL_ArmLoL.mo.dmx',
    'RB_Brawl_CHARSKEL_ArmLoR.mo.dmx',
    'RB_Brawl_CHARSKEL_Legs.mo.dmx',
    'BrawlCannon_STAT.mo.dmx',
    'BrawlCannon_STAT.mo.001.dmx'
]

# Apply armature modifiers on all meshes
for name in brawl_mesh_names:
    obj = bpy.data.objects.get(name)
    if obj:
        bpy.context.view_layer.objects.active = obj
        for mod in list(obj.modifiers):
            if mod.type == 'ARMATURE':
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                    print(f"Applied Armature mod to {name}")
                except Exception as e:
                    print(f"Error applying mod to {name}: {e}")
        # Clear parent keeping transform
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

print("All modifiers applied successfully.")
