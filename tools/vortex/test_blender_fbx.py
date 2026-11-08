import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import mathutils
from pathlib import Path

# Load vortex_vh_prepared.fbx in Blender and print bounds
fbx_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Vortex\vortex_vh_prepared.fbx")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

for obj in bpy.context.scene.objects:
    print(f"Object: {obj.name}, type={obj.type}")
    if obj.type == 'MESH':
        xs = [v.co.x for v in obj.data.vertices]
        ys = [v.co.y for v in obj.data.vertices]
        zs = [v.co.z for v in obj.data.vertices]
        print(f"  Mesh vertices: {len(obj.data.vertices)}")
        print(f"  X: [{min(xs):.3f}, {max(xs):.3f}] span={max(xs)-min(xs):.3f}")
        print(f"  Y: [{min(ys):.3f}, {max(ys):.3f}] span={max(ys)-min(ys):.3f}")
        print(f"  Z: [{min(zs):.3f}, {max(zs):.3f}] span={max(zs)-min(zs):.3f}")

