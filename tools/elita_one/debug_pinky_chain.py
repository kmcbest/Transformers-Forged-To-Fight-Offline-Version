import json
import bpy
import mathutils
from pathlib import Path

BLEND = Path(r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend")

bpy.ops.wm.open_mainfile(filepath=str(BLEND))
scene = bpy.context.scene
scene.frame_set(0)
bpy.context.view_layer.update()

arcee_arm = bpy.data.objects.get("Arcee_Armature")
elita_arm = bpy.data.objects.get("Elita_One_Armature")

# Let's inspect the hierarchy and pose of LeftHandPinky1, LeftHandPinky2
for bname in ["LeftHand", "LeftHandPinky1", "LeftHandPinky2", "LeftHandPinky3"]:
    pb = arcee_arm.pose.bones.get(bname)
    eb = arcee_arm.data.bones.get(bname)
    print(f"\n{bname}:")
    print(f"  Parent: {eb.parent.name if eb.parent else None}")
    print(f"  Head: {eb.head_local}")
    print(f"  Pose rot quat: {pb.rotation_quaternion}")
    print(f"  Pose head in arm space: {pb.head}")
    print(f"  Matrix in arm space:\n{pb.matrix}")
