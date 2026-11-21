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

# List all vertex groups
print("Vertex Groups:")
for g in mesh_obj.vertex_groups:
    print(f"  {g.index}: {g.name}")

# Also check head Z height
z_max = max(v.co.z for v in mesh.vertices)
print(f"Z max = {z_max:.3f}")
# Vertices near top (head):
head_verts = [v for v in mesh.vertices if v.co.z > z_max - 1.2]
print(f"Top 1.2m has {len(head_verts)} vertices")
# Check what vertex groups these head vertices belong to
vg_counts = {}
for v in head_verts:
    for g in v.groups:
        gname = mesh_obj.vertex_groups[g.group].name
        vg_counts[gname] = vg_counts.get(gname, 0) + 1
print("Head vertices belong to groups:", sorted(vg_counts.items(), key=lambda x: -x[1]))
