import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

FBX_PATH = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX_PATH)

print("=== All Objects matching blast or vh ===")
for o in bpy.data.objects:
    low = o.name.lower()
    if 'blast' in low or 'vh_' in low:
        mats = [s.name for s in o.material_slots]
        dims = [round(x, 3) for x in o.dimensions] if o.type == 'MESH' else None
        print(f"{o.name} | type={o.type} | parent={o.parent.name if o.parent else None} | dims={dims} | mats={mats}")
