import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

blend_path = Path(r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vehicle\vortex_vehicle.blend")
bpy.ops.wm.open_mainfile(filepath=str(blend_path))
vh_mesh = bpy.data.objects["VH_Vortex_SKEL.001.dmx"]

orig_vgs = {vg.name: vg.index for vg in vh_mesh.vertex_groups}

def resolve_vh_bone(vg_name, v_co):
    if "prop18" in vg_name.lower(): return "RotorMainBlade1"
    if "prop19" in vg_name.lower(): return "RotorMainBlade2"
    if "prop20" in vg_name.lower(): return "RotorMainBlade3"
    if "prop21" in vg_name.lower(): return "RotorMainBlade4"
    if "tail" in vg_name.lower() or "fin" in vg_name.lower(): return "Tail"
    if "wing" in vg_name.lower(): return "WingLeft" if v_co.x < 0 else "WingRight"
    if "head" in vg_name.lower() or "nose" in vg_name.lower(): return "BodyHeadLeft" if v_co.x < 0 else "BodyHeadRight"
    if v_co.y < -5.0: return "Tail"
    if v_co.y > 2.0: return "BodyHeadLeft" if v_co.x < 0 else "BodyHeadRight"
    if abs(v_co.x) > 1.8: return "WingLeft" if v_co.x < 0 else "WingRight"
    return "BodyMainCenterTopLeft" if v_co.x < 0 else "BodyMainCenterTopRight"

resolved_counts = {}
for v in vh_mesh.data.vertices:
    for g in v.groups:
        vg_name = list(orig_vgs.keys())[list(orig_vgs.values()).index(g.group)]
        tb = resolve_vh_bone(vg_name, v.co)
        resolved_counts[tb] = resolved_counts.get(tb, 0) + 1

print("Resolved counts in raw blend:")
for k, cnt in sorted(resolved_counts.items(), key=lambda x: -x[1]):
    print(f"  {k:25s}: {cnt}")

