import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import math
import shutil
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DONOR_BP_JSON = ROOT_DIR / "tools/swoop/ramjet_78_authoritative_bindposes.json"
FBX_SRC = ROOT_DIR / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"
FBX_OUT_DIR = ROOT_DIR / "3rd-party-models/swoop/03_fbx"
FBX_OUT_DIR.mkdir(parents=True, exist_ok=True)
UNITY_OUT_DIR = ROOT_DIR / "toolchain/unity_build_project/Assets/Swoop"
UNITY_OUT_DIR.mkdir(parents=True, exist_ok=True)

print("=== [Swoop] Stage 2: Building Aligned Robot FBX from Static Pose (Curled Fists + Shoulder-Arm Lock) ===")

with open(DONOR_BP_JSON, "r", encoding="utf-8") as f:
    donor_data = json.load(f)

donor_bones = donor_data["bones"]
donor_bone_names = donor_data["bone_names"]
print(f"Loaded {len(donor_bone_names)} donor bones from {DONOR_BP_JSON}")

# Convert Unity world pos to Blender coords: bx = -ux, by = -uz, bz = uy
donor_blender_pos = {}
for bname, binfo in donor_bones.items():
    ux, uy, uz = binfo["unity_world_pos"]
    donor_blender_pos[bname] = Vector((-ux, -uz, uy))

donor_parent_map = {}
for bname, binfo in donor_bones.items():
    p = binfo["parent"]
    donor_parent_map[bname] = p if p != "None" and p != "Reference" else None

# Clean scene & import source FBX
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

swoop_mesh = bpy.data.objects.get("Swoop.001")
sym_mesh = bpy.data.objects.get("Symbol_AB")
arm = bpy.data.objects.get("Bip001")

assert swoop_mesh is not None and arm is not None, "Missing Swoop.001 mesh or Bip001 armature!"

# Capture Symbol_AB transform relative to Swoop.001 mesh space BEFORE clearing transforms
rel_sym_mat = swoop_mesh.matrix_world.inverted() @ sym_mesh.matrix_world if sym_mesh else Matrix.Identity(4)

# Reset Bip001 to pure Static Pose (no vehicle/idle animation attached)
arm.animation_data_clear()
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.select_all(action='SELECT')
bpy.ops.pose.transforms_clear()

mat_arm_to_mesh = swoop_mesh.matrix_world.inverted() @ arm.matrix_world
rot_arm_to_mesh = mat_arm_to_mesh.to_3x3()


def pose_bone_mesh_quat(bname: str, q_tuple):
    pb = arm.pose.bones.get(bname)
    if pb:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = Quaternion(q_tuple).normalized()


def pose_bone_mesh_axis_curl(bname: str, mesh_axis: Vector, angle_deg: float):
    pb = arm.pose.bones.get(bname)
    if not pb:
        return
    bone_in_mesh = (rot_arm_to_mesh @ pb.bone.matrix_local.to_3x3()).normalized()
    local_axis = (bone_in_mesh.inverted() @ mesh_axis.normalized()).normalized()
    pb.rotation_mode = 'QUATERNION'
    pb.rotation_quaternion = Quaternion(local_axis, math.radians(angle_deg))


def pose_bone_mesh_translate(bname: str, mesh_delta: Vector):
    pb = arm.pose.bones.get(bname)
    if not pb:
        return
    bone_in_mesh = (rot_arm_to_mesh @ pb.bone.matrix_local.to_3x3()).normalized()
    pb.location = bone_in_mesh.inverted() @ mesh_delta


