import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import math
import mathutils
import bpy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"
REST_JSON = ROOT / "tools" / "elita_one" / "arcee_unity_rest_matrices.json"
BP_JSON = ROOT / "tools" / "elita_one" / "arcee_extracted" / "arcee_bindposes.json"
BONES63_JSON = ROOT / "tools" / "elita_one" / "arcee_extracted" / "arcee_63_bones.json"
HIERARCHY_JSON = ROOT / "tools" / "elita_one" / "arcee_bone_hierarchy.json"
MAPPING_JSON = ROOT / "tools" / "elita_one" / "elita_to_arcee_mapping.json"
OUT_FBX = ROOT / "toolchain" / "unity_build_project" / "Assets" / "ElitaOne" / "elita_one_prepared.fbx"

print("=== Building and Exporting Prepared FBX (1:1 Arcee 30-Finger Pivot & BindPose Alignment) ===")
bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Load Metadata
with open(HIERARCHY_JSON, "r", encoding="utf-8") as f:
    hierarchy = json.load(f)

with open(REST_JSON, "r", encoding="utf-8") as f:
    rest_data = json.load(f)

with open(BP_JSON, "r", encoding="utf-8") as f:
    bp_data = json.load(f)

with open(BONES63_JSON, "r", encoding="utf-8") as f:
    arcee_63_bones = json.load(f)

with open(MAPPING_JSON, "r", encoding="utf-8") as f:
    bone_mapping = json.load(f)

valid_bones = set(arcee_63_bones) | {"Reference"}

# Convert Arcee bindpose.inverse positions to Blender coordinates (x_u, z_u, y_u)
arcee_b_pos = {}
for idx, bname in enumerate(arcee_63_bones):
    bp = bp_data[idx]
    M_bp = mathutils.Matrix((
        (bp["e00"], bp["e01"], bp["e02"], bp["e03"]),
        (bp["e10"], bp["e11"], bp["e12"], bp["e13"]),
        (bp["e20"], bp["e21"], bp["e22"], bp["e23"]),
        (bp["e30"], bp["e31"], bp["e32"], bp["e33"]),
    ))
    u = M_bp.inverted().translation
    arcee_b_pos[bname] = mathutils.Vector((u.x, u.z, u.y))

# Solid hard-surface mechanical overrides
bone_mapping["l_lower_cover_wheel_skin"] = "LeftArm"
bone_mapping["l_lower_wheel_skin"] = "LeftArm"
bone_mapping["l_lower_wheel_skin_end"] = "LeftArm"
bone_mapping["r_lower_cover_wheel_skin"] = "RightArm"
bone_mapping["r_lower_wheel_skin"] = "RightArm"
bone_mapping["r_lower_wheel_skin_end"] = "RightArm"

bone_mapping["l_piston_lower_arm_start_skin"] = "LeftForeArm"
bone_mapping["l_piston_lower_arm_start_skin_end"] = "LeftForeArm"
bone_mapping["r_piston_lower_arm_start_skin"] = "RightForeArm"
bone_mapping["r_piston_lower_arm_start_skin_end"] = "RightForeArm"

for p_name in [
    "l_piston_leg_end_01_skin", "l_piston_leg_end_01_skin_end",
    "l_piston_leg_end_02_skin", "l_piston_leg_end_02_skin_end",
    "r_piston_leg_end_01_skin", "r_piston_leg_end_01_skin_end",
    "r_piston_leg_end_02_skin", "r_piston_leg_end_02_skin_end",
    "l_piston_leg_start_01_skin3", "l_piston_leg_start_01_skin3_end",
    "l_piston_leg_start_02_skin4", "l_piston_leg_start_02_skin4_end",
    "r_piston_leg_start_01_skin7", "r_piston_leg_start_01_skin7_end",
    "r_piston_leg_start_02_skin8", "r_piston_leg_start_02_skin8_end",
    "l_cover_hips_skin", "r_cover_hips_skin"
]:
    bone_mapping[p_name] = "Hips"

bone_mapping["l_shoulder_pistons_skin"] = "Spine1"
bone_mapping["l_shoulder_pistons_skin_end"] = "Spine1"
bone_mapping["r_shoulder_pistons_skin"] = "Spine1"
bone_mapping["r_shoulder_pistons_skin_end"] = "Spine1"

for p_name in [
    "l_piston_leg_start_01_skin", "l_piston_leg_start_01_skin_end",
    "l_piston_leg_start_02_skin", "l_piston_leg_start_02_skin_end",
    "l_foot_skin", "l_foot_heel_skin", "l_foot_heel_skin_end"
]:
    bone_mapping[p_name] = "LeftFoot"

