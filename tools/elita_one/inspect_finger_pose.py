import bpy
import mathutils

blend_path = r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

arm = bpy.data.objects.get("Arcee_Armature")
bpy.context.scene.frame_set(0)

for bname in ["LeftForeArmRoll", "LeftHand", "LeftHandIndex1", "LeftHandIndex2", "LeftHandIndex3"]:
    pb = arm.pose.bones.get(bname)
    b = arm.data.bones.get(bname)
    print(f"Bone {bname}:")
    print(f"  parent in edit bone: {b.parent.name if b.parent else None}")
    print(f"  edit head: {b.head_local}")
    print(f"  pose matrix translation: {pb.matrix.translation}")
    print(f"  pose rot quat: {pb.rotation_quaternion}")
