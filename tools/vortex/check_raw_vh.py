import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vehicle\vortex_vehicle.fbx")

for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        xs = [v.co.x for v in obj.data.vertices]
        ys = [v.co.y for v in obj.data.vertices]
        zs = [v.co.z for v in obj.data.vertices]
        print(f"Mesh: {obj.name}")
        print(f"  X: min={min(xs):.2f}, max={max(xs):.2f}, span={max(xs)-min(xs):.2f}")
        print(f"  Y: min={min(ys):.2f}, max={max(ys):.2f}, span={max(ys)-min(ys):.2f}")
        print(f"  Z: min={min(zs):.2f}, max={max(zs):.2f}, span={max(zs)-min(zs):.2f}")
