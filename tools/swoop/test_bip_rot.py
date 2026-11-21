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
lh      = arm.pose.bones.get("Bone_L_Hand")
scale = 340.16

bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
eval_arm = arm.evaluated_get(dg)
w_lh0 = (eval_arm.matrix_world @ eval_arm.pose.bones["Bone_L_Hand"].head) * scale
print(f"Base: L_Hand=({w_lh0.x:+.2f}, {w_lh0.y:+.2f}, {w_lh0.z:+.2f})")

# Rotate Bip001 L UpperArm
for axis in [Vector((1,0,0)), Vector((0,1,0)), Vector((0,0,1))]:
    for deg in [-45, -30, 30, 45]:
        dq = Quaternion(axis, math.radians(deg))
        bip_lua.rotation_quaternion = q_dict["Bip001 L UpperArm"] @ dq
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        eval_arm = arm.evaluated_get(dg)
        eval_lh = eval_arm.pose.bones["Bone_L_Hand"]
        w_lh = (eval_arm.matrix_world @ eval_lh.head) * scale
        print(f"Axis {axis} {deg:+3d} deg: L_Hand=({w_lh.x:+.2f}, {w_lh.y:+.2f}, {w_lh.z:+.2f})")