# 1) Curl BOTH Left and Right hands into tight, solid, symmetrical combat fists
# Left hand uses clean local Z curl (verified in debug_blender_fists.png)
LEFT_FIST_QUATS = {
    'Bone_L_Finger0': (0.996808, 0.001097, -0.078611, -0.013909),
    'Bone_L_Finger01': (0.985, 0.0, 0.0, 0.174),
    'Bone_L_Finger02': (0.924, 0.0, 0.0, 0.383),
    'Bone_L_Finger1': (0.906, 0.0, 0.0, 0.423),
    'Bone_L_Finger11': (0.887, 0.0, 0.0, 0.462),
    'Bone_L_Finger12': (0.906, 0.0, 0.0, 0.423),
    'Bone_L_Finger2': (0.906, 0.0, 0.0, 0.423),
    'Bone_L_Finger21': (0.887, 0.0, 0.0, 0.462),
    'Bone_L_Finger22': (0.887, 0.0, 0.0, 0.462),
}
for bn, qt in LEFT_FIST_QUATS.items():
    pose_bone_mesh_quat(bn, qt)
    # Mirror Left thumb (Finger0/01/02) exactly across X=0 onto Right thumb so both thumbs clench symmetrically!
    if "Finger0" in bn:
        pb_l = arm.pose.bones.get(bn)
        if pb_l:
            q_l = Quaternion(qt).normalized()
            ax_local, angle = q_l.to_axis_angle()
            bm_l = (rot_arm_to_mesh @ pb_l.bone.matrix_local.to_3x3()).normalized()
            ax_mesh_l = (bm_l @ ax_local).normalized()
            ax_mesh_r = Vector((-ax_mesh_l.x, ax_mesh_l.y, ax_mesh_l.z)).normalized()
            pose_bone_mesh_axis_curl(bn.replace("Bone_L_", "Bone_R_"), ax_mesh_r, -math.degrees(angle))

# Right hand fingers 1/2 use mesh-space axis curl so mirrored Bip001 axes never curl backwards
for bn, deg in [
    ("Bone_R_Finger1", 65), ("Bone_R_Finger11", 75), ("Bone_R_Finger12", 65),
    ("Bone_R_Finger2", 65), ("Bone_R_Finger21", 80), ("Bone_R_Finger22", 75),
]:
    pose_bone_mesh_axis_curl(bn, Vector((0.0, -1.0, 0.0)), deg)

# 2) Extend both clenched fists slightly below forearm armor cuffs (-0.042m raw ~= -0.15m scaled)
# Forearm cuffs still cover top 0.14m raw of hand root -> solid wrist with prominent protruding fists
pose_bone_mesh_translate("Bone_L_Hand", Vector((0.0, 0.0, -0.042)))
pose_bone_mesh_translate("Bone_R_Hand", Vector((0.0, 0.0, -0.042)))

# 3) Widen shoulders slightly (+0.075m raw ~= +0.26m scaled -> arm axis X = +-2.13m vs Ramjet +-2.33m)
# Keeps Bone_L/R_Clavicle02 overlapping Bone_L/R_Clavicle01 by ~0.115m raw (~0.40m scaled) with zero gap!
pose_bone_mesh_translate("Bone_L_Clavicle02", Vector((+0.075, 0.0, 0.0)))
pose_bone_mesh_translate("Bip001 L UpperArm", Vector((+0.075, 0.0, 0.0)))
pose_bone_mesh_translate("Bone_R_Clavicle02", Vector((-0.075, 0.0, 0.0)))
pose_bone_mesh_translate("Bip001 R UpperArm", Vector((-0.075, 0.0, 0.0)))

bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()

# Evaluate deformed Static Pose + clenched fists into clean mesh datablock (in swoop_mesh local space)
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = swoop_mesh.evaluated_get(depsgraph)
baked_mesh_data = bpy.data.meshes.new_from_object(eval_obj)
baked_swoop = bpy.data.objects.new("Swoop_Baked", baked_mesh_data)
bpy.context.scene.collection.objects.link(baked_swoop)
baked_swoop.matrix_world = Matrix.Identity(4)

# Copy vertex groups and weights from original Swoop.001
for vg in swoop_mesh.vertex_groups:
    baked_swoop.vertex_groups.new(name=vg.name)
vg_name_by_idx = {vg.index: vg.name for vg in swoop_mesh.vertex_groups}
for v in swoop_mesh.data.vertices:
    for g in v.groups:
        vgn = vg_name_by_idx.get(g.group)
        if vgn:
            baked_swoop.vertex_groups[vgn].add([v.index], g.weight, 'REPLACE')

# Detach Symbol_AB and apply its exact relative transform into baked mesh local space
if sym_mesh:
    sym_mesh.modifiers.clear()
    sym_mesh.parent = None
    sym_mesh.matrix_world = Matrix.Identity(4)
    sym_mesh.data.transform(rel_sym_mat)
    sym_mesh.data.update()

