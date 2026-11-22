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
    
    print("[*] Importing source FOC FBX...")
    bpy.ops.import_scene.fbx(filepath=fbx_path)

for o in bpy.data.objects:
    if "logo" in o.name.lower() or "symbol" in o.name.lower() or "faction" in o.name.lower() or "vortex" in o.name.lower():
        print(f"Object: {o.name}, type={o.type}")
        if o.type == 'MESH':
            print("  Materials:", [m.name for m in o.data.materials if m])
            print("  Polys:", len(o.data.polygons), "Verts:", len(o.data.vertices))
