import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path
import numpy as np

bpy.ops.wm.read_factory_settings(use_empty=True)

fbx_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Vortex\vortex_vh_prepared.fbx")
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

for obj in bpy.data.objects:
    if obj.type == "MESH":
        print(f"Mesh: {obj.name}, verts: {len(obj.data.vertices)}")
        # Check vertex groups
        for vg in obj.vertex_groups:
            print(f"  VG: {vg.name}")
        verts = np.array([v.co for v in obj.data.vertices])
        print(f"Bounds min: {verts.min(axis=0)}")
        print(f"Bounds max: {verts.max(axis=0)}")
        print(f"Center:     {verts.mean(axis=0)}")
