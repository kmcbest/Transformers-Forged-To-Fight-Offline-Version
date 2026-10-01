import bpy
import math

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase2_inspect.blend")
arm = bpy.data.objects.get("Ironhide_Reference_Armature")

p_l_arm = arm.pose.bones.get("LeftArm")
p_l_forearm = arm.pose.bones.get("LeftForeArm")
p_r_arm = arm.pose.bones.get("RightArm")
p_r_forearm = arm.pose.bones.get("RightForeArm")

print("--- Testing Frame 10 Pose ---")
bpy.context.scene.frame_set(10)
print(f"LeftArm rot: {p_l_arm.rotation_euler}")
print(f"LeftForeArm rot: {p_l_forearm.rotation_euler}")
print(f"RightArm rot: {p_r_arm.rotation_euler}")
print(f"RightForeArm rot: {p_r_forearm.rotation_euler}")

# Check hand and elbow positions in world space at frame 0 and frame 10:
for f in [0, 10, 20]:
    bpy.context.scene.frame_set(f)
    lh = arm.matrix_world @ p_l_forearm.tail
    le = arm.matrix_world @ p_l_forearm.head
    print(f"Frame {f:2d}: Left Elbow={le.y:.2f}(Y),{le.z:.2f}(Z)  Left Hand={lh.y:.2f}(Y),{lh.z:.2f}(Z)")
