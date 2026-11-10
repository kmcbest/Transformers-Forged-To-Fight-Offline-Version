import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx")

for name in ['bot:palm_geo_L', 'bot:palm_geo_R', 'bot:hand_geo_L', 'bot:hand_geo_R']:
    o = bpy.data.objects.get(name)
    print(f"=== {name} ===")
    print(f"  parent: {o.parent}")
    print(f"  matrix_local: {o.matrix_local.translation}")
    print(f"  matrix_world: {o.matrix_world.translation}")
    for m in o.modifiers:
        print(f"  modifier: {m.type}, name: {m.name}")
        if m.type == 'ARMATURE':
            print(f"    armature object: {m.object}")
