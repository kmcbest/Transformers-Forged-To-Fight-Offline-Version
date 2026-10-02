import bpy
from pathlib import Path

BLEND = Path(r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend")

bpy.ops.wm.open_mainfile(filepath=str(BLEND))
scene = bpy.context.scene
scene.frame_set(11)
bpy.context.view_layer.update()

arcee_arm = bpy.data.objects.get("Arcee_Armature")
elita_arm = bpy.data.objects.get("Elita_One_Armature")

print(f"Arcee Armature Location: {arcee_arm.location}")
print(f"Elita Armature Location: {elita_arm.location}")

for name, arm in [("Arcee", arcee_arm), ("Elita", elita_arm)]:
    pb_l = arm.pose.bones.get("LeftHand")
    pb_r = arm.pose.bones.get("RightHand")
    w_l = arm.matrix_world @ pb_l.head
    w_r = arm.matrix_world @ pb_r.head
    print(f"\n{name} in Frame 11 (World Space):")
    print(f"  LeftHand:  {w_l}")
    print(f"  RightHand: {w_r}")
