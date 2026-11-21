import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path
import numpy as np

blend_path = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_aligned_mesh\sideswipe_robot_aligned.blend")
bpy.ops.wm.open_mainfile(filepath=str(blend_path))

mesh_obj = next(o for o in bpy.data.objects if o.type == "MESH")
mesh = mesh_obj.data
uv_layer = mesh.uv_layers.active.data

# 2048 occupancy grid
grid = np.zeros((2048, 2048), dtype=bool)

for p in mesh.polygons:
    if p.index < 56: # skip mesh 20
        continue
    p_uvs = [uv_layer[li].uv for li in p.loop_indices]
    xs = [int(np.clip(uv[0] * 2048, 0, 2047)) for uv in p_uvs]
    # In OpenGL/Blender, v=0 is bottom, v=1 is top. In PIL y=0 is top.
    # Let's use Blender v directly: y_blender in [0..2047]
    ys = [int(np.clip(uv[1] * 2048, 0, 2047)) for uv in p_uvs]
    min_x, max_x = max(0, min(xs)-2), min(2047, max(xs)+2)
    min_y, max_y = max(0, min(ys)-2), min(2047, max(ys)+2)
    grid[min_y:max_y+1, min_x:max_x+1] = True

# Check candidate 128x128 patches
candidates = []
for by in range(0, 2048 - 128, 64):
    for bx in range(0, 2048 - 128, 64):
        if not grid[by:by+128, bx:bx+128].any():
            candidates.append((bx, by))

print(f"Total completely empty 128x128 patches: {len(candidates)}")
for bx, by in candidates[:10]:
    u0, u1 = bx / 2048.0, (bx + 128) / 2048.0
    v0, v1 = by / 2048.0, (by + 128) / 2048.0
    # PIL y coordinates (y_pil = 2048 - y_blender)
    y_pil_0 = 2048 - (by + 128)
    y_pil_1 = 2048 - by
    print(f"  Empty Box: X=[{bx}..{bx+128}], Y_blender=[{by}..{by+128}] -> U=[{u0:.3f}..{u1:.3f}], V=[{v0:.3f}..{v1:.3f}] -> Y_pil=[{y_pil_0}..{y_pil_1}]")