# Remove all other objects (Shadow, Swoop_Weapon, Symbol_DC, Bip001, original Swoop.001, empties)
keep_objs = {baked_swoop, sym_mesh}
for o in list(bpy.data.objects):
    if o not in keep_objs and o is not None:
        bpy.data.objects.remove(o, do_unlink=True)

swoop_mesh = baked_swoop

# Scale by 3.50x (matching shoulder pivot height 8.95m == Ramjet LeftArm 8.917m, Head 9.62m == Ramjet Head 9.499m!)
# Center X/Y on torso pelvis & ground min_z strictly at Z = 0.00m
vs = [v.co for v in swoop_mesh.data.vertices]
min_x, max_x = min(v.x for v in vs), max(v.x for v in vs)
min_y, max_y = min(v.y for v in vs), max(v.y for v in vs)
min_z, max_z = min(v.z for v in vs), max(v.z for v in vs)
scale_factor = 3.50
print(f"Raw Static Pose: Z=[{min_z:.3f}, {max_z:.3f}] (h={max_z-min_z:.3f}m) -> shoulder-aligned scale_factor={scale_factor:.4f}")

center_x = (min_x + max_x) / 2
# Keep Y centered near pelvis/spine rather than wing tips so torso Z/Y stays anchored near X/Y=0
pelvis_vg = swoop_mesh.vertex_groups.get("Bone_Pelvis")
pelvis_ys = [v.co.y for v in swoop_mesh.data.vertices if pelvis_vg and any(g.group == pelvis_vg.index and g.weight > 0.5 for g in v.groups)]
center_y = (sum(pelvis_ys) / len(pelvis_ys)) if pelvis_ys else (min_y + max_y) / 2

mat_xform = Matrix.Translation(Vector((-center_x * scale_factor, -center_y * scale_factor, -min_z * scale_factor))) @ Matrix.Scale(scale_factor, 4)

swoop_mesh.data.transform(mat_xform)
swoop_mesh.data.update()
if sym_mesh:
    sym_mesh.data.transform(mat_xform)
    sym_mesh.data.update()

vs_new = [v.co for v in swoop_mesh.data.vertices]
print(f"[✓] Scaled Swoop Robot: X=[{min(v.x for v in vs_new):.2f}, {max(v.x for v in vs_new):.2f}], Z=[{min(v.z for v in vs_new):.2f}, {max(v.z for v in vs_new):.2f}]")

