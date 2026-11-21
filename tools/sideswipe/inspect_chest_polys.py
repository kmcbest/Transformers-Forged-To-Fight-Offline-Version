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

# Find the chest headlights geometry
# In Sideswipe ROTF, the chest has the Corvette Stingray front headlights
# Let's inspect all polygons at Z in [7.5, 9.0], Y < 0 (front), |X| in [0.5, 2.5]
headlight_polys = []
for poly in mesh.polygons:
    p_xs = [mesh.vertices[v].co.x for v in poly.vertices]
    p_ys = [mesh.vertices[v].co.y for v in poly.vertices]
    p_zs = [mesh.vertices[v].co.z for v in poly.vertices]
    mx, my, mz = np.mean(p_xs), np.mean(p_ys), np.mean(p_zs)
    
    # Chest lights are at Z around 8.0 .. 8.8, forward Y < -0.3, X around 0.6 .. 2.0
    if 7.8 <= mz <= 9.0 and my < -0.2 and 0.5 <= abs(mx) <= 2.2:
        uvs = [uv_layer[l_idx].uv for l_idx in poly.loop_indices]
        u_mean = np.mean([uv[0] for uv in uvs])
        v_mean = np.mean([uv[1] for uv in uvs])
        headlight_polys.append((mx, my, mz, u_mean, v_mean, uvs, poly.index))

print(f"Total candidate chest headlight polygons: {len(headlight_polys)}")

# Group by UV clusters
u_all = [p[3] for p in headlight_polys]
v_all = [p[4] for p in headlight_polys]
print(f"UV U range: [{min(u_all):.4f} .. {max(u_all):.4f}]")
print(f"UV V range: [{min(v_all):.4f} .. {max(v_all):.4f}]")

# Let's check polygons with normal pointing forward: normal.y < -0.5
front_facing = [p for p in headlight_polys if mesh.polygons[p[6]].normal.y < -0.4]
print(f"Front-facing polygons: {len(front_facing)}")
for p in front_facing[:20]:
    u_min = min(uv[0] for uv in p[5])
    u_max = max(uv[0] for uv in p[5])
    v_min = min(uv[1] for uv in p[5])
    v_max = max(uv[1] for uv in p[5])
    # PIL Y
    py0 = int((1.0 - v_max) * 2048)
    py1 = int((1.0 - v_min) * 2048)
    px0 = int(u_min * 2048)
    px1 = int(u_max * 2048)
    print(f"  poly {p[6]}: 3D=({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f}) UV=({p[3]:.3f}, {p[4]:.3f}) Pixels: X=[{px0}..{px1}], Y=[{py0}..{py1}]")
