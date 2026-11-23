import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path("E:/Agent/TFTF-blender")
bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = ROOT / "3rd-party-models/Blitzwing_EW/01_source/H_shandian_G1_M_LOD.fbx"
bpy.ops.import_scene.fbx(filepath=str(fbx_path))
arm_obj = bpy.data.objects['floor']

for bname in ["Bip001 L Forearm", "Bip001 L Hand", "Bip001 R Forearm", "Bip001 R Hand"]:
    b = arm_obj.data.bones.get(bname)
    print(f"{bname}: head={b.head}, tail={b.tail}")
