import bpy

blend_path = r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

arm = bpy.data.objects.get("Arcee_Armature")
bpy.context.scene.frame_set(0)

for bname in ["LeftArm", "LeftArmRoll", "LeftForeArm", "LeftForeArmRoll", "LeftHand"]:
    pb = arm.pose.bones.get(bname)
    b = arm.data.bones.get(bname)
    print(f"{bname}: parent={b.parent.name if b.parent else None}")
    print(f"  edit_head={b.head_local}")
    print(f"  pose_mat_trans={pb.matrix.translation}")
    print(f"  pose_rot={pb.rotation_quaternion}")
