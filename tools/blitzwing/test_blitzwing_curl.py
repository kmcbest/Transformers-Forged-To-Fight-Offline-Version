import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Vector, Matrix, Quaternion, Euler
import math

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = "E:/Agent/TFTF-blender/3rd-party-models/Blitzwing_EW/01_source/H_shandian_G1_M_LOD.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

arm_obj = None
mesh_obj = None
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        arm_obj = obj
    elif obj.type == 'MESH':
        mesh_obj = obj

print("Armature:", arm_obj.name, "Mesh:", mesh_obj.name)

# Let's inspect Bip001 L Finger1 local axes and palm direction
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='POSE')

pb_hand = arm_obj.pose.bones.get("Bip001 L Hand")
pb_f1 = arm_obj.pose.bones.get("Bip001 L Finger1")
pb_f11 = arm_obj.pose.bones.get("Bip001 L Finger11")
pb_f12 = arm_obj.pose.bones.get("Bip001 L Finger12")

print("L Hand matrix_channel:", pb_hand.matrix)
print("L Finger1 matrix_channel:", pb_f1.matrix)

# In rest pose, what are the local axes in world space?
mat_f1 = arm_obj.matrix_world @ pb_f1.bone.matrix_local
print("Finger1 world local X:", mat_f1.to_3x3() @ Vector((1, 0, 0)))
print("Finger1 world local Y (bone axis):", mat_f1.to_3x3() @ Vector((0, 1, 0)))
print("Finger1 world local Z:", mat_f1.to_3x3() @ Vector((0, 0, 1)))

# Let's check vertices associated with Bip001 L Finger12
vg = mesh_obj.vertex_groups.get("Bip001 L Finger12")
if vg:
    v_indices = [v.index for v in mesh_obj.data.vertices if any(g.group == vg.index and g.weight > 0.5 for g in v.groups)]
    print(f"Bip001 L Finger12 has {len(v_indices)} vertices")
    avg_co = sum((mesh_obj.data.vertices[i].co for i in v_indices), Vector((0,0,0))) / len(v_indices)
    print("Avg vertex co in rest pose:", avg_co)

# Test rotations around local X, Y, Z
for axis_name, axis_vec in [("X", (1,0,0)), ("Y", (0,1,0)), ("Z", (0,0,1))]:
    for angle_deg in [45, -45]:
        pb_f1.rotation_mode = 'AXIS_ANGLE'
        pb_f1.rotation_axis_angle = (math.radians(angle_deg), axis_vec[0], axis_vec[1], axis_vec[2])
        bpy.context.view_layer.update()
        tail_pos = arm_obj.matrix_world @ pb_f1.tail
        print(f"Rotate {axis_name} {angle_deg:+} deg -> Finger1 tail pos = {tail_pos}")
