import sys
import json
import numpy as np
import bpy
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

bpy.ops.wm.open_mainfile(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\Tarn\06_working\tarn_workspace_baked.blend")
robot = bpy.data.objects["Tarn_Robot_LowPoly"]
hands = json.loads(Path(r"E:\Agent\TFTF-blender\3rd-party-models\Tarn\06_working\tarn_hand_bones.json").read_text(encoding="utf-8"))

vg_map = {vg.name: vg.index for vg in robot.vertex_groups}
print("=== Exact Left Hand Bone & Mesh Geometry (Tarn_Robot_LowPoly) ===")
for bname, info in hands["L"].items():
    vgn = f"handL__{bname}"
    idx = vg_map[vgn]
    pts = [v.co for v in robot.data.vertices if any(g.group == idx and g.weight > 0.25 for g in v.groups)]
    if pts:
        arr = np.array([[p.x, p.y, p.z] for p in pts])
        rng = f"X=[{arr[:,0].min():.2f},{arr[:,0].max():.2f}] Y=[{arr[:,1].min():.2f},{arr[:,1].max():.2f}] Z=[{arr[:,2].min():.2f},{arr[:,2].max():.2f}]"
    else:
        rng = "NO VERTS>0.25"
    h = info["head"]
    t = info["tail"]
    print(f"  {bname:8s} par={str(info['parent']):8s} head=({h[0]:.2f},{h[1]:.2f},{h[2]:.2f}) tail=({t[0]:.2f},{t[1]:.2f},{t[2]:.2f}) | n={len(pts):3d} {rng}")

# Check vertical extent of Fusion Cannon (part__Cylinder.003/004)
for pn in ("part__Cylinder.003", "part__Cylinder.004", "part__Cube.020", "part__Cube.025"):
    idx = vg_map[pn]
    pts = np.array([[v.co.x, v.co.y, v.co.z] for v in robot.data.vertices if any(g.group == idx and g.weight > 0.25 for g in v.groups)])
    print(f"  {pn:20s}: X=[{pts[:,0].min():.2f},{pts[:,0].max():.2f}] Y=[{pts[:,1].min():.2f},{pts[:,1].max():.2f}] Z=[{pts[:,2].min():.2f},{pts[:,2].max():.2f}]")
