import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import os
from pathlib import Path
import math
import bpy
from mathutils import Vector, Matrix, Quaternion, Euler

ROOT = Path("E:/Agent/TFTF-blender")
bpy.ops.wm.read_factory_settings(use_empty=True)

fbx_path = ROOT / "3rd-party-models/Blitzwing_EW/01_source/H_shandian_G1_M_LOD.fbx"
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

mesh_obj = bpy.data.objects['H_shandian_G1_M_Lod']
arm_obj = bpy.data.objects['floor']

# Unparent
bpy.ops.object.select_all(action='DESELECT')
for o in [mesh_obj, arm_obj]:
    o.select_set(True)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
for o in list(bpy.data.objects):
    if o not in [mesh_obj, arm_obj]:
        bpy.data.objects.remove(o, do_unlink=True)

bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='POSE')

# In rest pose, check Finger1 bones
for bname in ["Bip001 L Finger1", "Bip001 L Finger11", "Bip001 L Finger12"]:
    pb = arm_obj.pose.bones[bname]
    print(f"PoseBone {bname}:")
    print(f"  matrix in arm space: {pb.matrix.translation}")
    print(f"  bone.matrix_local: {pb.bone.matrix_local.translation}")

# Check vertex group Bip001 L Finger12
vg = mesh_obj.vertex_groups.get("Bip001 L Finger12")
v_indices = [v.index for v in mesh_obj.data.vertices if any(g.group == vg.index and g.weight > 0.5 for g in v.groups)]
print(f"Bip001 L Finger12 vertex count: {len(v_indices)}")

# Check effect of rotating Bip001 L Finger1 by +45 deg around local X, Y, Z
pb1 = arm_obj.pose.bones["Bip001 L Finger1"]
pb1.rotation_mode = 'XYZ'

# Let's inspect local axes of bone relative to Hand
pb_hand = arm_obj.pose.bones["Bip001 L Hand"]
print("Hand matrix_local:")
for r in pb_hand.bone.matrix_local.to_3x3():
    print(f"  ({r[0]:.3f}, {r[1]:.3f}, {r[2]:.3f})")

print("Finger1 matrix_local:")
for r in pb1.bone.matrix_local.to_3x3():
    print(f"  ({r[0]:.3f}, {r[1]:.3f}, {r[2]:.3f})")

# In 3ds Max Biped:
# For fingers, the bending/curling axis is typically local Z or local X.
# Let's test rotating around local X, Y, Z on pb1, pb11, pb12
for ax_idx, ax_name in enumerate(["X", "Y", "Z"]):
    for ang in [45, -45]:
        pb1.rotation_euler = (0, 0, 0)
        euler = [0, 0, 0]
        euler[ax_idx] = math.radians(ang)
        pb1.rotation_euler = Euler(euler, 'XYZ')
        bpy.context.view_layer.update()
        
        # Where does Finger1 tail go?
        tail_w = arm_obj.matrix_world @ pb1.tail
        head_w = arm_obj.matrix_world @ pb1.head
        diff = tail_w - head_w
        print(f"Axis {ax_name} {ang:+} deg: Finger1 vector = ({diff.x:.4f}, {diff.y:.4f}, {diff.z:.4f})")
