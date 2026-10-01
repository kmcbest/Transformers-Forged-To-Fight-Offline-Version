import bpy
import math

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase2_inspect.blend")
arm = bpy.data.objects.get("Ironhide_Reference_Armature")
p_r_arm = arm.pose.bones.get("RightArm")
p_r_fa = arm.pose.bones.get("RightForeArm")

# Reset
p_r_arm.rotation_euler = (0, 0, 0)

for angle in [-60, -30, 0, 30, 60]:
    p_r_fa.rotation_euler = (math.radians(angle), 0, 0)
    bpy.context.view_layer.update()
    rh = arm.matrix_world @ p_r_fa.tail
    re = arm.matrix_world @ p_r_fa.head
    # Check if hand is forward (+Y) or backward (-Y) of elbow:
    delta_y = rh.y - re.y
    print(f"RightForeArm rot_x = {angle:+3d} deg: Hand Y - Elbow Y = {delta_y:+.3f} ({'FORWARD (Flexed)' if delta_y > 0 else 'BACKWARD (Hyperextended)' if delta_y < 0 else 'Straight'})")
