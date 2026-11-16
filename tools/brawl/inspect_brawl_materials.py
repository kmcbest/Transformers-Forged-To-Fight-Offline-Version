import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)

fbx_path = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

brawl_meshes = [
    'RB_Brawl_CHARSKEL_Head.mo.dmx',
    'RB_Brawl_CHARSKEL_Chest.mo.dmx',
    'RB_Brawl_CHARSKEL_CapL.mo.dmx',
    'RB_Brawl_CHARSKEL_CapR.mo.dmx',
    'RB_Brawl_CHARSKEL_ArmLoL.mo.dmx',
    'RB_Brawl_CHARSKEL_ArmLoR.mo.dmx',
    'RB_Brawl_CHARSKEL_Legs.mo.dmx',
    'BrawlCannon_STAT.mo.dmx',
    'BrawlCannon_STAT.mo.001.dmx',
    'VH_BrawlCINE_SKEL.001.dmx'
]

print("--- MESH MATERIAL SLOTS ---")
for name in brawl_meshes:
    obj = bpy.data.objects.get(name)
    if obj:
        mat_names = [slot.material.name if slot.material else 'None' for slot in obj.material_slots]
        print(f"{name}: {mat_names}")
