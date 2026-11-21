import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FBX_PATH = ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

print("=== ALL UNIQUE ACTION NAMES (stripping object prefix) ===")
unique_names = set()
for a in bpy.data.actions:
    parts = a.name.split("|")
    act_core = parts[1] if len(parts) > 1 else a.name
    unique_names.add(act_core)

for n in sorted(unique_names):
    print(" ", n)
