import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

FBX_PATH = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX_PATH)

arm = bpy.data.objects.get("Blast-off_ARM")
print(f"Blast-off_ARM loc={arm.location}, mw_loc={arm.matrix_world.to_translation()}")

for o in bpy.data.objects:
    if "blast" in o.name.lower():
        print(f"  {o.name}: loc={o.location}, mw_loc={o.matrix_world.to_translation()}")
