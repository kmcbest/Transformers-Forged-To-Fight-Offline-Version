import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx")

for name in ["bot:window_geo_L", "bot:window_geo_R", "bot:doorInnerPartCyan_geo_L", "bot:door_geo_L"]:
    o = bpy.data.objects.get(name)
    if o:
        verts = [v.co for v in o.data.vertices]
        print(f"{name:30s}: verts={len(verts)}, Y=[{min(v.y for v in verts):.4f}, {max(v.y for v in verts):.4f}] (height in raw FBX)")
