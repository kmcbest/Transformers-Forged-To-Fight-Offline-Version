import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

fbx_path = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

arm = bpy.data.objects['Blast-off_ARM']
print("--- ALL BONES in Blast-off_ARM ---")
for b in arm.data.bones:
    print(f"  Bone: {b.name}")

head_obj = bpy.data.objects['RB_Blastoff_CHARSKEL_Head.001.dmx']
print("\n--- ALL VGs in Head.001.dmx ---")
for vg in head_obj.vertex_groups:
    print(f"  VG: {vg.name}")
