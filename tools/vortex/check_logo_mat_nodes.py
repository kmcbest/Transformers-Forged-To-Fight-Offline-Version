import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.open_mainfile(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vortex_master.blend")
mat = bpy.data.materials.get("TR_FactionLogo_Mat_INST.004")
if mat:
    print(f"Material {mat.name}: use_nodes={mat.use_nodes}")
    if mat.use_nodes:
        for node in mat.node_tree.nodes:
            print(f"   Node: {node.type} ({node.name})")
            if node.type == 'TEX_IMAGE' and node.image:
                print(f"      Image: {node.image.name}, filepath={node.image.filepath}")
else:
    print("Material not found!")
