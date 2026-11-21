import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

arm = bpy.data.objects.get("Bip001")
if arm:
    b = arm.data.bones.get("Bone_Pistol")
    if b:
        print(f"Bone_Pistol parent: {b.parent.name if b.parent else None}")
        print(f"Bone_Pistol head: {b.head_local}, tail: {b.tail_local}")
        print(f"Bone_Pistol world head: {arm.matrix_world @ b.head_local}")
