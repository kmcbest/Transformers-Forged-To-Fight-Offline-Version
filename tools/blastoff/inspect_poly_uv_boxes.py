import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\BlastOff\03_fbx_exports\blastoff_robot_prepared.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh_obj = next(o for o in bpy.data.objects if o.type == "MESH")
uv_layer = mesh_obj.data.uv_layers.active.data

# Find all vertices with bone weight bip_head > 0.5
head_vg_idx = mesh_obj.vertex_groups.get("Head") or mesh_obj.vertex_groups.get("bip_head")
print("Head vertex group:", head_vg_idx.name if head_vg_idx else "None")

# Find polygons where Z in [10.5, 12.5]
head_polys = []
for p in mesh_obj.data.polygons:
    p_vs = [mesh_obj.data.vertices[v_idx].co for v_idx in p.vertices]
    z_mean = sum(v.z for v in p_vs) / len(p_vs)
    if z_mean > 10.5:
        head_polys.append((p, z_mean))

print(f"Total head polygons: {len(head_polys)}")

# For all head polygons, get their UV bounding box in atlas (U in [0.5, 0.75], V in [0.75, 1.0])
# Convert atlas UV to tile UV: u_tile = (U - 0.5) / 0.25, v_tile = (V - 0.75) / 0.25
# In tile pixels (512x512):
# In PIL, y_pil = (1 - v_tile) * 512
# x_pil = u_tile * 512

# Let's inspect eye polygons: Z in [11.15, 11.35], and front-facing (Y < -0.2 in Blender, since -Y is forward)
eye_polys = []
crown_polys = []
for p, z in head_polys:
    p_vs = [mesh_obj.data.vertices[v_idx].co for v_idx in p.vertices]
    y_mean = sum(v.y for v in p_vs) / len(p_vs)
    x_mean = sum(v.x for v in p_vs) / len(p_vs)
    
    # Check crown: Z > 11.85
    if z > 11.85:
        crown_polys.append((p, x_mean, y_mean, z))
    # Check eyes/visor: Z in [11.15, 11.35], y_mean < -0.3
    if 11.15 <= z <= 11.35 and y_mean < -0.2:
        eye_polys.append((p, x_mean, y_mean, z))

print(f"Crown polys: {len(crown_polys)}, Eye polys: {len(eye_polys)}")

def get_pil_coords(poly):
    res = []
    for li in poly.loop_indices:
        uv = uv_layer[li].uv
        u_tile = (uv.x - 0.5) / 0.25
        v_tile = (uv.y - 0.75) / 0.25
        x_pil = u_tile * 512.0
        y_pil = (1.0 - v_tile) * 512.0
        res.append((round(x_pil, 1), round(y_pil, 1)))
    return res

print("\n--- Crown polygon tile PIL coords ---")
all_crown_x = []
all_crown_y = []
for p, xm, ym, z in crown_polys:
    coords = get_pil_coords(p)
    for cx, cy in coords:
        all_crown_x.append(cx)
        all_crown_y.append(cy)

if all_crown_x:
    print(f"Crown PIL box: X=[{min(all_crown_x)}, {max(all_crown_x)}], Y=[{min(all_crown_y)}, {max(all_crown_y)}]")

print("\n--- Eye polygon tile PIL coords ---")
all_eye_x = []
all_eye_y = []
for p, xm, ym, z in eye_polys:
    coords = get_pil_coords(p)
    for cx, cy in coords:
        all_eye_x.append(cx)
        all_eye_y.append(cy)

if all_eye_x:
    print(f"Eye PIL box: X=[{min(all_eye_x)}, {max(all_eye_x)}], Y=[{min(all_eye_y)}, {max(all_eye_y)}]")
