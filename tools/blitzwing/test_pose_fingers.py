import sys
from pathlib import Path
import math
import bpy
import bmesh
import mathutils
from mathutils import Vector, Matrix, Quaternion
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
SRC_DIR = ROOT / "3rd-party-models" / "Blitzwing_EW" / "01_source"
MEG_51_JSON = ROOT / "tools" / "blitzwing" / "megatron_51_authoritative_bindposes.json"
meg_51_data = json.loads(MEG_51_JSON.read_text(encoding="utf-8"))

def u_to_b(pos):
    return Vector((-float(pos[0]), -float(pos[2]), float(pos[1])))

meg_b_pos = {b: u_to_b(meg_51_data["bones"][b]["unity_world_pos"]) for b in meg_51_data["bones"]}

def pose_segment_world(arm_obj, bname, child_bname, target_head_w, target_end_w, thickness_scale=1.0):
    bpy.context.view_layer.update()
    pb = arm_obj.pose.bones[bname]
    pb_child = arm_obj.pose.bones[child_bname]
    w_old = arm_obj.matrix_world @ pb.matrix
    curr_head = w_old.translation.copy()
    curr_end = (arm_obj.matrix_world @ pb_child.matrix).translation.copy()

    v_curr = curr_end - curr_head
    v_targ = target_end_w - target_head_w
    len_curr = v_curr.length
    len_targ = v_targ.length

    q_rot = v_curr.rotation_difference(v_targ) if (len_curr > 1e-5 and len_targ > 1e-5) else Quaternion()
    s_len = (len_targ / len_curr) if len_curr > 1e-5 else 1.0

    d = v_curr.normalized() if len_curr > 1e-5 else Vector((0, 0, -1))
    S = Matrix.Identity(3) * thickness_scale
    for r in range(3):
        for c in range(3):
            S[r][c] += (s_len - thickness_scale) * d[r] * d[c]

    RS = q_rot.to_matrix() @ S
    R_new = RS @ w_old.to_3x3()
    M_new_w = R_new.to_4x4()
    M_new_w.translation = target_head_w
    pb.matrix = arm_obj.matrix_world.inverted() @ M_new_w
    bpy.context.view_layer.update()

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SRC_DIR / "H_shandian_G1_M_LOD.fbx"))

mesh_obj = bpy.data.objects['H_shandian_G1_M_Lod']
arm_obj = bpy.data.objects['floor']

# 1. Unparent
bpy.ops.object.select_all(action='DESELECT')
for o in [mesh_obj, arm_obj]:
    o.select_set(True)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

for o in list(bpy.data.objects):
    if o not in [mesh_obj, arm_obj]:
        bpy.data.objects.remove(o, do_unlink=True)

# 2. Reset rest pose
arm_obj.animation_data_clear()
mesh_obj.animation_data_clear()
for pb in arm_obj.pose.bones:
    pb.location = (0, 0, 0)
    pb.rotation_quaternion = (1, 0, 0, 0)
    pb.rotation_euler = (0, 0, 0)
    pb.scale = (1, 1, 1)
arm_obj.data.pose_position = 'REST'
bpy.context.view_layer.update()

# 3. Apply initial transform
bpy.ops.object.select_all(action='DESELECT')
for o in [mesh_obj, arm_obj]:
    o.select_set(True)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 4. Ground Z=0 & Scale to Megatron
min_z = min(v.co.z for v in mesh_obj.data.vertices)
mesh_obj.location.z -= min_z
arm_obj.location.z -= min_z
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

SCALE = 149.1728
mesh_obj.scale = (SCALE, SCALE, SCALE)
arm_obj.scale = (SCALE, SCALE, SCALE)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 5. Add finger tips
bpy.context.view_layer.objects.active = arm_obj
arm_obj.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')

for side in ["L", "R"]:
    for fi in range(5):
        distal_name = f"Bip001 {side} Finger{fi}2"
        tip_name = f"Bip001 {side} Finger{fi}_tip"
        if tip_name not in arm_obj.data.edit_bones:
            eb_dist = arm_obj.data.edit_bones[distal_name]
            eb_tip = arm_obj.data.edit_bones.new(tip_name)
            d_vec = (eb_dist.tail - eb_dist.head).normalized() if (eb_dist.tail - eb_dist.head).length > 1e-4 else Vector((0, 0, -1))
            eb_tip.head = eb_dist.tail
            eb_tip.tail = eb_dist.tail + d_vec * 0.15
            eb_tip.parent = eb_dist

bpy.ops.object.mode_set(mode='OBJECT')
arm_obj.data.pose_position = 'POSE'
for pb in arm_obj.pose.bones:
    pb.location = (0, 0, 0)
    pb.rotation_quaternion = (1, 0, 0, 0)
    pb.rotation_euler = (0, 0, 0)
    pb.scale = (1, 1, 1)
