import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(r"E:\Agent\TFTF-blender")
BLEND_SRC = ROOT / "3rd-party-models" / "blitzwing_extracted" / "rar" / "Blitzwing.blend"

bpy.ops.wm.open_mainfile(filepath=str(BLEND_SRC))
arm_obj = bpy.data.objects['Blitzwing_Skeleton']

print("=== Blitzwing.blend Thumb Edit Bones ===")
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='EDIT')

for side in ["L", "R"]:
    print(f"\n--- Side: {side} ---")
    for bname in [f"Bip01_{side}_Hand", f"Bip01_{side}_Finger0", f"Bip01_{side}_Finger01", f"Bip01_{side}_Finger02", f"Bip01_{side}_Finger1", f"Bip01_{side}_Finger11", f"Bip01_{side}_Finger12"]:
        if bname in arm_obj.data.edit_bones:
            eb = arm_obj.data.edit_bones[bname]
            p = eb.parent.name if eb.parent else "None"
            vec = eb.tail - eb.head
            print(f"EditBone '{bname:20s}' (parent={p:15s}): head={eb.head.to_tuple(3)} tail={eb.tail.to_tuple(3)} vec={vec.to_tuple(3)} roll={eb.roll:.2f}")
