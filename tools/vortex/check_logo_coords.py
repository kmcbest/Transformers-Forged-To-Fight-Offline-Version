import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.open_mainfile(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vortex_master.blend")
head = bpy.data.objects["RB_Vortex_CHARSKEL_Head.mo.dmx"]

for idx, slot in enumerate(head.material_slots):
    if "faction" in slot.material.name.lower():
        polys = [p for p in head.data.polygons if p.material_index == idx]
        v_indices = {v for p in polys for v in p.vertices}
        coords = [head.data.vertices[v].co for v in v_indices]
        print(f"Faction logo 2-poly coords: {coords}")