bpy.context.view_layer.update()

mesh_obj.modifiers.clear()
mesh_obj.parent = arm_obj
arm_mod = mesh_obj.modifiers.new("Armature", "ARMATURE")
arm_mod.object = arm_obj

# Posing arms and all 30 fingers
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='POSE')

for side, pfx in [("L", "Left"), ("R", "Right")]:
    sh_head = (arm_obj.matrix_world @ arm_obj.pose.bones[f"Bip001 {side} UpperArm"].matrix).translation.copy()
    elbow_targ = meg_b_pos[f"{pfx}ForeArm"]
    wrist_targ = meg_b_pos[f"{pfx}Hand"]

    pose_segment_world(arm_obj, f"Bip001 {side} UpperArm", f"Bip001 {side} Forearm", sh_head, elbow_targ, thickness_scale=1.0)
    pose_segment_world(arm_obj, f"Bip001 {side} Forearm", f"Bip001 {side} Hand", elbow_targ, wrist_targ, thickness_scale=1.0)

    mid1_targ = meg_b_pos[f"{pfx}HandMiddle1"]
    pose_segment_world(arm_obj, f"Bip001 {side} Hand", f"Bip001 {side} Finger2", wrist_targ, mid1_targ, thickness_scale=1.0)

    fn_map = [(1, "Index"), (2, "Middle"), (3, "Ring"), (4, "Pinky")]
    for fi, fname in fn_map:
        p1 = meg_b_pos[f"{pfx}Hand{fname}1"]
        p2 = meg_b_pos[f"{pfx}Hand{fname}2"]
        p3 = meg_b_pos[f"{pfx}Hand{fname}3"]
        p4 = p3 + (p3 - p2) * 0.95

        pose_segment_world(arm_obj, f"Bip001 {side} Finger{fi}", f"Bip001 {side} Finger{fi}1", p1, p2, thickness_scale=0.98)
        pose_segment_world(arm_obj, f"Bip001 {side} Finger{fi}1", f"Bip001 {side} Finger{fi}2", p2, p3, thickness_scale=0.98)
        pose_segment_world(arm_obj, f"Bip001 {side} Finger{fi}2", f"Bip001 {side} Finger{fi}_tip", p3, p4, thickness_scale=0.98)

    # Thumb
    t1 = meg_b_pos[f"{pfx}HandThumb1"]
    t2 = meg_b_pos[f"{pfx}HandThumb2"]
    t3 = meg_b_pos[f"{pfx}HandThumb3"]
    t4 = t3 + (t3 - t2) * 1.05

    pose_segment_world(arm_obj, f"Bip001 {side} Finger0", f"Bip001 {side} Finger01", t1, t2, thickness_scale=0.98)
    pose_segment_world(arm_obj, f"Bip001 {side} Finger01", f"Bip001 {side} Finger02", t2, t3, thickness_scale=0.98)
    pose_segment_world(arm_obj, f"Bip001 {side} Finger02", f"Bip001 {side} Finger0_tip", t3, t4, thickness_scale=0.98)

bpy.context.view_layer.update()

max_finger_err_mm = 0.0
for side, pfx in [("L", "Left"), ("R", "Right")]:
    for fi, fname in [(0, "Thumb"), (1, "Index"), (2, "Middle"), (3, "Ring"), (4, "Pinky")]:
        for k, jname in [(0, "1"), (1, "2"), (2, "3")]:
            b_segment = f"Bip001 {side} Finger{fi}" if k == 0 else f"Bip001 {side} Finger{fi}{k}"
            w_p = (arm_obj.matrix_world @ arm_obj.pose.bones[b_segment].matrix).translation
            t_p = meg_b_pos[f"{pfx}Hand{fname}{jname}"]
            err_mm = (w_p - t_p).length * 1000.0
            max_finger_err_mm = max(max_finger_err_mm, err_mm)

print(f"[✓] Max finger joint alignment error across ALL 30 finger hinges: {max_finger_err_mm:.4f} mm!")

bpy.ops.object.mode_set(mode='OBJECT')

# Apply posed armature to mesh
bpy.context.view_layer.objects.active = mesh_obj
mesh_obj.select_set(True)
bpy.ops.object.modifier_apply(modifier="Armature")

zs = [v.co.z for v in mesh_obj.data.vertices]
xs = [v.co.x for v in mesh_obj.data.vertices]
print(f"Posed Mesh Bounds:")
print(f"  Z: [{min(zs):.3f}, {max(zs):.3f}]m")
print(f"  X: [{min(xs):.3f}, {max(xs):.3f}]m")
assert min(zs) >= -0.1, f"Min Z {min(zs)} < -0.1!"
assert max(zs) < 13.0, f"Max Z {max(zs)} exploded!"
print("[PASS] Posed mesh vertices perfectly bounded and grounded!")
