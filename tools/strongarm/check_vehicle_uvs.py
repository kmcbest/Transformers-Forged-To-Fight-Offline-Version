import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

obj_path = Path(r"E:\Agent\RID_game\strongarm_extracted\strongarm_vehicle.obj")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.obj(filepath=str(obj_path))

m = bpy.data.objects['strongarm_vehicle']
mesh = m.data

# Check faces at max Z vs min Z
uv_layer = mesh.uv_layers.active.data

# Find faces with verts near +Z (Z > 2.5) and near -Z (Z < -2.5)
pos_z_uvs = []
neg_z_uvs = []

for poly in mesh.polygons:
    p_verts = [mesh.vertices[vi].co for vi in poly.vertices]
    z_avg = sum(v.z for v in p_verts) / len(p_verts)
    if z_avg > 2.8:
        for li in poly.loop_indices:
            pos_z_uvs.append(uv_layer[li].uv)
    elif z_avg < -2.8:
        for li in poly.loop_indices:
            neg_z_uvs.append(uv_layer[li].uv)

if pos_z_uvs:
    u_avg = sum(uv.x for uv in pos_z_uvs) / len(pos_z_uvs)
    v_avg = sum(uv.y for uv in pos_z_uvs) / len(pos_z_uvs)
    print(f"+Z faces (Z > 2.8): avg UV = ({u_avg:.3f}, {v_avg:.3f})")

if neg_z_uvs:
    u_avg = sum(uv.x for uv in neg_z_uvs) / len(neg_z_uvs)
    v_avg = sum(uv.y for uv in neg_z_uvs) / len(neg_z_uvs)
    print(f"-Z faces (Z < -2.8): avg UV = ({u_avg:.3f}, {v_avg:.3f})")
