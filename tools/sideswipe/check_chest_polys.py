import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

blend_path = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_aligned_mesh\sideswipe_robot_aligned.blend")
bpy.ops.wm.open_mainfile(filepath=str(blend_path))

mesh_obj = next(o for o in bpy.data.objects if o.type == "MESH")
mesh = mesh_obj.data
uv_layer = mesh.uv_layers.active.data

chest_polys = []
for p in mesh.polygons:
    p_uvs = [uv_layer[li].uv for li in p.loop_indices]
    u_mean = sum(uv[0] for uv in p_uvs) / len(p_uvs)
    v_mean = sum(uv[1] for uv in p_uvs) / len(p_uvs)
    
    # Check if in chest vent UV bounds
    # In OpenGL/Blender, v_mean in [0.54, 0.58] is y_pil in [860, 940]
    if 0.54 <= v_mean <= 0.58 and ((0.28 <= u_mean <= 0.34) or (0.42 <= u_mean <= 0.48)):
        p_xs = [mesh.vertices[vi].co.x for vi in p.vertices]
        p_ys = [mesh.vertices[vi].co.y for vi in p.vertices]
        p_zs = [mesh.vertices[vi].co.z for vi in p.vertices]
        chest_polys.append((p.index, sum(p_xs)/len(p_xs), sum(p_ys)/len(p_ys), sum(p_zs)/len(p_zs), u_mean, v_mean))

print(f"Total polygons in chest vent UV region: {len(chest_polys)}")
for cp in chest_polys:
    print(f"  poly {cp[0]}: 3D=({cp[1]:.2f}, {cp[2]:.2f}, {cp[3]:.2f}), UV=({cp[4]:.3f}, {cp[5]:.3f})")
