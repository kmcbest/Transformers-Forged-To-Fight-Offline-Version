import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import zipfile
import tempfile
import os

# Export Source VH_Vortex_SKEL.001.dmx poly centers, UVs, and material_index to JSON from Blender
import json

bpy.ops.wm.read_factory_settings(use_empty=True)
with zipfile.ZipFile(r"O:\agent\transformers-fall-of-cybertron-combaticons.zip", "r") as z:
    tmp_dir = tempfile.mkdtemp()
    fbx_name = "source/transformers fall of cybertron convaticons .fbx"
    z.extract(fbx_name, tmp_dir)
    bpy.ops.import_scene.fbx(filepath=os.path.join(tmp_dir, fbx_name))

src = bpy.data.objects.get("VH_Vortex_SKEL.001.dmx")
m = src.data
uv_l = m.uv_layers.active

polys_info = []
for p in m.polygons:
    uvs = [(round(uv_l.data[li].uv.x, 4), round(uv_l.data[li].uv.y, 4)) for li in p.loop_indices]
    polys_info.append({
        "idx": p.index,
        "mat_idx": p.material_index,
        "mat_name": m.materials[p.material_index].name,
        "uvs": uvs,
    })

out_json = r"e:\Agent\TFTF-blender\tools\vortex\diag\source_vh_polys.json"
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(polys_info, f)
print(f"Saved {len(polys_info)} source polys to {out_json}")
