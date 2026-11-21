import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy
from pathlib import Path

CAR_FBX = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe_Car.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=CAR_FBX)

mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in mesh_objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = mesh_objs[0]
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

for o in mesh_objs:
    xs = [v.co.x for v in o.data.vertices]
    ys = [v.co.y for v in o.data.vertices]
    zs = [v.co.z for v in o.data.vertices]
    print(f"Mesh {o.name:25s}: X=[{min(xs):.3f}, {max(xs):.3f}], Y=[{min(ys):.3f}, {max(ys):.3f}], Z=[{min(zs):.3f}, {max(zs):.3f}]")
