import bpy

blend_path = r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

arcee_arm = bpy.data.objects.get("Arcee_Armature")
elita_arm = bpy.data.objects.get("Elita_One_Armature")

bpy.context.scene.frame_set(0)

for bname in ["Hips", "LeftArm", "LeftForeArm", "LeftHand", "RightArm", "RightForeArm", "RightHand"]:
    pb_a = arcee_arm.pose.bones.get(bname)
    pb_e = elita_arm.pose.bones.get(bname)
    print(f"Bone {bname}:")
    print(f"  Arcee rot: {pb_a.rotation_quaternion if pb_a else None}")
    print(f"  Elita rot: {pb_e.rotation_quaternion if pb_e else None}")