for p_name in [
    "r_piston_leg_start_01_skin", "r_piston_leg_start_01_skin_end",
    "r_piston_leg_start_02_skin", "r_piston_leg_start_02_skin_end",
    "r_foot_skin", "r_foot_heel_skin", "r_foot_heel_skin_end"
]:
    bone_mapping[p_name] = "RightFoot"

# 2. Import Elita One FBX and Pose SK_CH_11 to 1:1 Arcee Arm/Hand/30-Finger Joints
print("[*] Importing Elita One FBX...")
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

fbx_arm = bpy.data.objects.get("SK_CH_11")
elita_mesh = bpy.data.objects.get("SK_CH_11.001")

orig_mat_slots = [p.material_index for p in elita_mesh.data.polygons]
new_poly_slots = [0 if idx in (0, 1) else 1 for idx in orig_mat_slots]

scale_s = 8.840 / 8.083
M_transform = mathutils.Matrix.Rotation(math.radians(90.0), 4, 'Z') @ mathutils.Matrix.Scale(scale_s, 4)

fbx_arm.data.transform(M_transform)
elita_mesh.data.transform(M_transform)

# Disconnect edit bones so PoseBone translations place joints with sub-millimeter precision
bpy.context.view_layer.objects.active = fbx_arm
bpy.ops.object.mode_set(mode='EDIT')
for eb in fbx_arm.data.edit_bones:
    eb.use_connect = False
bpy.ops.object.mode_set(mode='POSE')


def pose_segment(bname, child_bname, target_head, target_child_head, thickness_scale=1.0):
    """Align bname's head to target_head, rotate segment direction toward target_child_head, and scale along segment."""
    pb = fbx_arm.pose.bones.get(bname)
    pb_child = fbx_arm.pose.bones.get(child_bname) if child_bname else None
    bpy.context.view_layer.update()

    curr_head = pb.head.copy()
    if pb_child:
        curr_end = pb_child.head.copy()
    else:
        p_head = pb.parent.head.copy()
        curr_end = curr_head + (curr_head - p_head)

    v_curr = curr_end - curr_head
    v_targ = target_child_head - target_head
    len_curr = v_curr.length
    len_targ = v_targ.length

    q_rot = v_curr.rotation_difference(v_targ) if (len_curr > 1e-5 and len_targ > 1e-5) else mathutils.Quaternion()
    s_len = (len_targ / len_curr) if len_curr > 1e-5 else 1.0

    d = v_curr.normalized() if len_curr > 1e-5 else mathutils.Vector((0, 0, -1))
    S = mathutils.Matrix.Identity(3) * thickness_scale
    for r in range(3):
        for c in range(3):
            S[r][c] += (s_len - thickness_scale) * d[r] * d[c]

    RS = q_rot.to_matrix() @ S
    M_old = pb.matrix.copy()
    R_new = RS @ M_old.to_3x3()
    M_new = R_new.to_4x4()
    M_new.translation = target_head
    pb.matrix = M_new
    bpy.context.view_layer.update()


# 2.1 Rotate upperarms inward (pure rotation so shoulder wheels remain 100% rigid & circular)
for up_n, wr_n, hand_a in [
    ("l_upperarm_skin", "l_hand_skin", "LeftHand"),
    ("r_upperarm_skin", "r_hand_skin", "RightHand"),
]:
    sh = fbx_arm.data.bones.get(up_n).head_local
    wr = fbx_arm.data.bones.get(wr_n).head_local
    targ_wr = arcee_b_pos[hand_a]
    q = (wr - sh).rotation_difference(targ_wr - sh)
    R_rest = fbx_arm.data.bones.get(up_n).matrix_local.to_3x3()
    fbx_arm.pose.bones.get(up_n).rotation_quaternion = (R_rest.inverted() @ q.to_matrix() @ R_rest).to_quaternion()
bpy.context.view_layer.update()

# 2.2 Pose Forearms (keep elbow socket connected, reach Arcee LeftHand / RightHand) & Hands
for low_n, hand_n, hand_a, mid_n, mid_a in [
    ("l_lowerarm_skin", "l_hand_skin", "LeftHand", "l_middle_01_skin", "LeftHandMiddle1"),
    ("r_lowerarm_skin", "r_hand_skin", "RightHand", "r_middle_01_skin", "RightHandMiddle1"),
]:
    curr_elbow = fbx_arm.pose.bones.get(low_n).head.copy()
    pose_segment(low_n, hand_n, curr_elbow, arcee_b_pos[hand_a], thickness_scale=1.0)
    pose_segment(hand_n, mid_n, arcee_b_pos[hand_a], arcee_b_pos[mid_a], thickness_scale=1.25)

