import bpy
import math

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase2_inspect.blend")
arm = bpy.data.objects.get("Ironhide_Reference_Armature")
p_l_fa = arm.pose.bones.get("LeftForeArm")

for angle in [-60, -30, 0, 30, 60]:
    p_l_fa.rotation_euler = (math.radians(angle), 0, 0)
    bpy.context.view_layer.update()
    lh = arm.matrix_world @ p_l_fa.tail
    le = arm.matrix_world @ p_l_fa.head
    delta_y = lh.y - le.y
    print(f"LeftForeArm rot_x = {angle:+3d} deg: Hand Y - Elbow Y = {delta_y:+.3f} ({'FORWARD (Flexed)' if delta_y > 0 else 'BACKWARD (Hyperextended)' if delta_y < 0 else 'Straight'})")
