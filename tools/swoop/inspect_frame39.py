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

act = bpy.data.actions.get("Bip001|attack01_ex|Base Layer")
if act and arm.animation_data:
    arm.animation_data.action = act
    bpy.context.scene.frame_set(39)
    bpy.context.view_layer.update()
    
    pb_lh = arm.pose.bones.get("Bone_L_Hand")
    pb_rh = arm.pose.bones.get("Bone_R_Hand")
    pb_head = arm.pose.bones.get("Bone_Head")
    pb_lf = arm.pose.bones.get("Bone_L_Foot00")
    pb_rf = arm.pose.bones.get("Bone_R_Foot00")
    
    scale = 340.16
    print("attack01_ex frame 39:")
    print(f"  Head:   {(arm.matrix_world @ pb_head.head)*scale}")
    print(f"  L_Hand: {(arm.matrix_world @ pb_lh.head)*scale}")
    print(f"  R_Hand: {(arm.matrix_world @ pb_rh.head)*scale}")
    print(f"  L_Foot: {(arm.matrix_world @ pb_lf.head)*scale}")
    print(f"  R_Foot: {(arm.matrix_world @ pb_rf.head)*scale}")
