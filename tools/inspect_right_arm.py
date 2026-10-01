import bpy

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase2_inspect.blend")
arm = bpy.data.objects.get("Ironhide_Reference_Armature")
p_r_forearm = arm.pose.bones.get("RightForeArm")

for f in [0, 10, 20]:
    bpy.context.scene.frame_set(f)
    rh = arm.matrix_world @ p_r_forearm.tail
    re = arm.matrix_world @ p_r_forearm.head
    print(f"Frame {f:2d}: Right Elbow={re.y:.2f}(Y),{re.z:.2f}(Z)  Right Hand={rh.y:.2f}(Y),{rh.z:.2f}(Z)")
