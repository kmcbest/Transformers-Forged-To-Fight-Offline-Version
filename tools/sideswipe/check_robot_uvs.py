import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy

ROBOT_FBX = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=ROBOT_FBX)

for o in bpy.data.objects:
    if o.type == 'MESH':
        uvl = o.data.uv_layers.active
        if uvl:
            us = [d.uv.x for d in uvl.data]
            vs = [d.uv.y for d in uvl.data]
            print(f"Mesh {o.name:15s}: U=[{min(us):.3f}, {max(us):.3f}], V=[{min(vs):.3f}, {max(vs):.3f}], mats={[m.name for m in o.data.materials]}")
