import bpy
from pathlib import Path

BLEND = Path(r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend")

bpy.ops.wm.open_mainfile(filepath=str(BLEND))
scene = bpy.context.scene
scene.frame_set(7)
bpy.context.view_layer.update()

elita_arm = bpy.data.objects.get("Elita_One_Armature")
arcee_arm = bpy.data.objects.get("Arcee_Armature")

print("=== Bones in Elita_One_Armature in Frame 7 ===")
for pb in elita_arm.pose.bones:
    w_head = elita_arm.matrix_world @ pb.head
    # print if bone is vehicle chop or prop
    if any(k in pb.name for k in ["chop", "Prop", "Pistol", "sword", "Pinky", "Ring", "Middle", "Index", "Thumb"]):
        print(f"  {pb.name:32s}: World Head={w_head}")
