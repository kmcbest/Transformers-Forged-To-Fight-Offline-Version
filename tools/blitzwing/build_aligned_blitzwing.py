import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import bpy
import bmesh
import math
import mathutils
from mathutils import Vector, Matrix, Quaternion

ROOT = Path(r"E:\Agent\TFTF-blender")
BLEND_SRC = ROOT / "3rd-party-models" / "blitzwing_extracted" / "rar" / "Blitzwing.blend"
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
    """Welds split cartoon vertex doubles, clears custom anime split normals, and enables 3D metal auto-smoothing."""
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    verts_before = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0002)
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
    print(f"[weld_and_clean_normals] Welded {verts_before - len(obj.data.vertices)} vertices on '{obj.name}'. Normals cleaned, auto-smooth set to {smooth_angle_deg}deg.")

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

# =========================================================================
# 1. PROCESS HUMANOID ROBOT
# =========================================================================
print("=== 1. PROCESSING BLITZWING HUMANOID ===")
bpy.ops.wm.open_mainfile(filepath=str(BLEND_SRC))

mesh_obj = bpy.data.objects['Blitzwing']
arm_obj = bpy.data.objects['Blitzwing_Skeleton']

for o in list(bpy.data.objects):
    if o not in [mesh_obj, arm_obj]:
        bpy.data.objects.remove(o, do_unlink=True)

# Clear any animation data on armature and mesh
arm_obj.animation_data_clear()
mesh_obj.animation_data_clear()

# Reset ALL pose bones to identity (rest pose) to wipe out any residual Devastation pose
for pb in arm_obj.pose.bones:
    pb.location = (0, 0, 0)
    pb.rotation_quaternion = (1, 0, 0, 0)
    pb.rotation_euler = (0, 0, 0)
    pb.scale = (1, 1, 1)

arm_obj.data.pose_position = 'REST'
bpy.context.view_layer.update()

# Clear shape keys first if any
if mesh_obj.data.shape_keys:
    bpy.context.view_layer.objects.active = mesh_obj
    mesh_obj.select_set(True)
    bpy.ops.object.shape_key_remove(all=True)
    print("[✓] Cleared shape keys")

# Weld doubles & clear custom split normals
weld_and_clean_normals(mesh_obj, 40.0)

# Scale factor = 1.4803 & Ground Z=0
SCALE = 1.4803
min_z = min(v.co.z for v in mesh_obj.data.vertices)
print(f"Grounding by {-min_z:.4f}m and scaling by {SCALE}...")

ground_scale_mat = Matrix.Scale(SCALE, 4) @ Matrix.Translation((0, 0, -min_z))
mesh_obj.data.transform(ground_scale_mat)
mesh_obj.data.update()

# Ground and scale armature edit bones
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
# Reset all pose bones in POSE mode to ensure zero residual pose on pelvis, legs, spine, neck, and head
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

# Posing arms, forearms, hands, and all 30 fingers to 1:1 match Megatron's bind pose!
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='POSE')

