import bpy
import math

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase2_inspect.blend")
arm = bpy.data.objects.get("Ironhide_Reference_Armature")
p_l_leg = arm.pose.bones.get("LeftLeg")

for angle in [-60, -30, 0, 30, 60]:
    p_l_leg.rotation_euler = (math.radians(angle), 0, 0)
    bpy.context.view_layer.update()
    foot = arm.matrix_world @ p_l_leg.tail
    knee = arm.matrix_world @ p_l_leg.head
    delta_y = foot.y - knee.y
    print(f"LeftLeg (Knee) rot_x = {angle:+3d} deg: Foot Y - Knee Y = {delta_y:+.3f} ({'Kicked Back (Natural)' if delta_y < 0 else 'Kicked Forward (Hyperextended)' if delta_y > 0 else 'Straight'})")
