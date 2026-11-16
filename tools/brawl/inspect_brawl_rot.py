import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)

fbx_path = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

armature = bpy.data.objects.get("brawl_ARM")
print(f"brawl_ARM rotation_euler: {armature.rotation_euler}")
print(f"brawl_ARM scale: {armature.scale}")
print(f"brawl_ARM matrix_local:\n{armature.matrix_local}")
