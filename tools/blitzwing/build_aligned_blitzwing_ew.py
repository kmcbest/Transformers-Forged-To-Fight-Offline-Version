import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import math
import bpy
import bmesh
import mathutils
from mathutils import Vector, Matrix, Quaternion, Euler

ROOT = Path(r"E:\Agent\TFTF-blender")
SRC_DIR = ROOT / "3rd-party-models" / "Blitzwing_EW" / "01_source"
EXPORT_DIR = ROOT / "3rd-party-models" / "Blitzwing_EW" / "03_fbx_exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
UNITY_BW_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Blitzwing"
UNITY_BW_DIR.mkdir(parents=True, exist_ok=True)

MEG_51_JSON = ROOT / "tools" / "blitzwing" / "megatron_51_authoritative_bindposes.json"
MEG_TANK_JSON = ROOT / "tools" / "blitzwing" / "megatron_tank_21_authoritative_bindposes.json"
RAMJET_JET_JSON = ROOT / "tools" / "blitzwing" / "ramjet_jet_29_authoritative_bindposes.json"

meg_51_data = json.loads(MEG_51_JSON.read_text(encoding="utf-8"))
meg_tank_data = json.loads(MEG_TANK_JSON.read_text(encoding="utf-8"))
ramjet_jet_data = json.loads(RAMJET_JET_JSON.read_text(encoding="utf-8"))

def u_to_b(pos):
    """Unity (ux, uy, uz) -> Blender (-ux, -uz, uy)."""
    return Vector((-float(pos[0]), -float(pos[2]), float(pos[1])))

meg_b_pos = {b: u_to_b(meg_51_data["bones"][b]["unity_world_pos"]) for b in meg_51_data["bones"]}

def weld_and_clean_normals(obj, smooth_angle_deg=40.0):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    verts_before = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()

    bpy.ops.object.mode_set(mode='EDIT')
    if obj.data.has_custom_normals:
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
    bpy.ops.object.mode_set(mode='OBJECT')

    obj.data.polygons.foreach_set("use_smooth", [True] * len(obj.data.polygons))
    obj.data.use_auto_smooth = True
    obj.data.auto_smooth_angle = math.radians(smooth_angle_deg)
    obj.data.update()
    print(f"[weld_and_clean_normals] Welded {verts_before - len(obj.data.vertices)} vertices on '{obj.name}'.")

def remap_polygon_uv_to_tile(uv_layer, poly, u_min, u_max, v_min, v_max):
    """Per-polygon integer tile unwrapping for wrapped/repeat UVs (e.g. U in [-1, 0]) into an atlas quadrant."""
    loops = poly.loop_indices
    n = len(loops)
    if n == 0:
        return
    mean_u = sum(uv_layer.data[li].uv.x for li in loops) / n
    mean_v = sum(uv_layer.data[li].uv.y for li in loops) / n
    shift_u = math.floor(mean_u)
    shift_v = math.floor(mean_v)
    span_u = u_max - u_min
    span_v = v_max - v_min
    for li in loops:
        u_local = min(max(uv_layer.data[li].uv.x - shift_u, 0.0), 1.0)
        v_local = min(max(uv_layer.data[li].uv.y - shift_v, 0.0), 1.0)
        new_u = min(max(u_min + u_local * span_u, u_min + 0.004), u_max - 0.004)
        new_v = min(max(v_min + v_local * span_v, v_min + 0.004), v_max - 0.004)
        uv_layer.data[li].uv = (new_u, new_v)


def pose_segment_world(arm_obj, bname, child_bname, target_head_w, target_end_w, thickness_scale=1.0, preserve_length=False, max_stretch=1.45):
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
    s_len = 1.0 if preserve_length else min(max_stretch, max(0.65, (len_targ / len_curr) if len_curr > 1e-5 else 1.0))

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


def pose_hand_rigid_world(arm_obj, hand_bname, mid_bname, target_wrist_w, target_mid_w):
    """Orthonormalize Hand bone (scale=1,1,1) to block inherited forearm non-uniform scale/shear from distorting fingers."""
    bpy.context.view_layer.update()
    pb_h = arm_obj.pose.bones[hand_bname]
    pb_m = arm_obj.pose.bones[mid_bname]
    w_old = arm_obj.matrix_world @ pb_h.matrix
    R_old_ortho = w_old.to_3x3().to_quaternion().to_matrix()

    curr_wrist = w_old.translation
    curr_mid = (arm_obj.matrix_world @ pb_m.matrix).translation
    v_curr = (curr_mid - curr_wrist).normalized()
    v_targ = (target_mid_w - target_wrist_w).normalized()
    q_rot = v_curr.rotation_difference(v_targ)

    R_new = q_rot.to_matrix() @ R_old_ortho
    M_new_w = R_new.to_4x4()
    M_new_w.translation = target_wrist_w
    pb_h.matrix = arm_obj.matrix_world.inverted() @ M_new_w
    bpy.context.view_layer.update()


