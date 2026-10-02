import bpy
import mathutils

blend_path = r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

arcee_arm = bpy.data.objects.get("Arcee_Armature")
elita_arm = bpy.data.objects.get("Elita_One_Armature")

print("Arcee Armature edit bone heads:")
for bname in ["Reference", "Hips", "Spine", "Head", "LeftArm", "LeftHand", "LeftFoot"]:
    b = arcee_arm.data.bones.get(bname)
    if b:
        print(f"  {bname}: head={b.head}")

print("\nPose bone locations and matrices at frame 0:")
bpy.context.scene.frame_set(0)
for bname in ["Hips", "LeftArm", "LeftHand"]:
    pb = arcee_arm.pose.bones.get(bname)
    if pb:
        print(f"  Arcee {bname}: loc={pb.location}, matrix_translation={(arcee_arm.matrix_world @ pb.matrix).translation}")
    pb_e = elita_arm.pose.bones.get(bname)
    if pb_e:
        print(f"  Elita {bname}: loc={pb_e.location}, matrix_translation={(elita_arm.matrix_world @ pb_e.matrix).translation}")
