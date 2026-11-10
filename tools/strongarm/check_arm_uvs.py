import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

fbx_path = Path(r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

# Check materials and UVs of arm_geo_L and arm_geo_R
for name in ["bot:arm_geo_L", "bot:arm_geo_R", "bot:fender_geo_L", "bot:fender_geo_R"]:
    obj = bpy.data.objects.get(name)
    if obj:
        uvs = [loop.uv[:] for loop in obj.data.uv_layers.active.data]
        u_mean = sum(u[0] for u in uvs) / len(uvs)
        v_mean = sum(u[1] for u in uvs) / len(uvs)
        print(f"{name:20s}: X={obj.location.x:.3f}, UV mean=({u_mean:.3f}, {v_mean:.3f})")
