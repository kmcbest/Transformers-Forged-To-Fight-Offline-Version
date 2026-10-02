import bpy
import math
import mathutils
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

arm = bpy.data.objects.get("SK_CH_11")
mesh = bpy.data.objects.get("SK_CH_11.001")

scale_s = 8.840 / 8.083
M_transform = mathutils.Matrix.Rotation(math.radians(90.0), 4, 'Z') @ mathutils.Matrix.Scale(scale_s, 4)

# Apply transform to armature and mesh data
arm.data.transform(M_transform)
mesh.data.transform(M_transform)

# Target Arcee wrists:
target_l_wrist = mathutils.Vector((-1.2848, -0.0372, 4.2729))
target_r_wrist = mathutils.Vector(( 1.2848, -0.0372, 4.2729))

# Current FBX shoulders and wrists:
l_sh = arm.data.bones.get("l_upperarm_skin").head_local
r_sh = arm.data.bones.get("r_upperarm_skin").head_local
l_wr = arm.data.bones.get("l_hand_skin").head_local
r_wr = arm.data.bones.get("r_hand_skin").head_local

print(f"L Shoulder: {l_sh}, L Wrist: {l_wr}")
print(f"R Shoulder: {r_sh}, R Wrist: {r_wr}")

v_l_curr = l_wr - l_sh
v_l_targ = target_l_wrist - l_sh
q_l = v_l_curr.rotation_difference(v_l_targ)

v_r_curr = r_wr - r_sh
v_r_targ = target_r_wrist - r_sh
q_r = v_r_curr.rotation_difference(v_r_targ)

print(f"L Arm adjustment quat: {q_l}, angle: {math.degrees(q_l.angle):.1f}°")
print(f"R Arm adjustment quat: {q_r}, angle: {math.degrees(q_r.angle):.1f}°")

# Let's test applying this pose to SK_CH_11
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')

pb_l = arm.pose.bones.get("l_upperarm_skin")
pb_r = arm.pose.bones.get("r_upperarm_skin")

# In pose bone local space:
# q_local = R_bone_rest.inverted() @ q_world @ R_bone_rest
R_l_rest = arm.data.bones.get("l_upperarm_skin").matrix_local.to_3x3()
q_l_local = (R_l_rest.inverted() @ q_l.to_matrix() @ R_l_rest).to_quaternion()
pb_l.rotation_quaternion = q_l_local

R_r_rest = arm.data.bones.get("r_upperarm_skin").matrix_local.to_3x3()
q_r_local = (R_r_rest.inverted() @ q_r.to_matrix() @ R_r_rest).to_quaternion()
pb_r.rotation_quaternion = q_r_local

bpy.context.view_layer.update()

# Check new wrist positions in pose
new_l_wr = pb_l.id_data.matrix_world @ arm.pose.bones.get("l_hand_skin").head
new_r_wr = pb_r.id_data.matrix_world @ arm.pose.bones.get("r_hand_skin").head

print(f"\nAfter pose adjustment:")
print(f"New L Wrist: {new_l_wr} (Target: {target_l_wrist}) -> Diff: {(new_l_wr - target_l_wrist).length:.3f}m")
print(f"New R Wrist: {new_r_wr} (Target: {target_r_wrist}) -> Diff: {(new_r_wr - target_r_wrist).length:.3f}m")
