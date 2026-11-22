import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Vector
import numpy as np

fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\BlastOff\03_fbx_exports\blastoff_robot_prepared.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh_obj = next(o for o in bpy.data.objects if o.type == "MESH")
uv_layer = mesh_obj.data.uv_layers.active.data

# In Blender coords:
# Head center is at X=0, Y ~ -0.4 to 0.0, Z ~ 11.2 to 11.4
# Eyes are on the front face: X in [-0.25, 0.25], Y in [-0.55, -0.40], Z in [11.20, 11.35]
front_eye_polys = []
for p in mesh_obj.data.polygons:
    p_vs = [mesh_obj.data.vertices[v_idx].co for v_idx in p.vertices]
    zm = sum(v.z for v in p_vs) / len(p_vs)
    ym = sum(v.y for v in p_vs) / len(p_vs)
    xm = sum(v.x for v in p_vs) / len(p_vs)
    
    # Front of the face: Y is most negative (front facing in rest pose)
    if 11.15 <= zm <= 11.40 and -0.60 <= ym <= -0.40 and abs(xm) <= 0.25:
        front_eye_polys.append((p, xm, ym, zm))

print(f"Front eye/face polygons found: {len(front_eye_polys)}")
all_eye_uvs = []
for p, xm, ym, zm in front_eye_polys:
    loop_uvs = [uv_layer[l_idx].uv for l_idx in p.loop_indices]
    all_eye_uvs.extend(loop_uvs)
    uv_str = ", ".join([f"({uv.x:.4f}, {uv.y:.4f})" for uv in loop_uvs])
    print(f"  poly at ({xm:.3f}, {ym:.3f}, {zm:.3f}): {uv_str}")

min_u = min(uv.x for uv in all_eye_uvs)
max_u = max(uv.x for uv in all_eye_uvs)
min_v = min(uv.y for uv in all_eye_uvs)
max_v = max(uv.y for uv in all_eye_uvs)
print(f"\nFront eye UV bounds: U=[{min_u:.4f}, {max_u:.4f}], V=[{min_v:.4f}, {max_v:.4f}]")

# Map to 2048x2048 pixel coords:
px_min = int(min_u * 2048)
px_max = int(max_u * 2048)
py_min = int((1.0 - max_v) * 2048)
py_max = int((1.0 - min_v) * 2048)
print(f"Atlas pixel bounds: X=[{px_min}, {px_max}], Y=[{py_min}, {py_max}]")
