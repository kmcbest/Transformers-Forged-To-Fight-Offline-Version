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

# Let's inspect bip_upperArm_L in rest pose vs after rotation
pb_u = armature.pose.bones["bip_upperArm_L"]
pb_l = armature.pose.bones["bip_lowerArm_L"]
pb_h = armature.pose.bones["bip_hand_L"]

bpy.context.view_layer.update()
print("Rest Head bip_upperArm_L:", pb_u.head)
print("Rest Head bip_lowerArm_L:", pb_l.head)
print("Rest Head bip_hand_L    :", pb_h.head)

# In raw FBX coords:
# UpperArm head: (-0.2001, 1.1501, 4.8762) relative to scene (-19.6191)
# LowerArm head: (-0.2441, 1.7969, 4.0801)
# Hand head:     ( 0.1048, 2.5662, 3.1329)

# Notice the arm vector is pointing (+Y, -Z)
# We want it to point (0 Y, -Z)
# What is the angle in YZ plane?
dy = 1.7969 - 1.1501  # 0.6468
dz = 4.0801 - 4.8762  # -0.7961
angle_rad = math.atan2(dy, -dz)
angle_deg = math.degrees(angle_rad)
print(f"Current upper arm outward angle in YZ: {angle_deg:.2f} degrees")

# Let's see what happens if we rotate bip_upperArm_L by -angle_rad around bone's local axis or world X axis!