def curl_bone_world_axis(arm_obj, bname, world_axis, angle_deg):
    """Rotate pose bone cleanly around a deterministic world-space hinge axis through its head."""
    bpy.context.view_layer.update()
    pb = arm_obj.pose.bones.get(bname)
    if not pb:
        return
    w_old = arm_obj.matrix_world @ pb.matrix
    q_world = Quaternion(world_axis.normalized(), math.radians(angle_deg))
    R_new = q_world.to_matrix() @ w_old.to_3x3()
    M_new_w = R_new.to_4x4()
    M_new_w.translation = w_old.translation
    pb.matrix = arm_obj.matrix_world.inverted() @ M_new_w
    bpy.context.view_layer.update()


def set_foot_flat_world(arm_obj, foot_bname, ankle_target_w):
    """Keep Foot & child boot parts horizontal on the floor without inheriting Calf's slant."""
    bpy.context.view_layer.update()
    pb = arm_obj.pose.bones[foot_bname]
    R_rest = pb.bone.matrix_local.to_3x3()
    M_new_w = R_rest.to_4x4()
    M_new_w.translation = ankle_target_w
    pb.matrix = arm_obj.matrix_world.inverted() @ M_new_w
    bpy.context.view_layer.update()

# =========================================================================
# 1. PROCESS HUMANOID ROBOT
# =========================================================================
print("\n=======================================================")
print("=== 1. PROCESSING BLITZWING ROBOT ===")
print("=======================================================")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SRC_DIR / "H_shandian_G1_M_LOD.fbx"))

mesh_obj = bpy.data.objects['H_shandian_G1_M_Lod']
arm_obj = bpy.data.objects['floor']

# 1a. Unparent keeping world transform (strips 0.01 parent empty)
bpy.ops.object.select_all(action='DESELECT')
for o in [mesh_obj, arm_obj]:
    o.select_set(True)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

# Remove all other objects
for o in list(bpy.data.objects):
    if o not in [mesh_obj, arm_obj]:
        bpy.data.objects.remove(o, do_unlink=True)

# 1b. Reset rest pose & clear animations
arm_obj.animation_data_clear()
mesh_obj.animation_data_clear()
for pb in arm_obj.pose.bones:
    pb.location = (0, 0, 0)
    pb.rotation_quaternion = (1, 0, 0, 0)
    pb.rotation_euler = (0, 0, 0)
    pb.scale = (1, 1, 1)
arm_obj.data.pose_position = 'REST'
bpy.context.view_layer.update()

# 1c. Apply all initial transforms to freeze world scale
bpy.ops.object.select_all(action='DESELECT')
for o in [mesh_obj, arm_obj]:
    o.select_set(True)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 1d. Weld doubles & clean normals
weld_and_clean_normals(mesh_obj, 40.0)

# 1e. Remap UVs into 2048x2048 Atlas
# M_a -> Top-Left (U in [0, 0.5], V in [0.5, 1.0])
# M_b -> Bottom-Left (U in [0, 0.5], V in [0, 0.5])
print("[*] Remapping Robot UVs into cha_blitzwing_main 2048x2048 Atlas...")
uv_layer = mesh_obj.data.uv_layers.active
assert uv_layer, "Active UV layer missing on Robot mesh!"

mat_slots = [m.name for m in mesh_obj.data.materials if m]
for poly in mesh_obj.data.polygons:
    mat_idx = poly.material_index
    is_ma = (mat_idx == 0 or (mat_idx < len(mat_slots) and "M_a" in mat_slots[mat_idx]))
    if is_ma:
        remap_polygon_uv_to_tile(uv_layer, poly, 0.0, 0.5, 0.5, 1.0)
    else:
        remap_polygon_uv_to_tile(uv_layer, poly, 0.0, 0.5, 0.0, 0.5)

mesh_obj.data.materials.clear()
main_mat = bpy.data.materials.new(name="cha_blitzwing_main")
mesh_obj.data.materials.append(main_mat)
for poly in mesh_obj.data.polygons:
    poly.material_index = 0

