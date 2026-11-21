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
act = bpy.data.actions.get("Bip001|transform_r|Base Layer")
if act and arm.animation_data:
    arm.animation_data.action = act
    for frame in [1, 20, 40, 60, 80, 84]:
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        lh = arm.pose.bones.get("Bone_L_Hand")
        rh = arm.pose.bones.get("Bone_R_Hand")
        lf = arm.pose.bones.get("Bone_L_Foot00")
        rf = arm.pose.bones.get("Bone_R_Foot00")
        w_lh = arm.matrix_world @ lh.head
        w_rh = arm.matrix_world @ rh.head
        w_lf = arm.matrix_world @ lf.head
        w_rf = arm.matrix_world @ rf.head
        print(f"Frame {frame:2d}:")
        print(f"  Hands: L={w_lh.x:+.4f}, R={w_rh.x:+.4f} (diff X={w_lh.x+w_rh.x:+.4f}, diff Y={w_lh.y-w_rh.y:+.4f})")
        print(f"  Feet:  L={w_lf.x:+.4f}, R={w_rf.x:+.4f} (diff X={w_lf.x+w_rf.x:+.4f}, diff Y={w_lf.y-w_rf.y:+.4f})")
