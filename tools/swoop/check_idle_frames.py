import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

arm = bpy.data.objects.get("Bip001")
act = bpy.data.actions.get("Bip001|idle01|Base Layer")
if act and arm.animation_data:
    arm.animation_data.action = act
    for frame in range(1, 42, 5):
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        pb_lh = arm.pose.bones.get("Bone_L_Hand")
        w_lh = arm.matrix_world @ pb_lh.head
        print(f"Frame {frame:2d}: L Hand X = {w_lh.x * 340.16:+.3f}m, Y = {w_lh.y * 340.16:+.3f}m, Z = {w_lh.z * 340.16:+.3f}m")