# 1f. Ground Z=0
min_z = min(v.co.z for v in mesh_obj.data.vertices)
print(f"Grounding by {-min_z:.4f}m...")
mesh_obj.location.z -= min_z
arm_obj.location.z -= min_z
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 1g. Scale to Megatron height (~10.1m)
SCALE = 149.1728
print(f"Scaling by {SCALE:.4f}...")
mesh_obj.scale = (SCALE, SCALE, SCALE)
arm_obj.scale = (SCALE, SCALE, SCALE)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 1h. Add fingertip edit bones for distal segment targeting
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

# 1i. Posing Legs (Ground-First!) & Arms & Brawler Fists
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='POSE')

# 1i-1. Stand legs vertically closer to Megatron leg axes (X=+-0.838) with comfortable 34cm boot clearance
for side, sgn in [("L", 1.0), ("R", -1.0)]:
    th_head = (arm_obj.matrix_world @ arm_obj.pose.bones[f"Bip001 {side} Thigh"].matrix).translation.copy()
    knee_targ = Vector((0.98 * sgn, th_head.y - 0.05, 4.453))
    ankle_targ = Vector((1.05 * sgn, th_head.y + 0.05, 1.150))

    pose_segment_world(arm_obj, f"Bip001 {side} Thigh", f"Bip001 {side} Calf", th_head, knee_targ, thickness_scale=1.0, preserve_length=True)
    pose_segment_world(arm_obj, f"Bip001 {side} Calf", f"Bip001 {side} Foot", knee_targ, ankle_targ, thickness_scale=1.0, preserve_length=True)
    set_foot_flat_world(arm_obj, f"Bip001 {side} Foot", ankle_targ)

# Ground-First: shift mesh & armature so deformed boot soles touch Z=0 before aligning arms!
bpy.ops.object.mode_set(mode='OBJECT')
deps = bpy.context.evaluated_depsgraph_get()
ev_obj = mesh_obj.evaluated_get(deps)
ev_mesh = ev_obj.to_mesh()
post_leg_min_z = min((ev_obj.matrix_world @ v.co).z for v in ev_mesh.vertices)
ev_obj.to_mesh_clear()
mesh_obj.location.z -= post_leg_min_z
arm_obj.location.z -= post_leg_min_z
bpy.context.view_layer.update()
print(f"[✓] Ground-First leg alignment complete (ankles X=+-1.05m, shifted Z by {-post_leg_min_z:+.4f}m).")

# 1i-2. Posing arms & baking symmetrical palm-curled brawler fists via deterministic world axes (Track B)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='POSE')

for side, pfx in [("L", "Left"), ("R", "Right")]:
    sh_head = (arm_obj.matrix_world @ arm_obj.pose.bones[f"Bip001 {side} UpperArm"].matrix).translation.copy()
    elbow_targ = meg_b_pos[f"{pfx}ForeArm"]
    wrist_targ = meg_b_pos[f"{pfx}Hand"]
    mid1_targ = meg_b_pos[f"{pfx}HandMiddle1"]

    pose_segment_world(arm_obj, f"Bip001 {side} UpperArm", f"Bip001 {side} Forearm", sh_head, elbow_targ, thickness_scale=1.0, preserve_length=False, max_stretch=1.40)
    pose_segment_world(arm_obj, f"Bip001 {side} Forearm", f"Bip001 {side} Hand", elbow_targ, wrist_targ, thickness_scale=1.0, preserve_length=False, max_stretch=1.48)
    # Orthonormalize Hand so forearm stretch NEVER shears/distorts palm & fingers, while keeping authentic palm-inward facing
    pose_hand_rigid_world(arm_obj, f"Bip001 {side} Hand", f"Bip001 {side} Finger2", wrist_targ, mid1_targ)

    # Derive inward palm-curl knuckle axis directly from Index->Pinky world positions (immune to Biped mirrored local axes)
    f1_pos = (arm_obj.matrix_world @ arm_obj.pose.bones[f"Bip001 {side} Finger1"].matrix).translation
    f4_pos = (arm_obj.matrix_world @ arm_obj.pose.bones[f"Bip001 {side} Finger4"].matrix).translation
    knuckle_axis_w = (f4_pos - f1_pos).normalized() if side == "L" else (f1_pos - f4_pos).normalized()

    for fi in range(1, 5):
        for seg, deg in [("", 58.0), ("1", 68.0), ("2", 52.0)]:
            curl_bone_world_axis(arm_obj, f"Bip001 {side} Finger{fi}{seg}", knuckle_axis_w, deg)

    # Wrap Thumb (Finger0 -> 01 -> 02) smoothly across front of Index & Middle knuckles
    sgn = 1.0 if side == "L" else -1.0
    curl_bone_world_axis(arm_obj, f"Bip001 {side} Finger0", Vector((0, 0, -1 * sgn)), 14.0)
    curl_bone_world_axis(arm_obj, f"Bip001 {side} Finger0", Vector((1, 0, 0)), 14.0)
    curl_bone_world_axis(arm_obj, f"Bip001 {side} Finger01", Vector((0, 0, -1 * sgn)), 26.0)
    curl_bone_world_axis(arm_obj, f"Bip001 {side} Finger02", Vector((0, 0, -1 * sgn)), 28.0)

