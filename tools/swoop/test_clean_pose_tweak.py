import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Matrix, Vector, Quaternion
import math

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

arm = bpy.data.objects.get("Bip001")
swoop = bpy.data.objects.get("Swoop.001")

# Evaluate at idle01 frame 1
act = bpy.data.actions.get("Bip001|idle01|Base Layer")
if act and arm.animation_data:
    arm.animation_data.action = act
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()

# Record pose bone local matrices at frame 1
pose_matrices = {pb.name: pb.matrix_basis.copy() for pb in arm.pose.bones}

# Now clear animation data
arm.animation_data_clear()

# Restore pose matrices
for pb in arm.pose.bones:
    if pb.name in pose_matrices:
        pb.matrix_basis = pose_matrices[pb.name]
bpy.context.view_layer.update()

# Now we can rotate Bone_L_UpperArm / Forearm!
lua = arm.pose.bones.get("Bone_L_UpperArm")
lfa = arm.pose.bones.get("Bone_L_Forearm")
lh  = arm.pose.bones.get("Bone_L_Hand")

# Let's test rotating lua around its local Y or Z axis
# We can multiply pb.matrix_basis by a local rotation
R_out = Matrix.Rotation(math.radians(-35.0), 4, 'Z')
lua.matrix_basis = lua.matrix_basis @ R_out
bpy.context.view_layer.update()

scale = 340.16
w_lh = (arm.matrix_world @ lh.head) * scale
print(f"After -35 deg Z rot on L UpperArm: L_Hand pos = ({w_lh.x:+.2f}, {w_lh.y:+.2f}, {w_lh.z:+.2f})")

# Also rotate forearm slightly to straighten arm
R_fa = Matrix.Rotation(math.radians(-25.0), 4, 'Z')
lfa.matrix_basis = lfa.matrix_basis @ R_fa
bpy.context.view_layer.update()

w_lh2 = (arm.matrix_world @ lh.head) * scale
print(f"After -25 deg Z rot on L ForeArm:  L_Hand pos = ({w_lh2.x:+.2f}, {w_lh2.y:+.2f}, {w_lh2.z:+.2f})")
