import bpy
import math

BLEND_PATH = "tools/demolishor/demolishor_phase2_inspect.blend"
bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)

arm = bpy.data.objects.get("Ironhide_Reference_Armature")
action = arm.animation_data.action

def set_bone_kf(bone_name, frame, rx, ry, rz):
    pbone = arm.pose.bones.get(bone_name)
    if not pbone: return
    pbone.rotation_mode = 'XYZ'
    pbone.rotation_euler = (math.radians(rx), math.radians(ry), math.radians(rz))
    pbone.keyframe_insert(data_path="rotation_euler", frame=frame)

# Check all bones we want to animate for natural full-body running:
# In running:
# Hips: rotates slightly in Z (yaw) to follow the leading leg, slight pitch forward (X ~ 5 deg)
# Spine / Spine1: twists in Z opposite to hips (counter-rotation), slight pitch
# LeftShoulder / RightShoulder / Pads: subtle dynamic tilt

spine_kfs = [
    # Frame 0: Rest pose
    (0, "Hips", 0, 0, 0),
    (0, "Spine", 0, 0, 0),
    (0, "Spine1", 0, 0, 0),
    (0, "LeftShoulder", 0, 0, 0),
    (0, "RightShoulder", 0, 0, 0),
    (0, "LeftShoulderPad", 0, 0, 0),
    (0, "RightShoulderPad", 0, 0, 0),

    # Frame 10: Left leg forward, Right arm forward
    # Hips yaw left (+4 deg Z), Spine yaw right (-6 deg Z), pitch forward (X +4 deg)
    (10, "Hips", 4, 0, 4),
    (10, "Spine", 3, 0, -4),
    (10, "Spine1", 2, 0, -4),
    (10, "LeftShoulder", -3, 0, 0),
    (10, "RightShoulder", 5, 0, 0),
    (10, "LeftShoulderPad", -4, 0, 0),
    (10, "RightShoulderPad", 8, 0, 0),

    # Frame 30: Passing pose
    (30, "Hips", 2, 0, 0),
    (30, "Spine", 2, 0, 0),
    (30, "Spine1", 1, 0, 0),
    (30, "LeftShoulder", 0, 0, 0),
    (30, "RightShoulder", 0, 0, 0),
    (30, "LeftShoulderPad", 0, 0, 0),
    (30, "RightShoulderPad", 0, 0, 0),

    # Frame 50: Right leg forward, Left arm forward
    # Hips yaw right (-4 deg Z), Spine yaw left (+6 deg Z), pitch forward
    (50, "Hips", 4, 0, -4),
    (50, "Spine", 3, 0, 4),
    (50, "Spine1", 2, 0, 4),
    (50, "LeftShoulder", 5, 0, 0),
    (50, "RightShoulder", -3, 0, 0),
    (50, "LeftShoulderPad", 8, 0, 0),
    (50, "RightShoulderPad", -4, 0, 0),

    # Frame 70: Passing pose
    (70, "Hips", 2, 0, 0),
    (70, "Spine", 2, 0, 0),
    (70, "Spine1", 1, 0, 0),
    (70, "LeftShoulder", 0, 0, 0),
    (70, "RightShoulder", 0, 0, 0),
    (70, "LeftShoulderPad", 0, 0, 0),
    (70, "RightShoulderPad", 0, 0, 0),

    # Frame 90: Loop back to frame 10
    (90, "Hips", 4, 0, 4),
    (90, "Spine", 3, 0, -4),
    (90, "Spine1", 2, 0, -4),
    (90, "LeftShoulder", -3, 0, 0),
    (90, "RightShoulder", 5, 0, 0),
    (90, "LeftShoulderPad", -4, 0, 0),
    (90, "RightShoulderPad", 8, 0, 0),
]

for frame, bname, rx, ry, rz in spine_kfs:
    set_bone_kf(bname, frame, rx, ry, rz)

for fc in action.fcurves:
    for kf in fc.keyframe_points:
        kf.interpolation = 'BEZIER'

bpy.ops.wm.save_mainfile(filepath=BLEND_PATH)
print("[✓] Added natural spine twist and shoulder dynamics to action!")
