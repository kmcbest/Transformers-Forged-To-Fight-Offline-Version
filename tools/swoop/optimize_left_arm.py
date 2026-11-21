import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Quaternion, Vector
import math

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

arm = bpy.data.objects.get("Bip001")
act = bpy.data.actions.get("Bip001|idle01|Base Layer")
if act and arm.animation_data:
    arm.animation_data.action = act
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()

q_dict = {pb.name: pb.rotation_quaternion.copy() for pb in arm.pose.bones}
loc_dict = {pb.name: pb.location.copy() for pb in arm.pose.bones}

arm.animation_data_clear()

for pb in arm.pose.bones:
    pb.rotation_quaternion = q_dict[pb.name]
    pb.location = loc_dict[pb.name]

bip_lua = arm.pose.bones.get("Bip001 L UpperArm")
bip_lfa = arm.pose.bones.get("Bip001 L Forearm")
scale = 340.16

# We want L_Hand to be near X=+2.33, Y=+0.04, Z=+5.20 (Ramjet LeftHand)
# Let's search a grid of angles
best_diff = 999
best_params = None

for deg_z in range(25, 60, 5):
    for deg_x in range(-50, 20, 5):
        for deg_fa in range(-40, 20, 10):
            dq_ua = Quaternion(Vector((0, 0, 1)), math.radians(deg_z)) @ Quaternion(Vector((1, 0, 0)), math.radians(deg_x))
            dq_fa = Quaternion(Vector((1, 0, 0)), math.radians(deg_fa))
            
            bip_lua.rotation_quaternion = q_dict["Bip001 L UpperArm"] @ dq_ua
            bip_lfa.rotation_quaternion = q_dict["Bip001 L Forearm"] @ dq_fa
            bpy.context.view_layer.update()
            
            dg = bpy.context.evaluated_depsgraph_get()
            eval_arm = arm.evaluated_get(dg)
            w_lh = (eval_arm.matrix_world @ eval_arm.pose.bones["Bone_L_Hand"].head) * scale
            
            # Target is (+2.33, +0.04, +5.20)
            diff = (w_lh - Vector((2.33, 0.04, 5.20))).length
            if diff < best_diff:
                best_diff = diff
                best_params = (deg_z, deg_x, deg_fa, w_lh)

print(f"Best: deg_z={best_params[0]}, deg_x={best_params[1]}, deg_fa={best_params[2]}")
print(f"L_Hand pos: {best_params[3]}, dist to Ramjet LeftHand: {best_diff:.3f}m")
