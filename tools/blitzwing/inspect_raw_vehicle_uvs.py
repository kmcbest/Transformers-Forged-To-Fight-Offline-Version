import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Vector, Matrix
from pathlib import Path

BLEND_SRC = Path(r"E:\Agent\TFTF-blender\3rd-party-models\blitzwing_extracted\rar\Blitzwing.blend")
bpy.ops.wm.open_mainfile(filepath=str(BLEND_SRC))

# 1. Inspect Tank
tank = bpy.data.objects['Blitzwing_Alt_Tank']
print("=== TANK MODE ===")
print("Materials:", [m.name for m in tank.data.materials])
uv_layer = tank.data.uv_layers.active.data

# Check UVs per polygon material index
u_min, u_max = [1e9]*3, [-1e9]*3
v_min, v_max = [1e9]*3, [-1e9]*3
for poly in tank.data.polygons:
    mat_idx = poly.material_index
    for loop_idx in poly.loop_indices:
        uv = uv_layer[loop_idx].uv
        u_min[mat_idx] = min(u_min[mat_idx], uv.x)
        u_max[mat_idx] = max(u_max[mat_idx], uv.x)
        v_min[mat_idx] = min(v_min[mat_idx], uv.y)
        v_max[mat_idx] = max(v_max[mat_idx], uv.y)

for i, m in enumerate(tank.data.materials):
    print(f"  Slot {i} ({m.name}): U=[{u_min[i]:.3f}, {u_max[i]:.3f}], V=[{v_min[i]:.3f}, {v_max[i]:.3f}]")

# 2. Inspect Jet
jet = bpy.data.objects['Blitzwing_Jet Mode']
print("\n=== JET MODE ===")
print("Materials:", [m.name for m in jet.data.materials])
uv_layer_j = jet.data.uv_layers.active.data
u_min_j, u_max_j = [1e9]*2, [-1e9]*2
v_min_j, v_max_j = [1e9]*2, [-1e9]*2
for poly in jet.data.polygons:
    mat_idx = poly.material_index
    for loop_idx in poly.loop_indices:
        uv = uv_layer_j[loop_idx].uv
        u_min_j[mat_idx] = min(u_min_j[mat_idx], uv.x)
        u_max_j[mat_idx] = max(u_max_j[mat_idx], uv.x)
        v_min_j[mat_idx] = min(v_min_j[mat_idx], uv.y)
        v_max_j[mat_idx] = max(v_max_j[mat_idx], uv.y)

for i, m in enumerate(jet.data.materials):
    print(f"  Slot {i} ({m.name}): U=[{u_min_j[i]:.3f}, {u_max_j[i]:.3f}], V=[{v_min_j[i]:.3f}, {v_max_j[i]:.3f}]")
