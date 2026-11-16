import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

obj_path = r"E:\Agent\TFTF-blender\tools\brawl\meg_veh_rest.obj"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=obj_path)

obj = bpy.context.selected_objects[0]
xs = [v.co.x for v in obj.data.vertices]
ys = [v.co.y for v in obj.data.vertices]
zs = [v.co.z for v in obj.data.vertices]

print(f"Megatron Vehicle Rest OBJ bounds:")
print(f"  X: [{min(xs):.3f}, {max(xs):.3f}] span={max(xs)-min(xs):.3f}")
print(f"  Y: [{min(ys):.3f}, {max(ys):.3f}] span={max(ys)-min(ys):.3f}")
print(f"  Z: [{min(zs):.3f}, {max(zs):.3f}] span={max(zs)-min(zs):.3f}")
