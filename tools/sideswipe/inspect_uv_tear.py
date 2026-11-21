import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy

FBX_PATH = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\03_fbx_exports\sideswipe_robot_prepared.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX_PATH)

mesh = [o for o in bpy.data.objects if o.type == 'MESH'][0]
uvl = mesh.data.uv_layers.active

torn_polys = []
for p in mesh.data.polygons:
    pu = [uvl.data[li].uv.x for li in p.loop_indices]
    pv = [uvl.data[li].uv.y for li in p.loop_indices]
    span_u = max(pu) - min(pu)
    span_v = max(pv) - min(pv)
    if span_u > 0.70 or span_v > 0.70:
        torn_polys.append((p.index, span_u, span_v, pu, pv))

print(f"Total torn polygons: {len(torn_polys)}")
for idx, su, sv, pu, pv in torn_polys:
    print(f"  Poly #{idx}: span_u={su:.3f}, span_v={sv:.3f}, u={pu}, v={pv}")
