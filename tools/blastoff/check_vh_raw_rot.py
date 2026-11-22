import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

FBX_PATH = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX_PATH)

varm = bpy.data.objects.get("Blast-off_VH_ARM")
print(f"Blast-off_VH_ARM: loc={varm.location}, rot_euler={[round(r, 3) for r in varm.rotation_euler]}")

vmesh = bpy.data.objects.get("VH_Blastoff_SKEL.mo.dmx")
print(f"VH_Blastoff_SKEL.mo.dmx: loc={vmesh.location}, rot_euler={[round(r, 3) for r in vmesh.rotation_euler]}")
print(f"matrix_world translation: {vmesh.matrix_world.to_translation()}")
print(f"matrix_world euler: {[round(r, 3) for r in vmesh.matrix_world.to_euler()]}")