bpy.context.view_layer.update()
print("[✓] Posed arms cleanly and baked inward-curled brawler fists with front-wrapped Thumbs (Track B).")

bpy.ops.object.mode_set(mode='OBJECT')

# Apply posed armature to mesh and freeze any remaining object location into vertices
bpy.context.view_layer.objects.active = mesh_obj
mesh_obj.select_set(True)
bpy.ops.object.modifier_apply(modifier="Armature")
mesh_obj.parent = None
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.data.objects.remove(arm_obj, do_unlink=True)

# 1i-3. Seat ankle pins deeply into foot sockets so heavy combat crouches never leave floating calves
vg_pre_idx = {vg.index: vg.name for vg in mesh_obj.vertex_groups}
ankle_seated_cnt = 0
for v in mesh_obj.data.vertices:
    is_calf = any(vg_pre_idx.get(g.group) in ("Bone005(mirrored)", "Bone005", "Bip001 L Calf", "Bip001 R Calf") and g.weight > 0.3 for g in v.groups)
    if is_calf and 0.45 <= v.co.z < 0.88:
        # Check radial proximity to left/right ankle socket center (X=+-1.05, Y=0)
        if min((Vector((v.co.x - 1.05, v.co.y))).length, (Vector((v.co.x + 1.05, v.co.y))).length) < 0.55:
            # Extend pin cone tips downward deeper into foot cavity while staying strictly above sole bottom (0.28m)
            t_depth = (0.88 - v.co.z) / (0.88 - 0.50)
            v.co.z = max(0.28, v.co.z - 0.25 * min(1.2, t_depth))
            ankle_seated_cnt += 1
mesh_obj.data.update()
print(f"[✓] Extended & deeply seated {ankle_seated_cnt} ankle joint vertices into foot sockets (never floats in combat!).")

# 1j. Rebind Vertex Groups to Megatron 51 Authoritative Bones (Track B: fists locked cleanly to LeftHand/RightHand)
VG_MAP = {
    # Torso & Pelvis
    "Bip001 Pelvis": "Hips",
    "Bip001 Spine": "Spine",
    "Bone001": "Spine1", "Bone002": "Spine1", "Bone003": "Spine1", "Bone010": "Spine1",
    "Bone012": "Spine1", "Bone013": "Spine1", "Bone014": "Spine1",
    "Bone012(mirrored)": "Spine1", "Bone013(mirrored)": "Spine1", "Bone014(mirrored)": "Spine1",

    # Head
    "Bip001 Neck": "Head",
    "Bip001 Head": "Head",
    "Bone011": "Head",

    # Shoulders & Arms
    "Bip001 L Clavicle": "LeftShoulder",
    "Bone004(mirrored)": "LeftShoulder",
    "Bip001 L UpperArm": "LeftArm",
    "Bip001 L Forearm": "LeftForeArm",
    "Bip001 L Hand": "LeftHand",
    "Bone_wuqi01": "LeftHand",

    "Bip001 R Clavicle": "RightShoulder",
    "Bone004": "RightShoulder",
    "Bip001 R UpperArm": "RightArm",
    "Bip001 R Forearm": "RightForeArm",
    "Bip001 R Hand": "RightHand",
    "Bone_wuqi02": "RightHand",

    # Left Hand Fingers (15) - Baked natural brawler fist merged 100% into LeftHand
    "Bip001 L Finger0": "LeftHand",
    "Bip001 L Finger01": "LeftHand",
    "Bip001 L Finger02": "LeftHand",
    "Bip001 L Finger1": "LeftHand",
    "Bip001 L Finger11": "LeftHand",
    "Bip001 L Finger12": "LeftHand",
    "Bip001 L Finger2": "LeftHand",
    "Bip001 L Finger21": "LeftHand",
    "Bip001 L Finger22": "LeftHand",
    "Bip001 L Finger3": "LeftHand",
    "Bip001 L Finger31": "LeftHand",
    "Bip001 L Finger32": "LeftHand",
    "Bip001 L Finger4": "LeftHand",
    "Bip001 L Finger41": "LeftHand",
    "Bip001 L Finger42": "LeftHand",

    # Right Hand Fingers (15) - Baked natural brawler fist merged 100% into RightHand
    "Bip001 R Finger0": "RightHand",
    "Bip001 R Finger01": "RightHand",
    "Bip001 R Finger02": "RightHand",
    "Bip001 R Finger1": "RightHand",
    "Bip001 R Finger11": "RightHand",
    "Bip001 R Finger12": "RightHand",
    "Bip001 R Finger2": "RightHand",
    "Bip001 R Finger21": "RightHand",
    "Bip001 R Finger22": "RightHand",
    "Bip001 R Finger3": "RightHand",
    "Bip001 R Finger31": "RightHand",
    "Bip001 R Finger32": "RightHand",
    "Bip001 R Finger4": "RightHand",
    "Bip001 R Finger41": "RightHand",
    "Bip001 R Finger42": "RightHand",

    # Legs & Feet (keep rigid boot assemblies 100% locked to LeftFoot/RightFoot so tank treads/stabilizers never tear apart)
    "Bip001 L Thigh": "LeftUpLeg",
    "Bip001 R Thigh": "RightUpLeg",
    "Bip001 L Calf": "LeftLeg",
    "Bone005(mirrored)": "LeftLeg",
    "Bip001 R Calf": "RightLeg",
    "Bone005": "RightLeg",
    "Bip001 L Foot": "LeftFoot",
    "Bone006(mirrored)": "LeftFoot", "Bone007(mirrored)": "LeftFoot",
    "Bone008(mirrored)": "LeftFoot", "Bone009(mirrored)": "LeftFoot",
    "Bip001 L Toe0": "LeftFoot",
    "Bip001 R Foot": "RightFoot",
    "Bone006": "RightFoot", "Bone007": "RightFoot",
    "Bone008": "RightFoot", "Bone009": "RightFoot",
    "Bip001 R Toe0": "RightFoot",
}

