import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

fbx_path = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

for o in bpy.data.objects:
    if o.type == 'MESH' and (o.name.startswith("RB_Brawl") or o.name.startswith("Brawl")):
        arm_vgs = [vg.name for vg in o.vertex_groups if 'arm' in vg.name.lower() or 'collar' in vg.name.lower() or 'pad' in vg.name.lower() or 'clav' in vg.name.lower() or 'elbow' in vg.name.lower() or 'shoulder' in vg.name.lower()]
        if arm_vgs:
            print(f"Mesh: {o.name}")
            print(f"   Arm-related vertex groups: {arm_vgs}\n")
