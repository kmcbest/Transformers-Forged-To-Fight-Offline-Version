import sys
from pathlib import Path
import bpy
import mathutils

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
SRC_DIR = ROOT / "3rd-party-models" / "Blitzwing_EW" / "01_source"

# Check Tank FBX
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SRC_DIR / "H_shandian_G1_V1.fbx"))
print("\n--- Tank Objects ---")
for obj in bpy.data.objects:
    print(f"Tank obj: {obj.name} ({obj.type}), dims: {obj.dimensions}")
    if obj.type == 'MESH':
        print(f"  Materials: {[m.name for m in obj.data.materials if m]}")
        print(f"  Modifiers: {[m.name for m in obj.modifiers]}")

# Check Jet FBX
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SRC_DIR / "H_shandian_G1_V2.fbx"))
print("\n--- Jet Objects ---")
for obj in bpy.data.objects:
    print(f"Jet obj: {obj.name} ({obj.type}), dims: {obj.dimensions}")
    if obj.type == 'MESH':
        print(f"  Materials: {[m.name for m in obj.data.materials if m]}")
        print(f"  Modifiers: {[m.name for m in obj.modifiers]}")
