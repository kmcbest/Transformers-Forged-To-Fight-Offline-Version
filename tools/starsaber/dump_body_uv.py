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

body = bpy.data.objects.get("StarSaber.001")
uv_layer = body.data.uv_layers.active

polys = []
for p in body.data.polygons:
    polys.append([uv_layer.data[l].uv[:] for l in p.loop_indices])

with open(r"E:\Agent\TFTF-blender\scratch\body_uvs.json", "w") as f:
    json.dump(polys, f)
print("Saved body_uvs.json")
