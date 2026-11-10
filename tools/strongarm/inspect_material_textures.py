import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

fbx_path = Path(r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

for mat in bpy.data.materials:
    print(f"\nMaterial: {mat.name}")
    if mat.use_nodes:
        for node in mat.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                print(f"  Texture node: {node.image.name}, filepath: {node.image.filepath}")
    else:
        print("  (No nodes)")
