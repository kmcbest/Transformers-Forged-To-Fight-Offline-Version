import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

fbx_path = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

armature = bpy.data.objects.get("brawl_ARM")

for o in bpy.data.objects:
    if o.name.startswith("RB_Brawl") or o.name.startswith("Brawl"):
        mods = [m.type for m in o.modifiers]
        print(f"Object: {o.name:32s} Parent={o.parent.name if o.parent else 'None'} Modifiers={mods}")
