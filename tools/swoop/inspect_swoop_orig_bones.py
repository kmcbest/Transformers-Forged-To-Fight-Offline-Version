import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

fbx_src = Path(r"E:\Agent\TFTF-blender\3rd-party-models\swoop\01_master\Swoop_pbr.fbx")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx_src))

arm = bpy.data.objects.get("Bip001")
print("Bip001 Armature Bones around Clavicle / Arm:")
for b in arm.data.bones:
    if "clavicle" in b.name.lower() or "upperarm" in b.name.lower() or "shoulder" in b.name.lower():
        pname = b.parent.name if b.parent else "None"
        print(f"  {b.name} (parent: {pname}, head: {b.head}, tail: {b.tail})")
