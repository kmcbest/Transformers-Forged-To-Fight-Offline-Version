import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

obj_path = Path(r"E:\Agent\TFTF-blender\tools\strongarm\prowl_ref.obj")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=str(obj_path))

p_obj = bpy.data.objects[0]
# Find top vertices (Y > 8.0)
top_verts = [v for v in p_obj.data.vertices if v.co.y > 8.0]
top_zs = [v.co.z for v in top_verts]
top_xs = [v.co.x for v in top_verts]
print(f"Prowl Head vertices count: {len(top_verts)}")
print(f"  Head Z range: [{min(top_zs):.4f}, {max(top_zs):.4f}], mean={sum(top_zs)/len(top_zs):.4f}")
print(f"  Head X range: [{min(top_xs):.4f}, {max(top_xs):.4f}], mean={sum(top_xs)/len(top_xs):.4f}")

# Find chest vertices (Y between 6.5 and 7.8)
chest_verts = [v for v in p_obj.data.vertices if 6.5 < v.co.y < 7.8]
chest_zs = [v.co.z for v in chest_verts]
print(f"Prowl Chest vertices count: {len(chest_verts)}")
print(f"  Chest Z range: [{min(chest_zs):.4f}, {max(chest_zs):.4f}], mean={sum(chest_zs)/len(chest_zs):.4f}")
