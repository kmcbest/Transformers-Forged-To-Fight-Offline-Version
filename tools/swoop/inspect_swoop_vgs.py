import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"e:\Agent\TFTF-blender\3rd-party-models\swoop\01_master\Swoop_pbr.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh = bpy.data.objects.get("Swoop.001")
print(f"Total vertex groups in Swoop.001: {len(mesh.vertex_groups)}")
vgs = [vg.name for vg in mesh.vertex_groups]
for i, name in enumerate(sorted(vgs)):
    print(f"  [{i:02d}] {name}")