for side, pfx in [("L", "Left"), ("R", "Right")]:
    sh_head = (arm_obj.matrix_world @ arm_obj.pose.bones[f"bip_upperArm_{side}"].matrix).translation.copy()
    elbow_targ = meg_b_pos[f"{pfx}ForeArm"]
    wrist_targ = meg_b_pos[f"{pfx}Hand"]
    
    pose_segment_world(arm_obj, f"bip_upperArm_{side}", f"bip_lowerArm_{side}", sh_head, elbow_targ, thickness_scale=1.0)
    pose_segment_world(arm_obj, f"bip_lowerArm_{side}", f"Bip01_{side}_Hand", elbow_targ, wrist_targ, thickness_scale=1.0)

    mid1_targ = meg_b_pos[f"{pfx}HandMiddle1"]
    pose_segment_world(arm_obj, f"Bip01_{side}_Hand", f"Bip01_{side}_Finger2", wrist_targ, mid1_targ, thickness_scale=1.0)

    fn_map = [(1, "Index"), (2, "Middle"), (3, "Ring"), (4, "Pinky")]
    for fi, fname in fn_map:
        p1 = meg_b_pos[f"{pfx}Hand{fname}1"]
        p2 = meg_b_pos[f"{pfx}Hand{fname}2"]
        p3 = meg_b_pos[f"{pfx}Hand{fname}3"]
        p4 = p3 + (p3 - p2) * 0.95

        pose_segment_world(arm_obj, f"Bip01_{side}_Finger{fi}", f"Bip01_{side}_Finger{fi}1", p1, p2, thickness_scale=0.98)
        pose_segment_world(arm_obj, f"Bip01_{side}_Finger{fi}1", f"Bip01_{side}_Finger{fi}2", p2, p3, thickness_scale=0.98)
        pose_segment_world(arm_obj, f"Bip01_{side}_Finger{fi}2", f"Bip01_{side}_Finger{fi}_tip", p3, p4, thickness_scale=0.98)

    t1 = meg_b_pos[f"{pfx}HandThumb1"]
    t2 = meg_b_pos[f"{pfx}HandThumb2"]
    t3 = meg_b_pos[f"{pfx}HandThumb3"]
    t4 = t3 + (t3 - t2) * 1.05

    pose_segment_world(arm_obj, f"Bip01_{side}_Finger0", f"Bip01_{side}_Finger01", t1, t2, thickness_scale=0.98)
    pose_segment_world(arm_obj, f"Bip01_{side}_Finger01", f"Bip01_{side}_Finger02", t2, t3, thickness_scale=0.98)
    pose_segment_world(arm_obj, f"Bip01_{side}_Finger02", f"Bip01_{side}_Finger0_tip", t3, t4, thickness_scale=0.98)

bpy.context.view_layer.update()

max_finger_err_mm = 0.0
for side, pfx in [("L", "Left"), ("R", "Right")]:
    for fi, fname in [(0, "Thumb"), (1, "Index"), (2, "Middle"), (3, "Ring"), (4, "Pinky")]:
        for k, jname in [(0, "1"), (1, "2"), (2, "3")]:
            b_segment = f"Bip01_{side}_Finger{fi}" if k == 0 else f"Bip01_{side}_Finger{fi}{k}"
            w_p = (arm_obj.matrix_world @ arm_obj.pose.bones[b_segment].matrix).translation
            t_p = meg_b_pos[f"{pfx}Hand{fname}{jname}"]
            err_mm = (w_p - t_p).length * 1000.0
            max_finger_err_mm = max(max_finger_err_mm, err_mm)

print(f"[✓] Max finger joint alignment error across ALL 30 finger hinges: {max_finger_err_mm:.4f} mm!")

bpy.ops.object.mode_set(mode='OBJECT')

# Apply posed armature to mesh to freeze vertices in Megatron's bind pose
bpy.context.view_layer.objects.active = mesh_obj
mesh_obj.select_set(True)
bpy.ops.object.modifier_apply(modifier="Armature")
mesh_obj.parent = None
print("[✓] Posed armature modifier applied to mesh vertices!")

bpy.data.objects.remove(arm_obj, do_unlink=True)

# Remap vertex groups with 100% rigid shin/boot rule
BOOT_Z_THRESH = 0.35 * SCALE # ~0.518m

old_vg_by_index = {vg.index: vg.name for vg in mesh_obj.vertex_groups}
n_verts = len(mesh_obj.data.vertices)
target_weights = {b: [0.0] * n_verts for b in meg_51_data["bone_names"]}

