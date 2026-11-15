import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import bpy
from mathutils import Vector, Matrix, Quaternion

ROOT = Path(r"E:\Agent\TFTF-blender")
BLEND_SRC = ROOT / "3rd-party-models" / "blitzwing_extracted" / "rar" / "Blitzwing.blend"
MEG_51_JSON = ROOT / "tools" / "blitzwing" / "megatron_51_authoritative_bindposes.json"
meg_51_data = json.loads(MEG_51_JSON.read_text(encoding="utf-8"))

def u_to_b(pos):
    return Vector((-float(pos[0]), -float(pos[2]), float(pos[1])))

meg_b_pos = {b: u_to_b(meg_51_data["bones"][b]["unity_world_pos"]) for b in meg_51_data["bones"]}

bpy.ops.wm.open_mainfile(filepath=str(BLEND_SRC))
mesh_obj = bpy.data.objects['Blitzwing']
arm_obj = bpy.data.objects['Blitzwing_Skeleton']

for o in list(bpy.data.objects):
    if o not in [mesh_obj, arm_obj]:
        bpy.data.objects.remove(o, do_unlink=True)

arm_obj.animation_data_clear()
mesh_obj.animation_data_clear()
for pb in arm_obj.pose.bones:
    pb.location = (0, 0, 0)
    pb.rotation_quaternion = (1, 0, 0, 0)
    pb.rotation_euler = (0, 0, 0)
    pb.scale = (1, 1, 1)

arm_obj.data.pose_position = 'REST'
bpy.context.view_layer.update()

SCALE = 1.4803
min_z = min(v.co.z for v in mesh_obj.data.vertices)
ground_scale_mat = Matrix.Scale(SCALE, 4) @ Matrix.Translation((0, 0, -min_z))
mesh_obj.data.transform(ground_scale_mat)
mesh_obj.data.update()

bpy.context.view_layer.objects.active = arm_obj
arm_obj.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')

for eb in arm_obj.data.edit_bones:
    eb.use_connect = False
    eb.head = (eb.head.x * SCALE, eb.head.y * SCALE, (eb.head.z - min_z) * SCALE)
    eb.tail = (eb.tail.x * SCALE, eb.tail.y * SCALE, (eb.tail.z - min_z) * SCALE)

for side in ["L", "R"]:
    for fi in range(5):
        distal_name = f"Bip01_{side}_Finger{fi}2"
        tip_name = f"Bip01_{side}_Finger{fi}_tip"
        if tip_name not in arm_obj.data.edit_bones:
            eb_dist = arm_obj.data.edit_bones[distal_name]
            eb_tip = arm_obj.data.edit_bones.new(tip_name)
            
            # For thumb (fi==0): eb_dist.tail is bogus horizontal!
            # Use true direction from parent bone head (Finger01) to Finger02!
            if fi == 0:
                eb_parent = arm_obj.data.edit_bones[f"Bip01_{side}_Finger01"]
                true_dir = (eb_dist.head - eb_parent.head).normalized()
                eb_tip.head = eb_dist.head + true_dir * 0.12 * SCALE
                eb_tip.tail = eb_tip.head + true_dir * 0.05 * SCALE
            else:
                dir_v = (eb_dist.tail - eb_dist.head).normalized() if (eb_dist.tail - eb_dist.head).length > 1e-4 else Vector((0, 0, -1))
                eb_tip.head = eb_dist.tail
                eb_tip.tail = eb_tip.head + dir_v * 0.10
            eb_tip.parent = eb_dist

bpy.ops.object.mode_set(mode='OBJECT')

arm_obj.data.pose_position = 'POSE'
for pb in arm_obj.pose.bones:
    pb.location = (0, 0, 0)
    pb.rotation_quaternion = (1, 0, 0, 0)
    pb.rotation_euler = (0, 0, 0)
    pb.scale = (1, 1, 1)
bpy.context.view_layer.update()

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

bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='POSE')

for side, pfx in [("L", "Left"), ("R", "Right")]:
    t1 = meg_b_pos[f"{pfx}HandThumb1"]
    t2 = meg_b_pos[f"{pfx}HandThumb2"]
    t3 = meg_b_pos[f"{pfx}HandThumb3"]
    t4 = t3 + (t3 - t2) * 1.05

    pose_segment_world(arm_obj, f"Bip01_{side}_Finger0", f"Bip01_{side}_Finger01", t1, t2, thickness_scale=0.98)
    pose_segment_world(arm_obj, f"Bip01_{side}_Finger01", f"Bip01_{side}_Finger02", t2, t3, thickness_scale=0.98)
    pose_segment_world(arm_obj, f"Bip01_{side}_Finger02", f"Bip01_{side}_Finger0_tip", t3, t4, thickness_scale=0.98)

print("\n=== Corrected Blitzwing Posed Thumb Bones ===")
for side, pfx in [("L", "Left"), ("R", "Right")]:
    for k in [0, "01", "02"]:
        bname = f"Bip01_{side}_Finger{k}"
        pb = arm_obj.pose.bones[bname]
        M = arm_obj.matrix_world @ pb.matrix
        print(f"\n{bname}:")
        print(f"  Head pos: {M.translation.to_tuple(3)}")
        print(f"  Col 0: {M.to_3x3()[0].to_tuple(3)}")
        print(f"  Col 1: {M.to_3x3()[1].to_tuple(3)}")
        print(f"  Col 2: {M.to_3x3()[2].to_tuple(3)}")