# Record pre-shift thumb1 positions on the posed palm so we can smoothly bridge the palm thumb saddle
pre_l_thumb1 = fbx_arm.pose.bones.get("l_thumb_01_skin").head.copy()
pre_r_thumb1 = fbx_arm.pose.bones.get("r_thumb_01_skin").head.copy()
delta_l_thumb1 = arcee_b_pos["LeftHandThumb1"] - pre_l_thumb1
delta_r_thumb1 = arcee_b_pos["RightHandThumb1"] - pre_r_thumb1

# 2.3 Pose all 30 finger bones (5 fingers x 3 phalanges x 2 hands) directly onto Arcee's 30 finger pivots
finger_chains = [
    ("thumb", "Thumb"),
    ("index", "Index"),
    ("middle", "Middle"),
    ("ring", "Ring"),
    ("pinky", "Pinky"),
]

for side_p, side_a in [("l", "LeftHand"), ("r", "RightHand")]:
    for fn_e, fn_a in finger_chains:
        e1, e2, e3 = f"{side_p}_{fn_e}_01_skin", f"{side_p}_{fn_e}_02_skin", f"{side_p}_{fn_e}_03_skin"
        a1, a2, a3 = f"{side_a}{fn_a}1", f"{side_a}{fn_a}2", f"{side_a}{fn_a}3"
        p1, p2, p3 = arcee_b_pos[a1], arcee_b_pos[a2], arcee_b_pos[a3]
        p4 = p3 + (p3 - p2)
        pose_segment(e1, e2, p1, p2, thickness_scale=1.12)
        pose_segment(e2, e3, p2, p3, thickness_scale=1.12)
        pose_segment(e3, None, p3, p4, thickness_scale=1.12)

# Verify joint alignment accuracy across wrists and all 30 finger bones
max_finger_err_mm = 0.0
for side_p, side_a in [("l", "LeftHand"), ("r", "RightHand")]:
    w_err = (fbx_arm.pose.bones.get(f"{side_p}_hand_skin").head - arcee_b_pos[side_a]).length * 1000.0
    print(f"[✓] {side_a} wrist alignment error: {w_err:.3f} mm")
    for fn_e, fn_a in finger_chains:
        for k in (1, 2, 3):
            eb_n = f"{side_p}_{fn_e}_0{k}_skin"
            ab_n = f"{side_a}{fn_a}{k}"
            err_mm = (fbx_arm.pose.bones.get(eb_n).head - arcee_b_pos[ab_n]).length * 1000.0
            if err_mm > max_finger_err_mm:
                max_finger_err_mm = err_mm
print(f"[✓] Max joint error across ALL 30 finger bones: {max_finger_err_mm:.4f} mm!")

bpy.ops.object.mode_set(mode='OBJECT')

# Bake posed SK_CH_11 deformation onto elita_mesh
bpy.context.view_layer.objects.active = elita_mesh
for m in elita_mesh.modifiers:
    if m.type == 'ARMATURE':
        bpy.ops.object.modifier_apply(modifier=m.name)
        break

# Smoothly bridge the palm's thumb saddle toward LeftHandThumb1 / RightHandThumb1 so there is zero step gap
vg_name_by_idx = {vg.index: vg.name for vg in elita_mesh.vertex_groups}
saddle_radius = 0.18
bridged_count = 0
for v in elita_mesh.data.vertices:
    w_l_hand = 0.0
    w_r_hand = 0.0
    for g in v.groups:
        gn = vg_name_by_idx.get(g.group)
        if gn == "l_hand_skin":
            w_l_hand = g.weight
        elif gn == "r_hand_skin":
            w_r_hand = g.weight
    if w_l_hand > 0.01:
        d = (v.co - pre_l_thumb1).length
        if d < saddle_radius * 2.2:
            falloff = math.exp(-((d / saddle_radius) ** 2))
            v.co += delta_l_thumb1 * (w_l_hand * falloff)
            bridged_count += 1
    elif w_r_hand > 0.01:
        d = (v.co - pre_r_thumb1).length
        if d < saddle_radius * 2.2:
            falloff = math.exp(-((d / saddle_radius) ** 2))
            v.co += delta_r_thumb1 * (w_r_hand * falloff)
            bridged_count += 1

