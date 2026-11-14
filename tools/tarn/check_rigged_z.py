import sys
import bpy
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

bpy.ops.wm.open_mainfile(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\Tarn\06_working\tarn_rigged_um53.blend")
r = bpy.data.objects["Tarn_Robot_LowPoly"]
vg_names = [vg.name for vg in r.vertex_groups]
min_zs = {}
for vg in r.vertex_groups:
    pts = [v.co.z for v in r.data.vertices if any(g.group == vg.index and g.weight > 0.3 for g in v.groups)]
    if pts:
        min_zs[vg.name] = (min(pts), max(pts))
for bn, (mn, mx) in sorted(min_zs.items(), key=lambda x: x[1][0]):
    if mn < 1.5:
        print(f"  {bn:22s}: Z=[{mn:6.3f}, {mx:6.3f}]")
