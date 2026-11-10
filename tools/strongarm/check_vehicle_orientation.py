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
verts = [v.co for v in m.data.vertices]

xs = [v.x for v in verts]
ys = [v.y for v in verts]
zs = [v.z for v in verts]

print(f"X: min={min(xs):.3f}, max={max(xs):.3f}, center={(min(xs)+max(xs))/2:.3f}")
print(f"Y: min={min(ys):.3f}, max={max(ys):.3f}, center={(min(ys)+max(ys))/2:.3f}")
print(f"Z: min={min(zs):.3f}, max={max(zs):.3f}, center={(min(zs)+max(zs))/2:.3f}")