# Authoritative Vertex Group Mapping (Swoop Native -> Ramjet 78 Bones)
# CRITICAL: Both Bone_L/R_Clavicle02 AND Bone_L/R_UpperArm bind to LeftArm/RightArm so bicep NEVER disconnects from shoulder armor!
SWOOP_TO_RAMJET_BONES = {
    # Pelvis & Spine
    "Bone_Pelvis": "Hips",
    "Bip001 Spine": "Spine",
    "Bip001 Spine1": "Spine1",
    "Bone_Spine1": "Spine1",
    "Back": "Spine1",
    "bird_chest": "Spine1",

    # Head & Neck & Folded Beak
    "Bip001 Neck": "Neck",
    "Bip001 Head": "Head",
    "Bone_Head": "Head",
    "bird_Head": "Spine1",
    "bird_Head_02": "Spine1",
    "beak": "Spine1",
    "beak_the bottom": "Spine1",
    "bird_neck": "Spine1",

    # Left Arm (Shoulder Pad + UpperArm locked rigidly to LeftArm)
    "Bone_L_Clavicle01": "Spine1",
    "Bone_L_Clavicle02": "LeftArm",
    "Bone_L_UpperArm": "LeftArm",
    "Bone_L_Forearm": "LeftForeArm",
    "Bone_L_Hand": "LeftHand",

    # Left Hand & Curled Fist Fingers (Track B: locked to LeftHand)
    "Bone_L_Finger0": "LeftHand",
    "Bone_L_Finger01": "LeftHand",
    "Bone_L_Finger02": "LeftHand",
    "Bone_L_Finger1": "LeftHand",
    "Bone_L_Finger11": "LeftHand",
    "Bone_L_Finger12": "LeftHand",
    "Bone_L_Finger2": "LeftHand",
    "Bone_L_Finger21": "LeftHand",
    "Bone_L_Finger22": "LeftHand",

    # Left Wings & Missile (Anchored to Spine1)
    "Bone_L_Wing_01(mirrored)": "Spine1",
    "Bone_L_Wing_02(mirrored)": "Spine1",
    "L_missile": "Spine1",

    # Right Arm (Shoulder Pad + UpperArm locked rigidly to RightArm)
    "Bone_R_Clavicle01": "Spine1",
    "Bone_R_Clavicle02": "RightArm",
    "Bone_R_UpperArm": "RightArm",
    "Bone_R_Forearm": "RightForeArm",
    "Bone_R_Hand": "RightHand",

    # Right Hand & Curled Fist Fingers (Track B: locked to RightHand)
    "Bone_R_Finger0": "RightHand",
    "Bone_R_Finger01": "RightHand",
    "Bone_R_Finger02": "RightHand",
    "Bone_R_Finger1": "RightHand",
    "Bone_R_Finger11": "RightHand",
    "Bone_R_Finger12": "RightHand",
    "Bone_R_Finger2": "RightHand",
    "Bone_R_Finger21": "RightHand",
    "Bone_R_Finger22": "RightHand",

    # Right Wings & Missile (Anchored to Spine1)
    "Bone_R_Wing_01": "Spine1",
    "Bone_R_Wing_02": "Spine1",
    "R_missile": "Spine1",

    # Left Leg
    "Bip001 L Thigh": "LeftUpLeg",
    "Bone_L_Thigh": "LeftUpLeg",
    "Bone_L_Thigh001": "LeftUpLeg",
    "Bone_L_Thigh002": "LeftUpLeg",
    "Bone_L_Thigh003": "LeftUpLeg",
    "Bone_L_Thigh004": "LeftUpLeg",
    "Bone_L_Calf": "LeftLeg",
    "Bone_L_Foot00": "LeftFoot",

    # Right Leg
    "Bip001 R Thigh": "RightUpLeg",
    "Bone_R_Thigh": "RightUpLeg",
    "Bone_R_Thigh001(mirrored)": "RightUpLeg",
    "Bone_R_Thigh002(mirrored)": "RightUpLeg",
    "Bone_R_Thigh003(mirrored)": "RightUpLeg",
    "Bone_R_Thigh004(mirrored)": "RightUpLeg",
    "Bone_R_Calf": "RightLeg",
    "Bone_R_Foot00": "RightFoot",
}

# Remap vertex weights with hard-surface snap (w >= 0.65 -> 1.0)
old_vg_names = [vg.name for vg in swoop_mesh.vertex_groups]
vert_weights = [{} for _ in range(len(swoop_mesh.data.vertices))]

for v in swoop_mesh.data.vertices:
    for g in v.groups:
        if g.group < len(old_vg_names):
            vg_name = old_vg_names[g.group]
            target_bone = SWOOP_TO_RAMJET_BONES.get(vg_name)
            if target_bone:
                vert_weights[v.index][target_bone] = vert_weights[v.index].get(target_bone, 0.0) + g.weight

for vi, wdict in enumerate(vert_weights):
    if not wdict:
        v_co = swoop_mesh.data.vertices[vi].co
        if v_co.z > 9.0:
            wdict["Head"] = 1.0
        elif v_co.z > 6.5:
            wdict["Spine1"] = 1.0
        elif v_co.z > 4.5:
            wdict["Hips"] = 1.0
        elif v_co.z > 2.0:
            wdict["LeftLeg" if v_co.x >= 0 else "RightLeg"] = 1.0
        else:
            wdict["LeftFoot" if v_co.x >= 0 else "RightFoot"] = 1.0

swoop_mesh.vertex_groups.clear()
new_vg_map = {bname: swoop_mesh.vertex_groups.new(name=bname) for bname in donor_bone_names}

for vi, wdict in enumerate(vert_weights):
    max_b = max(wdict, key=wdict.get)
    max_w = wdict[max_b]
    if max_w >= 0.65:
        wdict = {max_b: 1.0}
    else:
        tot = sum(wdict.values())
        if tot > 0:
            wdict = {k: v / tot for k, v in wdict.items()}
    for b, w in wdict.items():
        if b in new_vg_map:
            new_vg_map[b].add([vi], w, 'REPLACE')

print("[✓] Swoop vertex groups remapped to Ramjet 78 bones (LeftArm/RightArm locked, Curled Fists on LeftHand/RightHand).")

