import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

arm = bpy.data.objects.get("Bip001")
swoop = bpy.data.objects.get("Swoop.001")

act = bpy.data.actions.get("Bip001|idle01|Base Layer")
if act and arm.animation_data:
    arm.animation_data.action = act
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()

scale_factor = 340.1627
# Head to foot offset
min_z = 0.000

for bname in [
    "Bone_Head", "Bip001 Spine1", "Bone_Pelvis",
    "Bone_L_UpperArm", "Bone_L_Forearm", "Bone_L_Hand",
    "Bone_R_UpperArm", "Bone_R_Forearm", "Bone_R_Hand",
    "Bone_L_Thigh", "Bone_L_Calf", "Bone_L_Foot00",
    "Bone_R_Thigh", "Bone_R_Calf", "Bone_R_Foot00",
]:
    pb = arm.pose.bones.get(bname)
    if pb:
        w_head = arm.matrix_world @ pb.head
        scaled_head = Vector((w_head.x * scale_factor, w_head.y * scale_factor, (w_head.z - min_z) * scale_factor))
        print(f"Swoop {bname:18s}: X={scaled_head.x:+.3f}, Y={scaled_head.y:+.3f}, Z={scaled_head.z:+.3f}")
