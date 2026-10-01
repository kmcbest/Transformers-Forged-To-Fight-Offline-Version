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

all_animated_bones = ["Hips", "LeftUpLeg", "LeftLeg", "RightUpLeg", "RightLeg", "LeftArm", "LeftForeArm", "RightArm", "RightForeArm"]

# Clear existing curves
action.fcurves.clear()

# Frame 0: Rest pose
for bname in all_animated_bones:
    set_bone_kf(bname, 0, 0, 0, 0)

# Stride cycle with CORRECT POSITIVE FOREARM ROTATION (Forward Flex):
# When LeftArm is forward (-38 deg X), LeftForeArm flexes (+45 deg X)
# When RightArm is back (+38 deg X), RightForeArm is slightly flexed (+20 deg X)
stride_kfs = [
    # Frame 10: Left Leg forward, Right Leg back, Right Arm forward, Left Arm back
    (10, "LeftUpLeg", 42, 0, 0),
    (10, "LeftLeg", -55, 0, 0),
    (10, "RightUpLeg", -25, 0, 0),
    (10, "RightLeg", -10, 0, 0),
    (10, "LeftArm", -38, 0, 0),
    (10, "LeftForeArm", 25, 0, 0),   # Natural arm swing back with forearm slightly bent forward
    (10, "RightArm", 38, 0, 0),
    (10, "RightForeArm", 55, 0, 0),  # Forward arm with forearm flexed towards chest!

    # Frame 30: Passing pose
    (30, "LeftUpLeg", 0, 0, 0),
    (30, "LeftLeg", -25, 0, 0),
    (30, "RightUpLeg", 0, 0, 0),
    (30, "RightLeg", -25, 0, 0),
    (30, "LeftArm", 0, 0, 0),
    (30, "LeftForeArm", 30, 0, 0),
    (30, "RightArm", 0, 0, 0),
    (30, "RightForeArm", 30, 0, 0),

    # Frame 50: Right Leg forward, Left Leg back, Left Arm forward, Right Arm back
    (50, "LeftUpLeg", -25, 0, 0),
    (50, "LeftLeg", -10, 0, 0),
    (50, "RightUpLeg", 42, 0, 0),
    (50, "RightLeg", -55, 0, 0),
    (50, "LeftArm", 38, 0, 0),
    (50, "LeftForeArm", 55, 0, 0),   # Forward arm with forearm flexed towards chest!
    (50, "RightArm", -38, 0, 0),
    (50, "RightForeArm", 25, 0, 0),  # Natural arm swing back

    # Frame 70: Passing pose
    (70, "LeftUpLeg", 0, 0, 0),
    (70, "LeftLeg", -25, 0, 0),
    (70, "RightUpLeg", 0, 0, 0),
    (70, "RightLeg", -25, 0, 0),
    (70, "LeftArm", 0, 0, 0),
    (70, "LeftForeArm", 30, 0, 0),
    (70, "RightArm", 0, 0, 0),
    (70, "RightForeArm", 30, 0, 0),

    # Frame 90: Loop back to Frame 10
    (90, "LeftUpLeg", 42, 0, 0),
    (90, "LeftLeg", -55, 0, 0),
    (90, "RightUpLeg", -25, 0, 0),
    (90, "RightLeg", -10, 0, 0),
    (90, "LeftArm", -38, 0, 0),
    (90, "LeftForeArm", 25, 0, 0),
    (90, "RightArm", 38, 0, 0),
    (90, "RightForeArm", 55, 0, 0),
]

for frame, bname, rx, ry, rz in stride_kfs:
    set_bone_kf(bname, frame, rx, ry, rz)

# Smooth interpolation
for fc in action.fcurves:
    for kf in fc.keyframe_points:
        kf.interpolation = 'BEZIER'

bpy.context.scene.frame_start = 0
bpy.context.scene.frame_end = 90
bpy.context.scene.frame_current = 0

bpy.ops.wm.save_mainfile(filepath=BLEND_PATH)
print(f"[✓] Saved corrected animation to {BLEND_PATH}")