# Assign single material slot "M_Swoop_Main" on body BEFORE join
main_mat = bpy.data.materials.new("M_Swoop_Main")
emblem_mat = bpy.data.materials.new("M_Swoop_Emblem")
swoop_mesh.data.materials.clear()
swoop_mesh.data.materials.append(main_mat)
for p in swoop_mesh.data.polygons:
    p.material_index = 0

body_uv_name = swoop_mesh.data.uv_layers.active.name  # "UV0"

# Remap UVs on swoop_mesh into Body tile [0.004, 0.746] x [0.254, 0.996]
uvl_body = swoop_mesh.data.uv_layers.active.data
for p in swoop_mesh.data.polygons:
    for li in p.loop_indices:
        u, v = uvl_body[li].uv
        cu = min(max(u, 0.004), 0.996)
        cv = min(max(v, 0.004), 0.996)
        uvl_body[li].uv = (0.004 + cu * (0.746 - 0.004), 0.254 + cv * (0.996 - 0.254))

print("[✓] All body polygon UVs cleanly remapped and clamped into 2048 atlas tiles.")

# Process Symbol_AB (Autobot Chest Emblem):
# - Bind 100% to Spine1
# - Nudge proud of chest beak (-Y forward) to eliminate Z-fighting
# - Write into exact same UV0 layer name as body so join() never creates a stale UV1
# - Split M_Symbol_AB (red face crest -> Slot 1 M_Swoop_Emblem) vs M_Symbol_Black (shield backing -> Slot 0 M_Swoop_Main)
if sym_mesh:
    sym_mesh.vertex_groups.clear()
    for bname in donor_bone_names:
        sym_mesh.vertex_groups.new(name=bname)
    sp1_vg = sym_mesh.vertex_groups["Spine1"]
    all_vis = list(range(len(sym_mesh.data.vertices)))
    sp1_vg.add(all_vis, 1.0, 'REPLACE')

    # Find which raw material index is M_Symbol_AB vs M_Symbol_Black
    crest_raw_idx = 0
    for mi, mat in enumerate(sym_mesh.data.materials):
        if mat and "black" in mat.name.lower():
            continue
        if mat and "ab" in mat.name.lower():
            crest_raw_idx = mi

    # Nudge proud of chest beak: whole badge -0.025m in Y, and red face crest -0.012m extra in Y
    crest_verts = set()
    for p in sym_mesh.data.polygons:
        if p.material_index == crest_raw_idx:
            for vi in p.vertices:
                crest_verts.add(vi)
    for vi, v in enumerate(sym_mesh.data.vertices):
        v.co.y -= 0.025
        if vi in crest_verts:
            v.co.y -= 0.012
    sym_mesh.data.update()

    # Reassign polygons: crest -> slot 1 (M_Swoop_Emblem), black backing -> slot 0 (M_Swoop_Main)
    is_crest_poly = [p.material_index == crest_raw_idx for p in sym_mesh.data.polygons]
    sym_mesh.data.materials.clear()
    sym_mesh.data.materials.append(main_mat)
    sym_mesh.data.materials.append(emblem_mat)
    for p, is_crest in zip(sym_mesh.data.polygons, is_crest_poly):
        p.material_index = 1 if is_crest else 0

    while sym_mesh.data.uv_layers:
        sym_mesh.data.uv_layers.remove(sym_mesh.data.uv_layers[0])
    sym_uv_layer = sym_mesh.data.uv_layers.new(name=body_uv_name)
    uvl = sym_uv_layer.data
    for p, is_crest in zip(sym_mesh.data.polygons, is_crest_poly):
        target_uv = (0.875, 0.6875) if is_crest else (0.875, 0.5625)
        for li in p.loop_indices:
            uvl[li].uv = target_uv

    pts = [v.co for v in sym_mesh.data.vertices]
    s_min_z, s_max_z = min(p.z for p in pts), max(p.z for p in pts)
    s_min_y = min(p.y for p in pts)
    print(f"[✓] Symbol_AB ({len(all_vis)} verts, {sum(is_crest_poly)} crest + {len(is_crest_poly)-sum(is_crest_poly)} backing polys) proud at Y={s_min_y:.3f}m Z=[{s_min_z:.2f}, {s_max_z:.2f}] on '{body_uv_name}' -> SubMesh 0/1.")

