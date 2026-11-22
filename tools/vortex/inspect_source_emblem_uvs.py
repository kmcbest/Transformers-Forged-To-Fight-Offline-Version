import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import zipfile
import tempfile
import os

bpy.ops.wm.read_factory_settings(use_empty=True)

with zipfile.ZipFile(r"O:\agent\transformers-fall-of-cybertron-combaticons.zip", "r") as z:
    tmp_dir = tempfile.mkdtemp()
    fbx_name = "source/transformers fall of cybertron convaticons .fbx"
    z.extract(fbx_name, tmp_dir)
    fbx_path = os.path.join(tmp_dir, fbx_name)
    bpy.ops.import_scene.fbx(filepath=fbx_path)

for o in bpy.data.objects:
    if o.name == "VH_Vortex_SKEL.001.dmx":
        mesh = o.data
        uv_layer = mesh.uv_layers.active
        for poly in mesh.polygons:
            mat = o.data.materials[poly.material_index]
            if "logo" in mat.name.lower():
                print(f"Emblem Poly {poly.index} (Mat '{mat.name}'):")
                for vi, li in zip(poly.vertices, poly.loop_indices):
                    print(f"  v{vi}: co={mesh.vertices[vi].co}, uv={uv_layer.data[li].uv}")
