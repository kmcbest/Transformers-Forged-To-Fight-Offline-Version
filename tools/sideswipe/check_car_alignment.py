import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy
from mathutils import Vector

CAR_FBX = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe_Car.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=CAR_FBX)

mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
for o in mesh_objs:
    print(f"Object {o.name:30s}: loc={o.location}, rot={o.rotation_euler}, scale={o.scale}")
    xs = [(o.matrix_world @ v.co).x for v in o.data.vertices]
    ys = [(o.matrix_world @ v.co).y for v in o.data.vertices]
    zs = [(o.matrix_world @ v.co).z for v in o.data.vertices]
    print(f"  X: [{min(xs):.4f}, {max(xs):.4f}], Y: [{min(ys):.4f}, {max(ys):.4f}], Z: [{min(zs):.4f}, {max(zs):.4f}]")
