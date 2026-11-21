import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import json

FBX_PATH = r"E:\Agent\TFTF-blender\3rd-party-models\StarSaber\source\StarSaber.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX_PATH)

ab = bpy.data.objects.get("Symbol_AB.001")
uv_layer = ab.data.uv_layers.active

data = []
for poly in ab.data.polygons:
    pts = []
    for l in poly.loop_indices:
        u, v = uv_layer.data[l].uv
        pts.append([u, v])
    data.append({
        "pts": pts,
        "mat": poly.material_index
    })

with open(r"E:\Agent\TFTF-blender\scratch\symbol_uv.json", "w") as f:
    json.dump(data, f)
print("Dumped symbol_uv.json")
