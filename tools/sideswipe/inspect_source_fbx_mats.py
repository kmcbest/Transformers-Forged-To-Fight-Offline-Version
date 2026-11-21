import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

fbx_path = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe.fbx")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

print("=== Imported FBX Objects ===")
for obj in bpy.data.objects:
    if obj.type == "MESH":
        print(f"Mesh: {obj.name}, verts={len(obj.data.vertices)}")
        for i, m in enumerate(obj.data.materials):
            print(f"  Mat {i}: {m.name if m else 'None'}")
            if m and m.use_nodes:
                for node in m.node_tree.nodes:
                    if node.type == "TEX_IMAGE" and node.image:
                        print(f"    Node tex: {node.image.name} ({node.image.filepath})")