old_vg_by_index = {vg.index: vg.name for vg in mesh_obj.vertex_groups}
n_verts = len(mesh_obj.data.vertices)
target_weights = {b: [0.0] * n_verts for b in meg_51_data["bone_names"]}

for v in mesh_obj.data.vertices:
    vi = v.index
    for g in v.groups:
        old_name = old_vg_by_index.get(g.group)
        if old_name in VG_MAP:
            target_bone = VG_MAP[old_name]
            target_weights[target_bone][vi] += g.weight

# Smooth spherical joint blend on lower-calf ankle pins (Z in [0.65, 1.15]) so the ankle shaft flexes without disconnecting
ankle_blended_cnt = 0
for v in mesh_obj.data.vertices:
    vi = v.index
    co = v.co
    if co.z < 1.15:
        for leg_b, foot_b, sgn in [("LeftLeg", "LeftFoot", 1.0), ("RightLeg", "RightFoot", -1.0)]:
            if target_weights[leg_b][vi] > 0.4 and (Vector((co.x - 1.05 * sgn, co.y))).length < 0.55:
                if co.z <= 0.65:
                    w_foot = 1.0
                else:
                    w_foot = (1.15 - co.z) / (1.15 - 0.65)
                tot_lf = target_weights[leg_b][vi] + target_weights[foot_b][vi]
                target_weights[foot_b][vi] = tot_lf * w_foot
                target_weights[leg_b][vi] = tot_lf * (1.0 - w_foot)
                ankle_blended_cnt += 1
print(f"[✓] Blended {ankle_blended_cnt} lower-calf ankle shaft vertices smoothly into foot sockets.")

# Normalize weights and guarantee zero unweighted vertices
zero_w_count = 0
for vi in range(n_verts):
    tot = sum(target_weights[b][vi] for b in meg_51_data["bone_names"])
    if tot > 1e-5:
        for b in meg_51_data["bone_names"]:
            target_weights[b][vi] /= tot
    else:
        target_weights["Hips"][vi] = 1.0
        zero_w_count += 1

print(f"[✓] Vertex groups normalized. Zero-weight fallbacks: {zero_w_count}")

mesh_obj.vertex_groups.clear()
for bname in meg_51_data["bone_names"]:
    vg = mesh_obj.vertex_groups.new(name=bname)
    w_list = target_weights[bname]
    for vi, w in enumerate(w_list):
        if w > 0.0005:
            vg.add([vi], w, 'REPLACE')

