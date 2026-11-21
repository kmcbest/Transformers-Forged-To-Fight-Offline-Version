import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"e:\Agent\TFTF-blender\3rd-party-models\swoop\01_master\Swoop_pbr.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

arm = bpy.data.objects.get("Bip001")
lh = arm.data.bones.get("Bone_L_Hand")
rh = arm.data.bones.get("Bone_R_Hand")
print(f"Bone_L_Hand head: {lh.head_local[:]}")
print(f"Bone_R_Hand head: {rh.head_local[:]}")
