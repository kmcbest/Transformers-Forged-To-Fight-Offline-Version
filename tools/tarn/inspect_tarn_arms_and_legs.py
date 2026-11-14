import sys
import json
import numpy as np
import bpy
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BAKED_BLEND = r"E:\Agent\TFTF-blender\3rd-party-models\Tarn\06_working\tarn_workspace_baked.blend"

bpy.ops.wm.open_mainfile(filepath=BAKED_BLEND)
robot = bpy.data.objects["Tarn_Robot_LowPoly"]

targets = [
    "part__Cube.000", "part__Cube.006", "part__Cube.025", "part__Cube.027",
    "part__Cube.017", "part__Cube.021", "part__Cube.020", "part__Cube.001", "part__Cube.022",
    "part__Cube.007", "part__Torus.000", "part__Cylinder.014", "part__Cylinder.015",
    "part__Cylinder.042", "part__Cube.045", "part__Cube.054", "part__Cube.055", "part__Cube.057",
    "part__Gear.000", "part__Cube.030", "part__Cube.047", "part__Cube.051",
]
vg_map = {vg.name: vg.index for vg in robot.vertex_groups}

# Print left/right split & min |x| for each
for name in targets:
    idx = vg_map.get(name)
    if idx is None:
        continue
    pts = [v.co for v in robot.data.vertices if any(g.group == idx and g.weight > 0.01 for g in v.groups)]
    arr = np.array([[p.x, p.y, p.z] for p in pts])
    min_abs_x = np.abs(arr[:, 0]).min()
    print(f"{name:22s}: n={len(arr):4d} min|X|={min_abs_x:5.3f} X=[{arr[:,0].min():6.2f},{arr[:,0].max():6.2f}] Y=[{arr[:,1].min():6.2f},{arr[:,1].max():6.2f}] Z=[{arr[:,2].min():6.2f},{arr[:,2].max():6.2f}]")

# Also check Tarn_Robot_LowPoly arm joint centers around Z=[7.5..10.5]
for side, xsgn in [("L(+X)", 1), ("R(-X)", -1)]:
    sub = np.array([[v.co.x, v.co.y, v.co.z] for v in robot.data.vertices if (v.co.x * xsgn > 2.3 and v.co.x * xsgn < 3.6 and 6.0 <= v.co.z <= 9.5)])
    print(f"Arm sleeve {side} X in [2.3,3.6] Z in [6,9.5]: n={len(sub)} center=({sub[:,0].mean():.2f},{sub[:,1].mean():.2f},{sub[:,2].mean():.2f})")

# Check ALL vertex groups that aren't handL/handR/part__ or any vertices with ZERO VG weights
unassigned = 0
for v in robot.data.vertices:
    has_part = any(robot.vertex_groups[g.group].name.startswith(("part__", "handL__", "handR__")) and g.weight > 0.01 for g in v.groups)
    if not has_part:
        unassigned += 1
print(f"Vertices without any part__/handL__/handR__ VG: {unassigned}")
