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

mesh_obj = None
for o in bpy.data.objects:
    if o.type == "MESH":
        mesh_obj = o
        break

print(f"Mesh object: {mesh_obj.name}, verts: {len(mesh_obj.data.vertices)}, polys: {len(mesh_obj.data.polygons)}")

# Let's inspect vertices on the head
# Head top is Y ~ 12.0m, eyes are Y ~ 11.2m, chin is Y ~ 10.65m (in Unity coordinates, Blender Z)
uv_layer = mesh_obj.data.uv_layers.active.data

# Find polygons at the eyes/visor
# Visor is at Z in [11.0, 11.4], and Y in [0.1, 0.6] (front)
eye_polys = []
crown_polys = []
for p in mesh_obj.data.polygons:
    p_vs = [mesh_obj.data.vertices[v_idx].co for v_idx in p.vertices]
    z_mean = sum(v.z for v in p_vs) / len(p_vs)
    y_mean = sum(v.y for v in p_vs) / len(p_vs)
    x_mean = sum(v.x for v in p_vs) / len(p_vs)
    
    # In Blender: Z is height!
    # Crown is at top of head: Z > 11.7
    if z_mean > 11.7:
        crown_polys.append(p)
    # Eyes / visor: Z in [11.1, 11.4], Y < -0.1 (or Y > 0.1 depending on orientation)
    if 11.1 <= z_mean <= 11.4 and abs(x_mean) < 0.6:
        eye_polys.append((p, x_mean, y_mean, z_mean))

print(f"Crown polygons (Z > 11.7): {len(crown_polys)}")
for p in crown_polys[:5]:
    loop_uvs = [uv_layer[l_idx].uv for l_idx in p.loop_indices]
    print(f"  Crown poly UVs: {[(round(uv.x, 4), round(uv.y, 4)) for uv in loop_uvs]}")

print(f"Eye/face candidate polygons: {len(eye_polys)}")
for p, xm, ym, zm in eye_polys:
    loop_uvs = [uv_layer[l_idx].uv for l_idx in p.loop_indices]
    print(f"  Eye poly at ({xm:.3f}, {ym:.3f}, {zm:.3f}) UVs: {[(round(uv.x, 4), round(uv.y, 4)) for uv in loop_uvs]}")
