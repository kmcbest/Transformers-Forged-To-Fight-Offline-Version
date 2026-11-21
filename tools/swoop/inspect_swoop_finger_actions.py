import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

FBX_SRC = Path("e:/Agent/TFTF-blender/3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

finger_acts = []
for act in bpy.data.actions:
    for fc in act.fcurves:
        if "Finger" in fc.data_path:
            finger_acts.append((act.name, fc.data_path))
            break

print(f"Total actions with Finger curves: {len(finger_acts)}")
for name, dp in finger_acts[:10]:
    print(f"  {name} -> {dp}")