elita_mesh.data.update()
print(f"[✓] Smoothly bridged {bridged_count} palm thumb-saddle vertices to Thumb1 sockets!")

bpy.data.objects.remove(fbx_arm, do_unlink=True)

# 3. Build 63-Bone Armature "character_model" using 100% Authoritative Arcee Rest Positions
C = mathutils.Matrix((
    (1, 0, 0, 0),
    (0, 0, 1, 0),
    (0, 1, 0, 0),
    (0, 0, 0, 1)
))

arm_data = bpy.data.armatures.new("character_model")
arm_obj = bpy.data.objects.new("character_model", arm_data)
bpy.context.scene.collection.objects.link(arm_obj)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='EDIT')

edit_bones = {}
for b in rest_data["bones"]:
    bname = b["name"]
    if bname in edit_bones or bname not in valid_bones:
        continue

    eb = arm_data.edit_bones.new(bname)
    m_raw = b["m"]
    M_u = mathutils.Matrix((m_raw[0:4], m_raw[4:8], m_raw[8:12], m_raw[12:16]))
    M_b = C @ M_u @ C
    eb.head = M_b.translation
    eb.tail = M_b.translation + mathutils.Vector((0.0, 0.08, 0.0))
    edit_bones[bname] = eb

for bname, eb in edit_bones.items():
    eb.use_connect = False
    pname = hierarchy.get(bname)
    if pname and pname in edit_bones:
        eb.parent = edit_bones[pname]

bpy.ops.object.mode_set(mode='OBJECT')
print("[✓] Created 63-bone Armature 'character_model' at 100% Arcee official rest positions!")

# 4. Remap Vertex Groups to 63 Arcee Bones
print("[*] Remapping Elita One vertex groups to 63 Arcee bones...")
remapped_weights = {v.index: {} for v in elita_mesh.data.vertices}
for v in elita_mesh.data.vertices:
    for g in v.groups:
        orig_name = elita_mesh.vertex_groups[g.group].name
        target_bone = bone_mapping.get(orig_name)
        if target_bone:
            remapped_weights[v.index][target_bone] = remapped_weights[v.index].get(target_bone, 0.0) + g.weight

elita_mesh.vertex_groups.clear()
new_vgs = {}
for bname in arcee_63_bones:
    if bname not in new_vgs:
        new_vgs[bname] = elita_mesh.vertex_groups.new(name=bname)

for v_idx, w_dict in remapped_weights.items():
    if not w_dict:
        continue
    top_4 = sorted(w_dict.items(), key=lambda kv: kv[1], reverse=True)[:4]
    sum_w = sum(w for _, w in top_4)
    if sum_w > 0:
        for bname, w in top_4:
            norm_w = w / sum_w
            if norm_w > 0.001 and bname in new_vgs:
                new_vgs[bname].add([v_idx], norm_w, 'REPLACE')

# Bind to character_model armature
mod_e = elita_mesh.modifiers.new(name="Armature", type='ARMATURE')
mod_e.object = arm_obj
mod_e.use_vertex_groups = True
elita_mesh.parent = arm_obj

# 5. Set up 2 Materials matching Arcee submesh contract
mat_main = bpy.data.materials.new(name="cha_elita_one_main")
mat_vh = bpy.data.materials.new(name="cha_elita_one_vh")

elita_mesh.data.materials.clear()
elita_mesh.data.materials.append(mat_main)
elita_mesh.data.materials.append(mat_vh)

for p, s_idx in zip(elita_mesh.data.polygons, new_poly_slots):
    p.material_index = s_idx

elita_mesh.name = "cha_elita_one_gs_00"
arm_obj.name = "character_model"

arm_obj.location = (0.0, 0.0, 0.0)
elita_mesh.location = (0.0, 0.0, 0.0)
bpy.context.view_layer.update()

# Limit influences & normalize in weight paint mode
bpy.context.view_layer.objects.active = elita_mesh
bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
bpy.ops.object.mode_set(mode='OBJECT')

# 6. Export FBX
bpy.ops.object.select_all(action='DESELECT')
elita_mesh.select_set(True)
arm_obj.select_set(True)
bpy.context.view_layer.objects.active = arm_obj

OUT_FBX.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.fbx(
    filepath=str(OUT_FBX),
    use_selection=True,
    bake_anim=False,
    add_leaf_bones=False
)

print(f"[✓] SUCCESS: Exported 1:1 finger-aligned prepared FBX to {OUT_FBX} ({OUT_FBX.stat().st_size / (1024*1024):.2f} MB)")
