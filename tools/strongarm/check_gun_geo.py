import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx")

gun = bpy.data.objects.get("bot:gun_geo")
if gun:
    verts = [v.co for v in gun.data.vertices]
    print(f"bot:gun_geo: {len(verts)} verts, X=[{min(v.x for v in verts):.3f}, {max(v.x for v in verts):.3f}], Y=[{min(v.y for v in verts):.3f}, {max(v.y for v in verts):.3f}], Z=[{min(v.z for v in verts):.3f}, {max(v.z for v in verts):.3f}]")
