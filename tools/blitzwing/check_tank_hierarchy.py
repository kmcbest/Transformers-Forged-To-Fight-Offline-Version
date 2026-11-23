import sys
from pathlib import Path
import bpy

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
SRC_DIR = ROOT / "3rd-party-models" / "Blitzwing_EW" / "01_source"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SRC_DIR / "H_shandian_G1_V1.fbx"))
print("Tank root objects:")
for o in bpy.data.objects:
    if o.parent is None:
        print(f"  Root: {o.name} ({o.type}), loc={o.location}, rot={o.rotation_euler}")
    else:
        print(f"  Child: {o.name} -> Parent: {o.parent.name}, loc={o.location}, rot={o.rotation_euler}")
