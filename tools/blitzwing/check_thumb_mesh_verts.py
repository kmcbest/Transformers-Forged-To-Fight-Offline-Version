import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(r"E:\Agent\TFTF-blender")
BLEND_SRC = ROOT / "3rd-party-models" / "blitzwing_extracted" / "rar" / "Blitzwing.blend"

bpy.ops.wm.open_mainfile(filepath=str(BLEND_SRC))
m = bpy.data.objects['Blitzwing']

vg_names = [vg.name for vg in m.vertex_groups]
thumb_vgs = [name for name in vg_names if "Finger0" in name]
print("Thumb vertex groups in Blitzwing.blend:", thumb_vgs)

for vg_name in thumb_vgs:
    vg_idx = m.vertex_groups[vg_name].index
    verts = [v for v in m.data.vertices if any(g.group == vg_idx and g.weight > 0.1 for g in v.groups)]
    if verts:
        min_x = min(v.co.x for v in verts)
        max_x = max(v.co.x for v in verts)
        min_y = min(v.co.y for v in verts)
        max_y = max(v.co.y for v in verts)
        min_z = min(v.co.z for v in verts)
        max_z = max(v.co.z for v in verts)
        c = sum((v.co for v in verts), Vector()) / len(verts)
        print(f"Group '{vg_name}': {len(verts)} verts, center=({c.x:.3f}, {c.y:.3f}, {c.z:.3f})")
        print(f"   X=[{min_x:.3f}, {max_x:.3f}], Y=[{min_y:.3f}, {max_y:.3f}], Z=[{min_z:.3f}, {max_z:.3f}]")
