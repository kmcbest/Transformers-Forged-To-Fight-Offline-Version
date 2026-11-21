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

# Record quaternions at frame 1
q_dict = {pb.name: pb.rotation_quaternion.copy() for pb in arm.pose.bones}
loc_dict = {pb.name: pb.location.copy() for pb in arm.pose.bones}

arm.animation_data_clear()

for pb in arm.pose.bones:
    pb.rotation_quaternion = q_dict[pb.name]
    pb.location = loc_dict[pb.name]

lua = arm.pose.bones.get("Bone_L_UpperArm")
scale = 340.16

# Test with depsgraph
for deg in [-60, -45, -30, 30, 45, 60]:
    dq = Quaternion(Vector((0, 0, 1)), math.radians(deg))
    lua.rotation_quaternion = q_dict["Bone_L_UpperArm"] @ dq
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    eval_arm = arm.evaluated_get(dg)
    eval_lh = eval_arm.pose.bones["Bone_L_Hand"]
    w_lh = (eval_arm.matrix_world @ eval_lh.head) * scale
    print(f"Z {deg:+3d} deg: L_Hand=({w_lh.x:+.2f}, {w_lh.y:+.2f}, {w_lh.z:+.2f})")