VG_MAP = {
    # Torso & Pelvis
    "bip_pelvis": "Hips",
    "bip_spine_0": "Spine",
    "bip_spine_1": "Spine1",
    "bip_spine_2": "Spine1",
    "bip_backplate": "Spine1",
    "bip_jetpack_0": "Spine1",
    "bip_jetpack_1": "Spine1",
    "bip_wing_L": "Spine1",
    "bip_wing_R": "Spine1",
    "bip_cannon_0": "Spine1",
    "bip_cannon_1": "Spine1",

    # Head & Face
    "bip_neck": "Head",
    "bip_head": "Head",
    "bip_jaw": "Head",
    "bip_lowerLip_1": "Head", "bip_lowerLip_2": "Head", "bip_lowerLip_3": "Head",
    "bip_lowerLip_4": "Head", "bip_lowerLip_5": "Head", "bip_lowerLip_6": "Head",
    "bip_upperLip_1": "Head", "bip_upperLip_2": "Head", "bip_upperLip_3": "Head",
    "bip_upperLip_4": "Head", "bip_upperLip_5": "Head", "bip_upperLip_6": "Head", "bip_upperLip_7": "Head",

    # Upper Legs
    "bip_hip_L": "LeftUpLeg",
    "bip_hip_R": "RightUpLeg",

    # Lower Legs
    "bip_knee_L": "LeftLeg",
    "bip_legWing_L": "LeftLeg",
    "bip_knee_R": "RightLeg",
    "bip_legWing_R": "RightLeg",

    # Arms & Shoulders
    "bip_collar_L": "LeftShoulder",
    "bip_ShoulderPad_L": "LeftShoulder",
    "bip_upperArm_L": "LeftArm",
    "bip_lowerArm_L": "LeftForeArm",

    "bip_collar_R": "RightShoulder",
    "bip_ShoulderPad_R": "RightShoulder",
    "bip_upperArm_R": "RightArm",
    "bip_lowerArm_R": "RightForeArm",

    # Left Hand & 15 Finger Bones
    "Bip01_L_Hand": "LeftHand",
    "bip_knuckke_L1": "LeftHand", "bip_knuckke_L2": "LeftHand", "bip_knuckke_L3": "LeftHand", "bip_knuckke_L4": "LeftHand",
    "Bip01_L_Finger0": "LeftHandThumb1",
    "Bip01_L_Finger01": "LeftHandThumb2",
    "Bip01_L_Finger02": "LeftHandThumb3",
    "Bip01_L_Finger1": "LeftHandIndex1",
    "Bip01_L_Finger11": "LeftHandIndex2",
    "Bip01_L_Finger12": "LeftHandIndex3",
    "Bip01_L_Finger2": "LeftHandMiddle1",
    "Bip01_L_Finger21": "LeftHandMiddle2",
    "Bip01_L_Finger22": "LeftHandMiddle3",
    "Bip01_L_Finger3": "LeftHandRing1",
    "Bip01_L_Finger31": "LeftHandRing2",
    "Bip01_L_Finger32": "LeftHandRing3",
    "Bip01_L_Finger4": "LeftHandPinky1",
    "Bip01_L_Finger41": "LeftHandPinky2",
    "Bip01_L_Finger42": "LeftHandPinky3",

    # Right Hand & 15 Finger Bones
    "Bip01_R_Hand": "RightHand",
    "bip_knuckle_R1": "RightHand", "bip_knuckle_R2": "RightHand", "bip_knuckle_R3": "RightHand", "bip_knuckle_R4": "RightHand",
    "Bip01_R_Finger0": "RightHandThumb1",
    "Bip01_R_Finger01": "RightHandThumb2",
    "Bip01_R_Finger02": "RightHandThumb3",
    "Bip01_R_Finger1": "RightHandIndex1",
    "Bip01_R_Finger11": "RightHandIndex2",
    "Bip01_R_Finger12": "RightHandIndex3",
    "Bip01_R_Finger2": "RightHandMiddle1",
    "Bip01_R_Finger21": "RightHandMiddle2",
    "Bip01_R_Finger22": "RightHandMiddle3",
    "Bip01_R_Finger3": "RightHandRing1",
    "Bip01_R_Finger31": "RightHandRing2",
    "Bip01_R_Finger32": "RightHandRing3",
    "Bip01_R_Finger4": "RightHandPinky1",
    "Bip01_R_Finger41": "RightHandPinky2",
    "Bip01_R_Finger42": "RightHandPinky3",
}