# 1k. Build Megatron 51-bone Armature
new_arm_data = bpy.data.armatures.new("character_model")
new_arm_obj = bpy.data.objects.new("character_model", new_arm_data)
bpy.context.scene.collection.objects.link(new_arm_obj)
bpy.context.view_layer.objects.active = new_arm_obj
bpy.ops.object.mode_set(mode='EDIT')

edit_bones = {}
for bname in meg_51_data["bone_names"]:
    b_info = meg_51_data["bones"][bname]
    head_pos = u_to_b(b_info["unity_world_pos"])
    eb = new_arm_data.edit_bones.new(bname)
    eb.head = head_pos
    if any(k in bname for k in ["Thumb", "Index", "Middle", "Ring", "Pinky", "Arm", "Leg", "ForeArm"]):
        eb.tail = head_pos + Vector((0, -0.15, 0))
    else:
        eb.tail = head_pos + Vector((0, 0, 0.15))
    edit_bones[bname] = eb

for bname in meg_51_data["bone_names"]:
    b_info = meg_51_data["bones"][bname]
    p_name = b_info.get("parent")
    if p_name and p_name in edit_bones and p_name != bname:
        eb = edit_bones[bname]
        eb.parent = edit_bones[p_name]
        diff = eb.head - edit_bones[p_name].head
        if diff.length > 0.04 and any(k in p_name for k in ["Thumb", "Index", "Middle", "Ring", "Pinky", "Arm", "Leg"]):
            edit_bones[p_name].tail = eb.head

# Set terminal distal bone tails along finger direction
for bname in meg_51_data["bone_names"]:
    eb = edit_bones[bname]
    if eb.parent and any(k in bname for k in ["Thumb3", "Index3", "Middle3", "Ring3", "Pinky3"]):
        diff = eb.head - eb.parent.head
        if diff.length > 0.02:
            eb.tail = eb.head + diff.normalized() * 0.15

bpy.ops.object.mode_set(mode='OBJECT')

mesh_obj.parent = new_arm_obj
mod = mesh_obj.modifiers.new("Armature", "ARMATURE")
mod.object = new_arm_obj

out_robot_fbx = UNITY_BW_DIR / "blitzwing_robot.fbx"
out_robot_stage = EXPORT_DIR / "cha_blitzwing_gs_00_robot.fbx"

for out_path in (out_robot_fbx, out_robot_stage):
    bpy.ops.object.select_all(action='DESELECT')
    new_arm_obj.select_set(True)
    mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = new_arm_obj
    bpy.ops.export_scene.fbx(
        filepath=str(out_path),
        use_selection=True,
        axis_forward='-Z',
        axis_up='Y',
        apply_scale_options='FBX_SCALE_ALL',
        bake_space_transform=False,
        object_types={'ARMATURE', 'MESH'},
        use_mesh_modifiers=True,
        add_leaf_bones=False,
        primary_bone_axis='Y',
        secondary_bone_axis='X',
        armature_nodetype='NULL'
    )
print(f"[✓] Exported Robot FBX: {out_robot_fbx}")


# =========================================================================
# 2. PROCESS TANK MODE (V1)
# =========================================================================
print("\n=======================================================")
print("=== 2. PROCESSING BLITZWING TANK MODE ===")
print("=======================================================")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SRC_DIR / "H_shandian_G1_V1.fbx"))

tank_mesh = bpy.data.objects['H_shandian_G1_V1.001']
tank_raw_arm = bpy.data.objects['floor']

bpy.ops.object.select_all(action='DESELECT')
for o in [tank_mesh, tank_raw_arm]:
    o.select_set(True)
bpy.context.view_layer.objects.active = tank_raw_arm
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

for o in list(bpy.data.objects):
    if o not in [tank_mesh, tank_raw_arm]:
        bpy.data.objects.remove(o, do_unlink=True)

bpy.ops.object.select_all(action='DESELECT')
for o in [tank_mesh, tank_raw_arm]:
    o.select_set(True)
bpy.context.view_layer.objects.active = tank_raw_arm
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

tank_mesh.modifiers.clear()
tank_mesh.parent = None
bpy.data.objects.remove(tank_raw_arm, do_unlink=True)

weld_and_clean_normals(tank_mesh, 40.0)

# Remap UVs to Top-Left in cha_blitzwing_tform_misc (U in [0, 0.5], V in [0.5, 1.0])
print("[*] Remapping Tank UVs into cha_blitzwing_tform_misc (per-polygon tile unwrap)...")
uv_l = tank_mesh.data.uv_layers.active
for poly in tank_mesh.data.polygons:
    remap_polygon_uv_to_tile(uv_l, poly, 0.0, 0.5, 0.5, 1.0)

