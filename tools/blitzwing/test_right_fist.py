import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import math
import bpy
from mathutils import Vector, Matrix, Quaternion, Euler

ROOT = Path(r"E:\Agent\TFTF-blender")
SRC_DIR = ROOT / "3rd-party-models" / "Blitzwing_EW" / "01_source"
MEG_51_JSON = ROOT / "tools" / "blitzwing" / "megatron_51_authoritative_bindposes.json"
meg_51_data = json.loads(MEG_51_JSON.read_text(encoding="utf-8"))

def u_to_b(pos):
    return Vector((-float(pos[0]), -float(pos[2]), float(pos[1])))

meg_b_pos = {b: u_to_b(meg_51_data["bones"][b]["unity_world_pos"]) for b in meg_51_data["bones"]}

def pose_segment_world(arm_obj, bname, child_bname, target_head_w, target_end_w, thickness_scale=1.0, preserve_length=True):
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
    s_len = 1.0 if preserve_length else min(1.35, max(0.70, (len_targ / len_curr) if len_curr > 1e-5 else 1.0))

    d = v_curr.normalized() if len_curr > 1e-5 else Vector((0, 0, -1))
    S = Matrix.Identity(3) * thickness_scale
    for r in range(3):
        for c in range(3):
            S[r][c] += (s_len - thickness_scale) * d[r] * d[c]

    R_new = q_rot.to_matrix() @ S @ w_old.to_3x3()
    M_new_w = R_new.to_4x4()
    M_new_w.translation = target_head_w
    pb.matrix = arm_obj.matrix_world.inverted() @ M_new_w
    bpy.context.view_layer.update()

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SRC_DIR / "H_shandian_G1_M_LOD.fbx"))

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

# Transform
arm_obj.rotation_euler = (0, 0, math.radians(-90))
mesh_obj.rotation_euler = (0, 0, math.radians(-90))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.transform_apply(rotation=True)

min_z = min(v.co.z for v in mesh_obj.data.vertices)
mesh_obj.location.z -= min_z
arm_obj.location.z -= min_z
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

SCALE = 149.1728
mesh_obj.scale = (SCALE, SCALE, SCALE)
arm_obj.scale = (SCALE, SCALE, SCALE)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

mesh_obj.modifiers.clear()
mesh_obj.parent = arm_obj
arm_mod = mesh_obj.modifiers.new("Armature", "ARMATURE")
arm_mod.object = arm_obj

bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='POSE')

# Pose with preserve_length=True
for side, pfx in [("L", "Left"), ("R", "Right")]:
    sh_head = (arm_obj.matrix_world @ arm_obj.pose.bones[f"Bip001 {side} UpperArm"].matrix).translation.copy()
    elbow_targ = meg_b_pos[f"{pfx}ForeArm"]
    wrist_targ = meg_b_pos[f"{pfx}Hand"]

    pose_segment_world(arm_obj, f"Bip001 {side} UpperArm", f"Bip001 {side} Forearm", sh_head, elbow_targ, thickness_scale=1.0, preserve_length=True)
    pose_segment_world(arm_obj, f"Bip001 {side} Forearm", f"Bip001 {side} Hand", elbow_targ, wrist_targ, thickness_scale=1.0, preserve_length=True)

bpy.context.view_layer.update()

# Test Right hand
for sign in [1.0, -1.0]:
    for fi in range(1, 5):
        for seg in ["", "1", "2"]:
            pb = arm_obj.pose.bones[f"Bip001 R Finger{fi}{seg}"]
            pb.rotation_mode = 'XYZ'
            ang = sign * math.radians(45.0)
            pb.rotation_euler = Euler((0, 0, ang), 'XYZ')
    bpy.context.view_layer.update()
    
    pb_tip = arm_obj.pose.bones["Bip001 R Finger22"]
    pb_knuckle = arm_obj.pose.bones["Bip001 R Finger2"]
    kn_pos = arm_obj.matrix_world @ pb_knuckle.head
    tip_pos = arm_obj.matrix_world @ pb_tip.tail
    delta = tip_pos - kn_pos
    print(f"Right Hand Sign {sign:+.1f}: Finger2 base={kn_pos}, tip={tip_pos}, delta={delta}")
