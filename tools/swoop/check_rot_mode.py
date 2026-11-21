import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

arm = bpy.data.objects.get("Bip001")
lua = arm.pose.bones.get("Bone_L_UpperArm")
print(f"lua rotation_mode: {lua.rotation_mode}")
print(f"lua rotation_quaternion: {lua.rotation_quaternion}")
print(f"lua rotation_euler: {lua.rotation_euler}")
print(f"lua location: {lua.location}")
