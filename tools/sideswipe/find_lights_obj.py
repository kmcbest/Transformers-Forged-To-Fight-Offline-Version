import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

source_fbx = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe.fbx")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(source_fbx))

for o in bpy.data.objects:
    if o.type == 'MESH':
        mats = [m.name for m in o.data.materials if m]
        if "Lights" in mats or o.name == "20":
            print(f"Object '{o.name}' has materials: {mats}, verts={len(o.data.vertices)}, polys={len(o.data.polygons)}")
