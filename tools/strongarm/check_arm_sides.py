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

arm_l = next(o for o in bpy.data.objects if o.name == "bot:arm_geo_L")
arm_r = next(o for o in bpy.data.objects if o.name == "bot:arm_geo_R")

l_xs = [v.co.x for v in arm_l.data.vertices]
r_xs = [v.co.x for v in arm_r.data.vertices]
print(f"Strongarm Left Arm (bot:arm_geo_L) X center: {sum(l_xs)/len(l_xs):.4f}")
print(f"Strongarm Right Arm (bot:arm_geo_R) X center: {sum(r_xs)/len(r_xs):.4f}")