# Join swoop_mesh and sym_mesh into unified mesh (preserves 2 material slots + 1 UV0 layer!)
bpy.ops.object.select_all(action='DESELECT')
swoop_mesh.select_set(True)
if sym_mesh:
    sym_mesh.select_set(True)
bpy.context.view_layer.objects.active = swoop_mesh
bpy.ops.object.join()

unified_mesh = swoop_mesh
unified_mesh.name = "cha_swoop_robot"
assert len(unified_mesh.data.uv_layers) == 1, f"Expected 1 UV layer, got {[u.name for u in unified_mesh.data.uv_layers]}"
assert len(unified_mesh.data.materials) == 2, f"Expected 2 materials, got {[m.name for m in unified_mesh.data.materials]}"

# Build Ramjet's clean 78-bone Armature
arm_data = bpy.data.armatures.new("Ramjet_78_Armature")
new_arm = bpy.data.objects.new("cha_swoop_robot_Armature", arm_data)
bpy.context.scene.collection.objects.link(new_arm)
bpy.context.view_layer.objects.active = new_arm
bpy.ops.object.mode_set(mode='EDIT')

edit_bones = {}
for bname in donor_bone_names:
    eb = arm_data.edit_bones.new(bname)
    head_pos = donor_blender_pos[bname]
    eb.head = head_pos
    eb.tail = head_pos + Vector((0.0, 0.0, 0.1))
    edit_bones[bname] = eb

for bname, eb in edit_bones.items():
    pname = donor_parent_map.get(bname)
    if pname and pname in edit_bones:
        eb.parent = edit_bones[pname]
        delta = eb.head - eb.parent.head
        if delta.length > 0.05 and (eb.parent.tail - eb.parent.head).length < 0.2:
            eb.parent.tail = eb.parent.head + delta * 0.35

bpy.ops.object.mode_set(mode='OBJECT')

unified_mesh.modifiers.clear()
arm_mod = unified_mesh.modifiers.new(name="Armature", type='ARMATURE')
arm_mod.object = new_arm
unified_mesh.parent = new_arm

# Verify Left/Right X axis parity & joint alignment
for b_chk, expect_pos in [("LeftArm", True), ("RightArm", False), ("LeftHand", True), ("RightHand", False)]:
    vg = unified_mesh.vertex_groups.get(b_chk)
    assert vg, f"Missing {b_chk} vertex group!"
    pts = [v.co for v in unified_mesh.data.vertices if any(g.group == vg.index and g.weight > 0.4 for g in v.groups)]
    mx = sum(p.x for p in pts) / len(pts)
    mz = sum(p.z for p in pts) / len(pts)
    print(f"  {b_chk:10s}: n={len(pts):4d}, mean_X={mx:+.3f}m, mean_Z={mz:.3f}m (donor X={donor_blender_pos[b_chk].x:+.3f}, Z={donor_blender_pos[b_chk].z:.3f})")
    if expect_pos:
        assert mx > 0.5, f"{b_chk} mean X ({mx:.3f}) not > +0.5!"
    else:
        assert mx < -0.5, f"{b_chk} mean X ({mx:.3f}) not < -0.5!"

# Export FBX
out_fbx = FBX_OUT_DIR / "swoop_prepared.fbx"
unity_fbx = UNITY_OUT_DIR / "swoop_prepared.fbx"

bpy.ops.object.select_all(action='DESELECT')
new_arm.select_set(True)
unified_mesh.select_set(True)
bpy.context.view_layer.objects.active = new_arm

bpy.ops.export_scene.fbx(
    filepath=str(out_fbx),
    use_selection=True,
    global_scale=1.0,
    apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_ALL',
    bake_space_transform=False,
    object_types={'ARMATURE', 'MESH'},
    use_mesh_modifiers=True,
    mesh_smooth_type='FACE',
    add_leaf_bones=False,
    primary_bone_axis='Y',
    secondary_bone_axis='X',
    armature_nodetype='NULL',
    axis_forward='-Z',
    axis_up='Y',
)
print(f"[✓] Exported robot FBX to {out_fbx} ({out_fbx.stat().st_size / (1024*1024):.2f} MB)")

shutil.copyfile(str(out_fbx), str(unity_fbx))
print(f"[✓] Synced robot FBX to Unity: {unity_fbx}")
print("=== Stage 2 Robot FBX Build Complete & Verified! ===")
