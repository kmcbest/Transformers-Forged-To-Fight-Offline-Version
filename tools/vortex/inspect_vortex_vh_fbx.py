import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Vortex\vortex_vh_prepared.fbx")

for o in bpy.data.objects:
    if o.type == 'MESH':
        print(f"Object: {o.name}, polys: {len(o.data.polygons)}, verts: {len(o.data.vertices)}")
        for m in o.data.materials:
            print(f"  Material: {m.name if m else 'None'}")
