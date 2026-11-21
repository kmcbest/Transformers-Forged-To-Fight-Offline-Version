import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BLENDER_EXE = ROOT / "toolchain" / "blender" / "blender.exe"
FBX_PATH = ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

print(f"\n--- Objects in FBX ---")
for o in bpy.data.objects:
    print(f"  Object: {o.name} ({o.type})")

print(f"\n--- Actions in FBX ---")
for act in bpy.data.actions:
    print(f"  Action: '{act.name}' (frames {act.frame_range[0]} to {act.frame_range[1]})")

arm = bpy.data.objects.get("Bip001")
if arm:
    print(f"\nArmature '{arm.name}' has {len(arm.data.bones)} bones")
    print(f"Current action on armature: {arm.animation_data.action.name if arm.animation_data and arm.animation_data.action else 'None'}")
