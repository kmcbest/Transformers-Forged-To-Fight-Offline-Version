import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx")

for o in bpy.data.objects:
    if o.type == 'MESH':
        if any(k in o.name.lower() for k in ["deco", "cyan", "fender", "shin"]):
            print(f"{o.name:30s}: verts={len(o.data.vertices)}, vgs={[vg.name for vg in o.vertex_groups]}")
