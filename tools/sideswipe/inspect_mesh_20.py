import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy

FBX_PATH = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX_PATH)

obj_20 = bpy.data.objects.get("20")
print(f"Object 20: verts={len(obj_20.data.vertices)}, polys={len(obj_20.data.polygons)}")
uvl = obj_20.data.uv_layers.active
for p in obj_20.data.polygons:
    pu = [uvl.data[li].uv.x for li in p.loop_indices]
    pv = [uvl.data[li].uv.y for li in p.loop_indices]
    span_u = max(pu) - min(pu)
    span_v = max(pv) - min(pv)
    if span_u > 0.5 or span_v > 0.5:
        print(f"  Poly #{p.index}: verts={[v for v in p.vertices]}, span_u={span_u:.3f}, span_v={span_v:.3f}, u={pu}, v={pv}")
