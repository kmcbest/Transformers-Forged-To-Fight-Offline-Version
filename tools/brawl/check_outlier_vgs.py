import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

bpy.ops.wm.open_mainfile(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\Brawl\01_aligned_mesh\brawl_robot_aligned.blend")
r = bpy.data.objects["cha_brawl_gs_00"]
arm = bpy.data.objects["ARM_Brawl_Robot"]

for vg in r.vertex_groups:
    pts = [v.co for v in r.data.vertices if any(g.group == vg.index and g.weight > 0.5 for g in v.groups)]
    if pts:
        xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
        if min(zs) < -0.1 or min(ys) < -1.8 or max(ys) > 1.8:
            print(f"OUTLIER VG {vg.name:18s}: n={len(pts):4d} X=[{min(xs):.2f},{max(xs):.2f}] Y=[{min(ys):.2f},{max(ys):.2f}] Z=[{min(zs):.2f},{max(zs):.2f}]")
