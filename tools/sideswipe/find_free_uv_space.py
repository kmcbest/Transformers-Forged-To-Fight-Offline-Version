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

# Create occupancy grid 128x128
grid = np.zeros((128, 128), dtype=bool)

for p in mesh.polygons:
    # exclude poly 0..55 (Mesh 20)
    if p.index < 56:
        continue
    for li in p.loop_indices:
        u, v = uv_layer[li].uv
        gx = int(np.clip(u * 128, 0, 127))
        gy = int(np.clip(v * 128, 0, 127))
        grid[gy, gx] = True

# Find large empty boxes
free_pct = (~grid).mean() * 100
print(f"Free UV grid cells: {free_pct:.1f}%")

# Check corners:
# In UV space (u in [0..1], v in [0..1]):
for u0, v0, u1, v1, name in [
    (0.0, 0.0, 0.2, 0.2, "Bottom-Left"),
    (0.8, 0.0, 1.0, 0.2, "Bottom-Right"),
    (0.0, 0.8, 0.2, 1.0, "Top-Left"),
    (0.8, 0.8, 1.0, 1.0, "Top-Right"),
    (0.0, 0.4, 0.1, 0.6, "Middle-Left"),
    (0.9, 0.4, 1.0, 0.6, "Middle-Right"),
]:
    gu0, gu1 = int(u0 * 128), int(u1 * 128)
    gv0, gv1 = int(v0 * 128), int(v1 * 128)
    occ = grid[gv0:gv1, gu0:gu1].sum()
    total = (gu1 - gu0) * (gv1 - gv0)
    print(f"Region {name} (U=[{u0},{u1}], V=[{v0},{v1}]): {occ}/{total} occupied ({occ/total*100:.1f}%)")