tank_mesh.data.materials.clear()
tank_mat = bpy.data.materials.new(name="cha_blitzwing_tform_misc")
tank_mesh.data.materials.append(tank_mat)
for poly in tank_mesh.data.polygons:
    poly.material_index = 0

# Scale Tank to match Megatron Tank size: length ~8.9m, width ~4.7m
SCALE_T = 135.0
tank_mesh.scale = (SCALE_T, SCALE_T, SCALE_T)
bpy.context.view_layer.objects.active = tank_mesh
tank_mesh.select_set(True)
bpy.ops.object.transform_apply(scale=True)

# Center X and ground Z=0
min_x = min(v.co.x for v in tank_mesh.data.vertices)
max_x = max(v.co.x for v in tank_mesh.data.vertices)
cx = (min_x + max_x) / 2.0
min_z = min(v.co.z for v in tank_mesh.data.vertices)
tank_mesh.location = (-cx, 0, -min_z)
bpy.ops.object.transform_apply(location=True)

# Build Megatron Tank 21-bone Armature
tank_arm_data = bpy.data.armatures.new("transformed")
tank_arm_obj = bpy.data.objects.new("transformed", tank_arm_data)
bpy.context.scene.collection.objects.link(tank_arm_obj)
bpy.context.view_layer.objects.active = tank_arm_obj
bpy.ops.object.mode_set(mode='EDIT')

tank_edit_bones = {}
for bname in meg_tank_data["bone_names"]:
    b_info = meg_tank_data["bones"][bname]
    head_pos = u_to_b(b_info["unity_world_pos"])
    eb = tank_arm_data.edit_bones.new(bname)
    eb.head = head_pos
    eb.tail = head_pos + Vector((0, -0.1, 0))
    tank_edit_bones[bname] = eb

for bname in meg_tank_data["bone_names"]:
    b_info = meg_tank_data["bones"][bname]
    p_name = b_info.get("parent")
    if p_name and p_name in tank_edit_bones and p_name != bname:
        tank_edit_bones[bname].parent = tank_edit_bones[p_name]

bpy.ops.object.mode_set(mode='OBJECT')

tank_mesh.vertex_groups.clear()
for bname in meg_tank_data["bone_names"]:
    vg = tank_mesh.vertex_groups.new(name=bname)
    if bname == "chop2_torso_main_center":
        vg.add(list(range(len(tank_mesh.data.vertices))), 1.0, 'REPLACE')

tank_mesh.parent = tank_arm_obj
t_mod = tank_mesh.modifiers.new("Armature", "ARMATURE")
t_mod.object = tank_arm_obj

out_tank_fbx = UNITY_BW_DIR / "blitzwing_tank.fbx"
out_tank_stage = EXPORT_DIR / "cha_blitzwing_gs_01_tank.fbx"

for out_path in (out_tank_fbx, out_tank_stage):
    bpy.ops.object.select_all(action='DESELECT')
    tank_arm_obj.select_set(True)
    tank_mesh.select_set(True)
    bpy.context.view_layer.objects.active = tank_arm_obj
    bpy.ops.export_scene.fbx(
        filepath=str(out_path),
        use_selection=True,
        axis_forward='-Z',
        axis_up='Y',
        apply_scale_options='FBX_SCALE_ALL',
        bake_space_transform=False,
        object_types={'ARMATURE', 'MESH'},
        use_mesh_modifiers=True,
        add_leaf_bones=False,
        primary_bone_axis='Y',
        secondary_bone_axis='X',
        armature_nodetype='NULL'
    )
print(f"[✓] Exported Tank FBX: {out_tank_fbx}")


# =========================================================================
# 3. PROCESS JET MODE (V2)
# =========================================================================
print("\n=======================================================")
print("=== 3. PROCESSING BLITZWING JET MODE ===")
print("=======================================================")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SRC_DIR / "H_shandian_G1_V2.fbx"))

jet_mesh = bpy.data.objects['H_shandian_G1_V2.001']
jet_raw_arm = bpy.data.objects['H_shandian_G1_V2']

bpy.ops.object.select_all(action='DESELECT')
for o in [jet_mesh, jet_raw_arm]:
    o.select_set(True)
bpy.context.view_layer.objects.active = jet_raw_arm
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

for o in list(bpy.data.objects):
    if o not in [jet_mesh, jet_raw_arm]:
        bpy.data.objects.remove(o, do_unlink=True)

