import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

arm = bpy.data.objects.get("Bip001")
for b in arm.data.bones:
    if "Hand" in b.name or "Arm" in b.name or "arm" in b.name:
        print(f"Bone {b.name:20s} parent: {b.parent.name if b.parent else None}")