rigid_shin_count = 0
for v in mesh_obj.data.vertices:
    vi = v.index
    vg_names = [old_vg_by_index.get(g.group) for g in v.groups]

    # Rigid Shin Rule: Any vertex that touches the knee bone belongs 100% to the shin!
    # This captures the entire purple tank tread boot (including the 368 overlap vertices)
    # and strictly prevents ankle rotation from bending the shin boot armor like rubber!
    if "bip_knee_L" in vg_names:
        target_weights["LeftLeg"][vi] = 1.0
        rigid_shin_count += 1
        continue
    elif "bip_knee_R" in vg_names:
        target_weights["RightLeg"][vi] = 1.0
        rigid_shin_count += 1
        continue

    # Pure foot and toe vertices (below the shin boot)
    if "bip_toe_L" in vg_names:
        target_weights["LeftToeBase"][vi] = 1.0
        continue
    elif "bip_toe_R" in vg_names:
        target_weights["RightToeBase"][vi] = 1.0
        continue
    elif "bip_foot_L" in vg_names:
        target_weights["LeftFoot"][vi] = 1.0
        continue
    elif "bip_foot_R" in vg_names:
        target_weights["RightFoot"][vi] = 1.0
        continue

    for g in v.groups:
        old_vg_name = old_vg_by_index.get(g.group)
        if old_vg_name in VG_MAP:
            target_bone = VG_MAP[old_vg_name]
            target_weights[target_bone][vi] += g.weight

print(f"[✓] Rigid Shin Rule: {rigid_shin_count} boot vertices forced 100% rigid on LeftLeg/RightLeg (zero foot weight leakage)!")

# Normalize weights
for vi in range(n_verts):
    tot = sum(target_weights[b][vi] for b in meg_51_data["bone_names"])
    if tot > 1e-6:
        for b in meg_51_data["bone_names"]:
            target_weights[b][vi] /= tot
    else:
        target_weights["Hips"][vi] = 1.0

# Clear old VGs and create 51 authoritative VGs
mesh_obj.vertex_groups.clear()
for bname in meg_51_data["bone_names"]:
    vg = mesh_obj.vertex_groups.new(name=bname)
    w_list = target_weights[bname]
    for vi, w in enumerate(w_list):
        if w > 0.001:
            vg.add([vi], w, 'REPLACE')

print(f"[✓] Remapped {n_verts} vertices to 51 Megatron G1 bone vertex groups")

# Build Megatron authoritative 51-bone Armature
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
    eb.tail = head_pos + Vector((0, -0.08, 0))
    edit_bones[bname] = eb

for bname in meg_51_data["bone_names"]:
    b_info = meg_51_data["bones"][bname]
    parent_name = b_info.get("parent")
    if parent_name and parent_name in edit_bones and parent_name != bname:
        eb = edit_bones[bname]
        eb.parent = edit_bones[parent_name]
        diff = eb.head - edit_bones[parent_name].head
        if diff.length > 0.04 and any(k in parent_name for k in ["Thumb", "Index", "Middle", "Ring", "Pinky", "Arm", "Leg"]):
            edit_bones[parent_name].tail = eb.head

bpy.ops.object.mode_set(mode='OBJECT')

mesh_obj.parent = new_arm_obj
mod = mesh_obj.modifiers.new("Armature", "ARMATURE")
mod.object = new_arm_obj

out_humanoid_fbx = UNITY_BW_DIR / "blitzwing_robot.fbx"
bpy.ops.object.select_all(action='DESELECT')
new_arm_obj.select_set(True)
mesh_obj.select_set(True)
bpy.context.view_layer.objects.active = new_arm_obj

