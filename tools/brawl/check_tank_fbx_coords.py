import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

fbx_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Brawl\brawl_tank.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

tank = bpy.context.selected_objects[0]
for o in bpy.data.objects:
    if o.type == 'MESH':
        tank = o
        break

print(f"Tank name: {tank.name}")
xs = [v.co.x for v in tank.data.vertices]
ys = [v.co.y for v in tank.data.vertices]
zs = [v.co.z for v in tank.data.vertices]
print(f"X: [{min(xs):.3f}, {max(xs):.3f}] span={max(xs)-min(xs):.3f}")
print(f"Y: [{min(ys):.3f}, {max(ys):.3f}] span={max(ys)-min(ys):.3f}")
print(f"Z: [{min(zs):.3f}, {max(zs):.3f}] span={max(zs)-min(zs):.3f}")
