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

arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
bones = arm.data.bones
print(f"Total bones in Strongarm.fbx: {len(bones)}")
for b in sorted(bones, key=lambda x: x.name):
    print(f"  {b.name}")