bpy.ops.export_scene.fbx(
    filepath=str(out_humanoid_fbx),
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
print(f"[✓] Exported posed 30-finger articulated FBX: {out_humanoid_fbx} ({out_humanoid_fbx.stat().st_size} bytes)")


# =========================================================================
# 2. PROCESS TANK MODE
# =========================================================================
print("\n=== 2. PROCESSING BLITZWING TANK MODE ===")
bpy.ops.wm.open_mainfile(filepath=str(BLEND_SRC))

tank_mesh = bpy.data.objects['Blitzwing_Alt_Tank']
for o in list(bpy.data.objects):
    if o != tank_mesh:
        bpy.data.objects.remove(o, do_unlink=True)

tank_mesh.modifiers.clear()
tank_mesh.parent = None
tank_mesh.matrix_world = Matrix.Identity(4)

weld_and_clean_normals(tank_mesh, 40.0)

min_x = min(v.co.x for v in tank_mesh.data.vertices)
max_x = max(v.co.x for v in tank_mesh.data.vertices)
cx = (min_x + max_x) / 2.0
print(f"Centering Tank by X={-cx:.4f}...")
tank_mesh.data.transform(Matrix.Translation((-cx, 0, 0)))

min_z = min(v.co.z for v in tank_mesh.data.vertices)
tank_mesh.data.transform(Matrix.Translation((0, 0, -min_z)))
tank_mesh.data.update()

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
    parent_name = b_info.get("parent")
    if parent_name and parent_name in tank_edit_bones and parent_name != bname:
        tank_edit_bones[bname].parent = tank_edit_bones[parent_name]

bpy.ops.object.mode_set(mode='OBJECT')

tank_n_verts = len(tank_mesh.data.vertices)
tank_target_weights = {b: [0.0] * tank_n_verts for b in meg_tank_data["bone_names"]}
tank_old_vg = {vg.index: vg.name for vg in tank_mesh.vertex_groups}

for v in tank_mesh.data.vertices:
    vi = v.index
    for g in v.groups:
        nm = tank_old_vg.get(g.group, "")
        if "top" in nm.lower() or "cannon" in nm.lower():
            tank_target_weights["chop1_cannon_right"][vi] += g.weight
        else:
            tank_target_weights["chop2_torso_main_center"][vi] += g.weight

for vi in range(tank_n_verts):
    tot = sum(tank_target_weights[b][vi] for b in meg_tank_data["bone_names"])
    if tot > 1e-6:
        for b in meg_tank_data["bone_names"]:
            tank_target_weights[b][vi] /= tot
    else:
        tank_target_weights["chop2_torso_main_center"][vi] = 1.0

tank_mesh.vertex_groups.clear()
for bname in meg_tank_data["bone_names"]:
    vg = tank_mesh.vertex_groups.new(name=bname)
    w_list = tank_target_weights[bname]
    for vi, w in enumerate(w_list):
        if w > 0.001:
            vg.add([vi], w, 'REPLACE')

tank_mesh.parent = tank_arm_obj
t_mod = tank_mesh.modifiers.new("Armature", "ARMATURE")
t_mod.object = tank_arm_obj

out_tank_fbx = UNITY_BW_DIR / "blitzwing_tank.fbx"
bpy.ops.object.select_all(action='DESELECT')
tank_arm_obj.select_set(True)
tank_mesh.select_set(True)
bpy.context.view_layer.objects.active = tank_arm_obj

bpy.ops.export_scene.fbx(
    filepath=str(out_tank_fbx),
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
# 3. PROCESS JET MODE
# =========================================================================
print("\n=== 3. PROCESSING BLITZWING JET MODE ===")
bpy.ops.wm.open_mainfile(filepath=str(BLEND_SRC))

jet_mesh = bpy.data.objects['Blitzwing_Jet Mode']
for o in list(bpy.data.objects):
    if o != jet_mesh:
        bpy.data.objects.remove(o, do_unlink=True)

jet_mesh.modifiers.clear()
jet_mesh.parent = None
jet_mesh.matrix_world = Matrix.Identity(4)

weld_and_clean_normals(jet_mesh, 40.0)

min_x = min(v.co.x for v in jet_mesh.data.vertices)
max_x = max(v.co.x for v in jet_mesh.data.vertices)
cx = (min_x + max_x) / 2.0
print(f"Centering Jet by X={-cx:.4f}...")
jet_mesh.data.transform(Matrix.Translation((-cx, 0, 0)))

min_z = min(v.co.z for v in jet_mesh.data.vertices)
jet_mesh.data.transform(Matrix.Translation((0, 0, -min_z)))
jet_mesh.data.update()

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
    parent_name = b_info.get("parent")
    if parent_name and parent_name in jet_edit_bones and parent_name != bname:
        jet_edit_bones[bname].parent = jet_edit_bones[parent_name]

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
bpy.ops.object.select_all(action='DESELECT')
jet_arm_obj.select_set(True)
jet_mesh.select_set(True)
bpy.context.view_layer.objects.active = jet_arm_obj

bpy.ops.export_scene.fbx(
    filepath=str(out_jet_fbx),
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
print("\n=== ALL 3 BLITZWING MODELS SUCCESSFULLY EXPORTED TO UNITY! ===")
