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
print(f"brawl_ARM matrix_world translation: {armature.matrix_world.translation}")

brawl_mesh_names = [
    'RB_Brawl_CHARSKEL_Head.mo.dmx',
    'RB_Brawl_CHARSKEL_Chest.mo.dmx',
    'RB_Brawl_CHARSKEL_Legs.mo.dmx',
    'VH_BrawlCINE_SKEL.001.dmx'
]
for name in brawl_mesh_names:
    obj = bpy.data.objects.get(name)
    if obj:
        print(f"{name}: parent={obj.parent.name if obj.parent else None}, matrix_world translation={obj.matrix_world.translation}")
