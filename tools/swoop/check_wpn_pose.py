import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

arm = bpy.data.objects.get("Bip001")
wpn = bpy.data.objects.get("Swoop_Weapon")

act = bpy.data.actions.get("Bip001|idle01|Base Layer")
if act and arm.animation_data:
    arm.animation_data.action = act
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    
    # Check Bone_Pistol pose bone pos
    pb = arm.pose.bones.get("Bone_Pistol")
    rh = arm.pose.bones.get("Bone_R_Hand")
    if pb and rh:
        print(f"Pose Bone_Pistol head: {arm.matrix_world @ pb.head}")
        print(f"Pose Bone_R_Hand head: {arm.matrix_world @ rh.head}")
        
    pts = [wpn.matrix_world @ v.co for v in wpn.data.vertices]
    print(f"Swoop_Weapon evaluated center: {sum(pts, bpy.mathutils.Vector((0,0,0))) / len(pts)}")
