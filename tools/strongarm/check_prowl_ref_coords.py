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
xs = [v.co.x for v in p_obj.data.vertices]
ys = [v.co.y for v in p_obj.data.vertices]
zs = [v.co.z for v in p_obj.data.vertices]

print(f"Prowl Ref Mesh in Blender:")
print(f"  X: [{min(xs):.4f}, {max(xs):.4f}], span={max(xs)-min(xs):.4f}")
print(f"  Y: [{min(ys):.4f}, {max(ys):.4f}], span={max(ys)-min(ys):.4f}")
print(f"  Z: [{min(zs):.4f}, {max(zs):.4f}], span={max(zs)-min(zs):.4f}")
