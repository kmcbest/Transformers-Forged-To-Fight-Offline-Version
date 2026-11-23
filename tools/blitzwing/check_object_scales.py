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
bpy.ops.import_scene.fbx(filepath=str(SRC_DIR / "H_shandian_G1_M_LOD.fbx"))

for o in bpy.data.objects:
    print(f"Object: {o.name:24s} | Parent: {o.parent.name if o.parent else 'NONE':20s} | Loc: {o.location} | Scale: {o.scale} | MatrixScale: {o.matrix_world.to_scale()}")