bpy.ops.object.select_all(action='DESELECT')
for o in [jet_mesh, jet_raw_arm]:
    o.select_set(True)
bpy.context.view_layer.objects.active = jet_raw_arm
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

jet_mesh.modifiers.clear()
jet_mesh.parent = None
bpy.data.objects.remove(jet_raw_arm, do_unlink=True)

weld_and_clean_normals(jet_mesh, 40.0)

# Remap UVs to Top-Right in cha_blitzwing_tform_misc (U in [0.5, 1.0], V in [0.5, 1.0])
print("[*] Remapping Jet UVs into cha_blitzwing_tform_misc (per-polygon tile unwrap)...")
uv_lj = jet_mesh.data.uv_layers.active
for poly in jet_mesh.data.polygons:
    remap_polygon_uv_to_tile(uv_lj, poly, 0.5, 1.0, 0.5, 1.0)

jet_mesh.data.materials.clear()
jet_mat = bpy.data.materials.new(name="cha_blitzwing_tform_misc")
jet_mesh.data.materials.append(jet_mat)
for poly in jet_mesh.data.polygons:
    poly.material_index = 0

# Scale Jet to match Ramjet length ~9.5m
SCALE_J = 140.0
jet_mesh.scale = (SCALE_J, SCALE_J, SCALE_J)
bpy.context.view_layer.objects.active = jet_mesh
jet_mesh.select_set(True)
bpy.ops.object.transform_apply(scale=True)

min_x = min(v.co.x for v in jet_mesh.data.vertices)
max_x = max(v.co.x for v in jet_mesh.data.vertices)
cx = (min_x + max_x) / 2.0
min_z = min(v.co.z for v in jet_mesh.data.vertices)
jet_mesh.location = (-cx, 0, -min_z)
bpy.ops.object.transform_apply(location=True)

# Build Ramjet Jet 29-bone Armature
jet_arm_data = bpy.data.armatures.new("transformed_2")
jet_arm_obj = bpy.data.objects.new("transformed_2", jet_arm_data)
bpy.context.scene.collection.objects.link(jet_arm_obj)
bpy.context.view_layer.objects.active = jet_arm_obj
bpy.ops.object.mode_set(mode='EDIT')

jet_edit_bones = {}
for bname in ramjet_jet_data["bone_names"]:
    b_info = ramjet_jet_data["bones"][bname]
    head_pos = u_to_b(b_info["unity_world_pos"])
    eb = jet_arm_data.edit_bones.new(bname)
    eb.head = head_pos
    eb.tail = head_pos + Vector((0, -0.1, 0))
    jet_edit_bones[bname] = eb

for bname in ramjet_jet_data["bone_names"]:
    b_info = ramjet_jet_data["bones"][bname]
    p_name = b_info.get("parent")
    if p_name and p_name in jet_edit_bones and p_name != bname:
        jet_edit_bones[bname].parent = jet_edit_bones[p_name]

bpy.ops.object.mode_set(mode='OBJECT')

jet_mesh.vertex_groups.clear()
for bname in ramjet_jet_data["bone_names"]:
    vg = jet_mesh.vertex_groups.new(name=bname)
    if bname == "COG":
        vg.add(list(range(len(jet_mesh.data.vertices))), 1.0, 'REPLACE')

jet_mesh.parent = jet_arm_obj
j_mod = jet_mesh.modifiers.new("Armature", "ARMATURE")
j_mod.object = jet_arm_obj

out_jet_fbx = UNITY_BW_DIR / "blitzwing_jet.fbx"
out_jet_stage = EXPORT_DIR / "cha_blitzwing_gs_02_jet.fbx"

for out_path in (out_jet_fbx, out_jet_stage):
    bpy.ops.object.select_all(action='DESELECT')
    jet_arm_obj.select_set(True)
    jet_mesh.select_set(True)
    bpy.context.view_layer.objects.active = jet_arm_obj
    bpy.ops.export_scene.fbx(
        filepath=str(out_path),
        use_selection=True,
        axis_forward='-Z',
        axis_up='Y',
        apply_scale_options='FBX_SCALE_ALL',
        bake_space_transform=False,
        object_types={'ARMATURE', 'MESH'},
        use_mesh_modifiers=True,
        add_leaf_bones=False,
        primary_bone_axis='Y',
        secondary_bone_axis='X',
        armature_nodetype='NULL'
    )
print(f"[✓] Exported Jet FBX: {out_jet_fbx}")
print("\n=== [GATE 2 SUCCESS] All 3 FBXs successfully built and exported! ===")
