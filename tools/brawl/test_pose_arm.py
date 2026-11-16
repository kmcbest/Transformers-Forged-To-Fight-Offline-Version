import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math
from mathutils import Vector, Matrix, Euler, Quaternion

fbx_path = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

armature = bpy.data.objects.get("brawl_ARM")
bpy.context.view_layer.objects.active = armature
bpy.ops.object.mode_set(mode='POSE')

pb_u = armature.pose.bones["bip_upperArm_L"]
pb_l = armature.pose.bones["bip_lowerArm_L"]
pb_h = armature.pose.bones["bip_hand_L"]

# Rotate upper arm in world X axis by -39.09 degrees:
# In armature space, bone matrix is M.
# To rotate around bone head by angle around X:
rot_mat = Matrix.Rotation(math.radians(-39.09), 4, 'X')

# Apply rotation to upper arm:
# pb.matrix = ...
# Or using rotation_quaternion:
# Let's find rotation difference:
curr_vec = pb_l.head - pb_u.head
target_vec = Vector((curr_vec.x, 0.0, -curr_vec.length))
q = curr_vec.rotation_difference(target_vec)

# World matrix of pb_u:
w_u = armature.matrix_world @ pb_u.matrix
head_u = w_u.translation.copy()

M_new = Matrix.Translation(head_u) @ q.to_matrix().to_4x4() @ Matrix.Translation(-head_u) @ w_u
pb_u.matrix = armature.matrix_world.inverted() @ M_new

bpy.context.view_layer.update()

print("Posed Head bip_upperArm_L:", pb_u.head)
print("Posed Head bip_lowerArm_L:", pb_l.head)
print("Posed Head bip_hand_L    :", pb_h.head)
