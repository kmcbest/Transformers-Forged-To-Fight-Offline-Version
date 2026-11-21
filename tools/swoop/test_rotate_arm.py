import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Matrix, Vector, Quaternion
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

def rotate_pose_bone_world(arm_obj, bname, axis_w, angle_deg):
    bpy.context.view_layer.update()
    pb = arm_obj.pose.bones[bname]
    w_old = arm_obj.matrix_world @ pb.matrix
    q = Quaternion(axis_w.normalized(), math.radians(angle_deg))
    R_new = q.to_matrix() @ w_old.to_3x3()
    M_new_w = R_new.to_4x4()
    M_new_w.translation = w_old.translation.copy()
    pb.matrix = arm_obj.matrix_world.inverted() @ M_new_w
    bpy.context.view_layer.update()

bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')

lh = arm.pose.bones.get("Bone_L_Hand")
rh = arm.pose.bones.get("Bone_R_Hand")
scale = 340.16

w_lh0 = (arm.matrix_world @ lh.head) * scale
w_rh0 = (arm.matrix_world @ rh.head) * scale
print(f"Initial: L_Hand=({w_lh0.x:+.2f}, {w_lh0.y:+.2f}, {w_lh0.z:+.2f}), R_Hand=({w_rh0.x:+.2f}, {w_rh0.y:+.2f}, {w_rh0.z:+.2f})")

# Test rotating around Z and X
for deg_z in [-50, -40, -30, 30, 40, 50]:
    # Reset pose
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    rotate_pose_bone_world(arm, "Bone_L_UpperArm", Vector((0, 0, 1)), deg_z)
    w_lh = (arm.matrix_world @ lh.head) * scale
    print(f"deg_z {deg_z:+3d}: L_Hand=({w_lh.x:+.2f}, {w_lh.y:+.2f}, {w_lh.z:+.2f})")
