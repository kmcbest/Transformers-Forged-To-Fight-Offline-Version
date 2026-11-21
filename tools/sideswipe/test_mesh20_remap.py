import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy
from mathutils import Vector

FBX_PATH = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX_PATH)

obj_20 = bpy.data.objects.get("20")
xs = [v.co.x for v in obj_20.data.vertices]
ys = [v.co.y for v in obj_20.data.vertices]
zs = [v.co.z for v in obj_20.data.vertices]
print(f"Mesh 20 bounds: X=[{min(xs):.4f}, {max(xs):.4f}], Y=[{min(ys):.4f}, {max(ys):.4f}], Z=[{min(zs):.4f}, {max(zs):.4f}]")

# Separate into left (X > 0) and right (X < 0) lights
uvl = obj_20.data.uv_layers.active
for p in obj_20.data.polygons:
    p_xs = [obj_20.data.vertices[vi].co.x for vi in p.vertices]
    is_left = sum(p_xs)/len(p_xs) > 0
    # Left light box in atlas: U in [0.295, 0.325], V in [0.555, 0.565]
    # Right light box in atlas: U in [0.430, 0.460], V in [0.555, 0.565]
    base_u = 0.310 if is_left else 0.445
    base_v = 0.560
    for li in p.loop_indices:
        uvl.data[li].uv = (base_u, base_v)

torn = 0
for p in obj_20.data.polygons:
    pu = [uvl.data[li].uv.x for li in p.loop_indices]
    pv = [uvl.data[li].uv.y for li in p.loop_indices]
    if max(pu) - min(pu) > 0.70 or max(pv) - min(pv) > 0.70:
        torn += 1

print(f"Mesh 20 torn polygons after remap: {torn}")
