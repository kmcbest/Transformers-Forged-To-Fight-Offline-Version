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

# In brawl_ARM, let's see rest positions of L arm
# In FBX coords (X=forward, Y=left/right, Z=up):
# bip_upperArm_L head: (-0.2001, -18.4691, 4.8762) relative to scene (-19.6191) -> Y=+1.1500, Z=4.8762
# bip_lowerArm_L head: (-0.2441, -17.8222, 4.0801) -> Y=+1.7969, Z=4.0801
# bip_hand_L head: (0.1048, -17.0529, 3.1329) -> Y=+2.5662, Z=3.1329

# Target Megatron in FBX space (before conversion):
# In Unity space:
# Meg LeftArm: (-2.4734, 9.4803, -0.0470)
# Meg LeftForeArm: (-2.4734, 7.6254, -0.0470)
# Meg LeftHand: (-2.4734, 5.5272, -0.0470)

# With SCALE ~ 2.04:
# Target Y in raw FBX: -(-2.4734 / 2.04) = +1.212
# That means in raw FBX, Y should be ~ -18.407!
# Notice: Megatron's arm is almost directly below the shoulder in Y (shoulder Y=+1.15, hand Y=+1.21)!
# But in Brawl: shoulder Y=+1.15, elbow Y=+1.80, hand Y=+2.57!
# So the arm needs to be rotated inward around the X-axis (or local bone axis) to bring the elbow and hand from Y=+2.57 to Y=+1.21!

pb_u = armature.pose.bones["bip_upperArm_L"]
print("Initial upper arm rotation_mode:", pb_u.rotation_mode)
print("Initial upper arm rotation:", pb_u.rotation_euler if pb_u.rotation_mode == 'XYZ' else pb_u.rotation_quaternion)

# Let's inspect bone axes:
print("Bone matrix:", pb_u.matrix)
print("Bone vector (tail - head):", pb_u.tail - pb_u.head)
