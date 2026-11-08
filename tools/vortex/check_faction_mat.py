import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

bpy.ops.wm.open_mainfile(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vortex_master.blend")

head = bpy.data.objects["RB_Vortex_CHARSKEL_Head.mo.dmx"]
for idx, slot in enumerate(head.material_slots):
    mname = slot.material.name if slot.material else "None"
    polys = [p for p in head.data.polygons if p.material_index == idx]
    print(f"Slot {idx}: {mname} -> {len(polys)} polys")
    if "faction" in mname.lower():
        uv_layer = head.data.uv_layers.active
        uvs = [uv_layer.data[li].uv for p in polys[:5] for li in p.loop_indices]
        print(f"   Faction UV sample: {[(round(u[0], 3), round(u[1], 3)) for u in uvs[:8]]}")
