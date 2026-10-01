# -*- coding: utf-8 -*-
import bpy
import math
import mathutils
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BLEND_PATH = ROOT / "tools" / "demolishor" / "demolishor_phase2_inspect.blend"

bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))

arm_obj = bpy.data.objects.get("Ironhide_Reference_Armature")
mesh_obj = bpy.data.objects.get("cha_demolishor_gs_01")

print(f"Armature object: {arm_obj}")
print(f"Mesh object: {mesh_obj}")
print("Mesh modifier:", [(m.name, m.type, m.object.name if hasattr(m, 'object') and m.object else None) for m in mesh_obj.modifiers])

# Print actual bone names in armature
all_pbones = [b.name for b in arm_obj.pose.bones]
print("\n--- Armature Pose Bones Count:", len(all_pbones))
print("Sample bones:", all_pbones[:20])

# Clean old action
if arm_obj.animation_data:
    arm_obj.animation_data_clear()

arm_obj.animation_data_create()
act = bpy.data.actions.new(name="TF_Combat_Test_Action")
arm_obj.animation_data.action = act

bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 80
bpy.context.scene.frame_current = 1

def add_rot_key(bone_name, frame, euler_deg):
    pb = arm_obj.pose.bones.get(bone_name)
    if not pb:
        print(f"[!] Warning: Bone '{bone_name}' not found in pose bones!")
        return
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = mathutils.Euler((math.radians(euler_deg[0]), 
                                         math.radians(euler_deg[1]), 
                                         math.radians(euler_deg[2])), 'XYZ')
    pb.keyframe_insert(data_path="rotation_euler", frame=frame)

# Neutral pose at frame 1 and 80
bones_to_animate = ["Spine", "Spine1", "LeftArm", "RightArm", "LeftForeArm", "RightForeArm", "LeftUpLeg", "RightUpLeg"]
for b in bones_to_animate:
    add_rot_key(b, 1, (0, 0, 0))
    add_rot_key(b, 40, (0, 0, 0))
    add_rot_key(b, 80, (0, 0, 0))

# Frame 20: Left Punch + Torso Twist + Knee Bend
add_rot_key("Spine", 20, (0, 20, 15))
add_rot_key("LeftArm", 20, (-50, 25, 45))     # Left arm raises and swings forward
add_rot_key("LeftForeArm", 20, (0, 60, 0))     # Forearm punches forward
add_rot_key("RightArm", 20, (20, -10, -15))    # Right arm cocks back
add_rot_key("LeftUpLeg", 20, (15, 0, 0))       # Left leg steps
add_rot_key("RightUpLeg", 20, (-10, 0, 0))

# Frame 60: Right Punch + Opposite Torso Twist
add_rot_key("Spine", 60, (0, -20, -15))
add_rot_key("RightArm", 60, (-50, -25, -45))   # Right arm raises and swings forward
add_rot_key("RightForeArm", 60, (0, -60, 0))   # Forearm punches forward
add_rot_key("LeftArm", 60, (20, 10, 15))       # Left arm cocks back
add_rot_key("RightUpLeg", 60, (15, 0, 0))      # Right leg steps
add_rot_key("LeftUpLeg", 60, (-10, 0, 0))

print("[✓] Successfully injected 80-frame dynamic combat action with valid bone keys!")

# Also ensure autoexec script is active
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
print("[✓] Saved to:", BLEND_PATH)
