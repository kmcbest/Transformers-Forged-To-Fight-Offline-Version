import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import bpy
import bmesh
from mathutils import Vector

TARN_ROOT = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Tarn")
SRC_BLEND = TARN_ROOT / "01_robot_source" / "source" / "last comp3.blend"
SCRATCH_DIR = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\66aaeff3-2652-4f24-8fc9-00b0ef375582\scratch")

bpy.ops.wm.open_mainfile(filepath=str(SRC_BLEND))

# Compute overall robot bounds excluding decal planes if any
# First compute min/max of all visible mesh objects
pts_all = []
for o in bpy.data.objects:
    if o.type == 'MESH' and not ("decal" in o.name.lower() or "panel" in o.name.lower()):
        mw = o.matrix_world
        for v in o.data.vertices:
            pts_all.append(mw @ v.co)
mn = Vector((min(p.x for p in pts_all), min(p.y for p in pts_all), min(p.z for p in pts_all)))
mx = Vector((max(p.x for p in pts_all), max(p.y for p in pts_all), max(p.z for p in pts_all)))
cx = 0.5 * (mn.x + mx.x)
cy = 0.5 * (mn.y + mx.y)
sf = 11.45 / (mx.z - mn.z)

print(f"Raw bounds: min={tuple(round(x,2) for x in mn)}, max={tuple(round(x,2) for x in mx)}, scale_f={sf:.5f}")

def to_norm(p):
    return Vector(((p.x - cx)*sf, (p.y - cy)*sf, (p.z - mn.z)*sf))

print("\n=== ALL OBJECTS (SORTED BY NORMALIZED Z CENTER DESC, TOP TO BOTTOM) ===")
rows = []
for o in bpy.data.objects:
    if o.type not in ('MESH', 'CURVE'):
        continue
    if o.type == 'CURVE':
        rows.append((99.0, o.name, "CURVE", 0, 0, [], [], [0,0,0], [0,0,0]))
        continue
    mw = o.matrix_world
    pts = [to_norm(mw @ v.co) for v in o.data.vertices]
    if not pts:
        continue
    bmn = [round(min(p[i] for p in pts), 2) for i in range(3)]
    bmx = [round(max(p[i] for p in pts), 2) for i in range(3)]
    cz = 0.5 * (bmn[2] + bmx[2])
    mats = [ms.material.name if ms.material else "None" for ms in o.material_slots]
    mods = [f"{m.type}({'1' if m.show_viewport else '0'})" for m in o.modifiers]
    tris = sum(max(0, len(p.vertices)-2) for p in o.data.polygons)
    rows.append((cz, o.name, "MESH", len(o.data.vertices), tris, mats, mods, bmn, bmx))

for cz, nm, tp, vc, tc, mats, mods, bmn, bmx in sorted(rows, key=lambda r: -r[0]):
    print(f"  Z~{cz:5.2f} | {nm:20s} | v={vc:6d} t={tc:6d} | X[{bmn[0]:5.2f},{bmx[0]:5.2f}] Y[{bmn[1]:5.2f},{bmx[1]:5.2f}] Z[{bmn[2]:5.2f},{bmx[2]:5.2f}] | mods={mods} | mats={mats}")
