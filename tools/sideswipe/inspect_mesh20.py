import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path
import numpy as np

fbx_path = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe.fbx")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

obj20 = bpy.data.objects.get("20")
if obj20:
    print(f"Mesh 20: verts={len(obj20.data.vertices)}")
    xs = [v.co.x for v in obj20.data.vertices]
    ys = [v.co.y for v in obj20.data.vertices]
    zs = [v.co.z for v in obj20.data.vertices]
    print(f"  3D Local: X=[{min(xs):.3f}..{max(xs):.3f}], Y=[{min(ys):.3f}..{max(ys):.3f}], Z=[{min(zs):.3f}..{max(zs):.3f}]")
    uv_data = obj20.data.uv_layers.active.data
    us = [uv_data[i].uv[0] for i in range(len(uv_data))]
    vs = [uv_data[i].uv[1] for i in range(len(uv_data))]
    print(f"  UVs: U=[{min(us):.3f}..{max(us):.3f}], V=[{min(vs):.3f}..{max(vs):.3f}]")

# Check what File0018.png is
SRC_TEX_DIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\textures")
print("\nFiles in textures directory:")
for f in SRC_TEX_DIR.iterdir():
    print(f"  {f.name}: size={f.stat().st_size}")
