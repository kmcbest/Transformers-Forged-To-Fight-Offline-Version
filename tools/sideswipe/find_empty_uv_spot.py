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

# Collect all UV loops (excluding poly 0..55)
all_uvs = []
for p in mesh.polygons:
    if p.index < 56:
        continue
    for li in p.loop_indices:
        all_uvs.append(uv_layer[li].uv)

all_uvs = np.array(all_uvs) # Shape (N, 2)
print(f"Total UV vertices (excluding Mesh 20): {len(all_uvs)}")

# Sample points in top-right or corners
for u_center, v_center, name in [
    (0.02, 0.02, "Corner (0.02, 0.02)"),
    (0.98, 0.02, "Corner (0.98, 0.02)"),
    (0.02, 0.98, "Corner (0.02, 0.98)"),
    (0.98, 0.98, "Corner (0.98, 0.98)"),
    (0.95, 0.95, "Corner (0.95, 0.95)"),
    (0.85, 0.95, "Top (0.85, 0.95)"),
    (0.50, 0.98, "Top (0.50, 0.98)"),
    (0.05, 0.50, "Left (0.05, 0.50)"),
    (0.95, 0.50, "Right (0.95, 0.50)"),
]:
    dists = np.hypot(all_uvs[:, 0] - u_center, all_uvs[:, 1] - v_center)
    min_dist = dists.min()
    pixel_dist = min_dist * 2048
    print(f"{name}: closest UV vertex is {pixel_dist:.1f} pixels away (UV dist = {min_dist:.4f})")
