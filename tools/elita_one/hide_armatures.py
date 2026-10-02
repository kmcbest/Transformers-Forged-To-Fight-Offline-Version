import bpy
from pathlib import Path

BLEND = Path(r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend")

bpy.ops.wm.open_mainfile(filepath=str(BLEND))

arcee_arm = bpy.data.objects.get("Arcee_Armature")
elita_arm = bpy.data.objects.get("Elita_One_Armature")

if arcee_arm:
    arcee_arm.hide_viewport = True
if elita_arm:
    elita_arm.hide_viewport = True

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
print("[OK] Hidden armatures in viewport and saved blend file!")
