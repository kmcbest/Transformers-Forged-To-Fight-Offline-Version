import sys
from pathlib import Path
import bpy
from mathutils import Vector

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
SRC_DIR = ROOT / "3rd-party-models" / "Blitzwing_EW" / "01_source"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SRC_DIR / "H_shandian_G1_M_LOD.fbx"))

arm = bpy.data.objects.get("floor")
for b in arm.data.bones:
    if "Finger0" in b.name:
        print(f"Bone: {b.name:24s} | Head: {b.head_local} | Tail: {b.tail_local} | Length: {b.length}")
