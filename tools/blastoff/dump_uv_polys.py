import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import bpy
import json
from pathlib import Path

FBX_PATH = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
OUT_JSON = Path(r"E:\Agent\TFTF-blender\renders\blastoff\uv_islands_dump.json")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX_PATH)

def dominant_bone(obj, poly):
    acc = {}
    for vi in poly.vertices:
        for g in obj.data.vertices[vi].groups:
            bname = obj.vertex_groups[g.group].name
            acc[bname] = acc.get(bname, 0.0) + g.weight
    return max(acc.items(), key=lambda x: x[1])[0] if acc else "NONE"

records = []
for oname in ["RB_Blastoff_CHARSKEL_Head.001.dmx", "RB_Blastoff_CHARSKEL_ArmLoL.001.dmx", "VH_Blastoff_SKEL.mo.dmx", "VH_BlastoffWing_STAT.mo.001.dmx", "RB_BlastoffWing_STAT.001.dmx"]:
    obj = bpy.data.objects.get(oname)
    if not obj:
        # Check what vehicle object is named
        continue
    uv_layer = obj.data.uv_layers.active
    mat_slots = [s.material.name if s.material else "" for s in obj.material_slots]
    mw = obj.matrix_world
    for poly in obj.data.polygons:
        mname = mat_slots[poly.material_index] if poly.material_index < len(mat_slots) else ""
        cw = mw @ poly.center
        bone = dominant_bone(obj, poly)
        pts = []
        for li in poly.loop_indices:
            uv = uv_layer.data[li].uv
            pts.append([round(uv.x % 1.0, 4), round(uv.y % 1.0, 4)])
        records.append({
            "obj": oname,
            "mat": mname,
            "bone": bone,
            "w": [round(cw.x, 3), round(cw.y + 10.0118, 3), round(cw.z, 3)],
            "uv": pts,
        })

# Also print all mesh object names in FBX so we don't miss vehicle mesh
print("All Blastoff objects:", [o.name for o in bpy.data.objects if "blast" in o.name.lower() and o.type == "MESH"])
OUT_JSON.write_text(json.dumps(records), encoding="utf-8")
print(f"Wrote {len(records)} polygon UV records to {OUT_JSON}")
