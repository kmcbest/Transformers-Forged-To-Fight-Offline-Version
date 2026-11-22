import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math
from mathutils import Vector, Matrix
import json
from pathlib import Path
import numpy as np

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = str(ROOT / "3rd-party-models" / "BlastOff" / "01_extracted" / "source" / "transformers fall of cybertron convaticons .fbx")
if not Path(FBX_PATH).exists():
    FBX_PATH = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
DONOR_JSON = ROOT / "3rd-party-models" / "BlastOff" / "00_donor_reference" / "donor_summary.json"

BLASTOFF_MESH_NAMES = [
    "RB_Blastoff_CHARSKEL_Head.001.dmx",
    "RB_Blastoff_CHARSKEL_ArmLoL.001.dmx",
    "RB_Blastoff_CHARSKEL_ArmLoR.001.dmx",
    "RB_BlastoffWing_STAT.001.dmx",
    "RB_BlastoffWing_STAT.dmx",
]

def unity_to_blender(upos):
    return Vector((-float(upos[0]), -float(upos[2]), float(upos[1])))

def load_megatronus_bones():
    donor = json.loads(DONOR_JSON.read_text(encoding="utf-8"))
    mesh_00 = donor["meshes"]["cha_megatronus_gs_kabam_00"]
    avatar_tos = donor["avatars"]["cha_megatronus_gs_kabam_00Avatar"]["tos"]
    pos_b = {}
    for idx, (h, bp) in enumerate(zip(mesh_00["boneHashes"], mesh_00["bindposes"])):
        mat = np.array([
            [bp["e00"], bp["e01"], bp["e02"], bp["e03"]],
            [bp["e10"], bp["e11"], bp["e12"], bp["e13"]],
            [bp["e20"], bp["e21"], bp["e22"], bp["e23"]],
            [bp["e30"], bp["e31"], bp["e32"], bp["e33"]],
        ])
        inv_mat = np.linalg.inv(mat)
        upos = inv_mat[:3, 3]
        bname = avatar_tos.get(str(h), f"bone_{idx}").split("/")[-1]
        pos_b[bname] = unity_to_blender(upos)
    return pos_b

def pose_segment_world(arm_obj, bone_name, child_name, target_head_w, target_tail_w, thickness_scale=1.0, preserve_length=False):
    bpy.context.view_layer.update()
    pb = arm_obj.pose.bones[bone_name]
    w_old = arm_obj.matrix_world @ pb.matrix
    p_head_old = (arm_obj.matrix_world @ pb.head).copy()
    if child_name and child_name in arm_obj.pose.bones:
        p_tail_old = (arm_obj.matrix_world @ arm_obj.pose.bones[child_name].head).copy()
    else:
        p_tail_old = (arm_obj.matrix_world @ pb.tail).copy()

    v_old = p_tail_old - p_head_old
    v_new = target_tail_w - target_head_w
    if v_old.length < 1e-4 or v_new.length < 1e-4:
        return

    q_rot = v_old.rotation_difference(v_new)
    s_len = 1.0 if preserve_length else (v_new.length / v_old.length)
    s_len = max(0.2, min(5.0, s_len))

    d = v_old.normalized()
    S = Matrix.Identity(3) * thickness_scale
    for r in range(3):
        for c in range(3):
            S[r][c] += (s_len - thickness_scale) * d[r] * d[c]

    R_new = q_rot.to_matrix() @ S @ w_old.to_3x3()
    M_new_w = R_new.to_4x4()
    M_new_w.translation = target_head_w
    pb.matrix = arm_obj.matrix_world.inverted() @ M_new_w
    bpy.context.view_layer.update()

def pb_head_w(arm_obj, bname):
    bpy.context.view_layer.update()
    return arm_obj.matrix_world @ arm_obj.pose.bones[bname].head

bpy.ops.wm.read_factory_settings(use_empty=True)
meg_pos = load_megatronus_bones()
bpy.ops.import_scene.fbx(filepath=FBX_PATH)

arm = bpy.data.objects.get("Blast-off_ARM")
robot_objs = [bpy.data.objects[n] for n in BLASTOFF_MESH_NAMES if n in bpy.data.objects]

keep_objs = set(robot_objs) | {arm}
for o in list(bpy.data.objects):
    if o not in keep_objs:
        bpy.data.objects.remove(o, do_unlink=True)

# 0. Center Blast Off
arm.location.y += 10.0118
for obj in robot_objs:
    obj.location.y += 10.0118

# 1. R_z(-90)
R_z90 = Matrix.Rotation(math.radians(-90), 4, 'Z')
arm.matrix_world = R_z90 @ arm.matrix_world
for obj in robot_objs:
    obj.matrix_world = R_z90 @ obj.matrix_world
bpy.context.view_layer.update()

bpy.ops.object.select_all(action="DESELECT")
for obj in robot_objs:
    obj.select_set(True)
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 2. Scale 2.2928x
SCALE_BLASTOFF = 2.2928
arm.scale = (SCALE_BLASTOFF, SCALE_BLASTOFF, SCALE_BLASTOFF)
for obj in robot_objs:
    obj.scale = (SCALE_BLASTOFF, SCALE_BLASTOFF, SCALE_BLASTOFF)
bpy.ops.object.select_all(action="DESELECT")
for obj in robot_objs:
    obj.select_set(True)
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Attach Armature modifier
for obj in robot_objs:
    arm_mod = obj.modifiers.get("Armature")
    if not arm_mod:
        arm_mod = obj.modifiers.new("Armature", "ARMATURE")
    arm_mod.object = arm

# Enter POSE mode
bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="POSE")

# STEP A: POSE PELVIS FIRST (Root of everything!)
pose_segment_world(arm, "bip_pelvis", "bip_spine_0", meg_pos["Hips"], meg_pos["Spine"], thickness_scale=1.0, preserve_length=False)

# STEP B: POSE SPINE CHAIN (Spine0 -> Spine1 -> Neck -> Head)
pose_segment_world(arm, "bip_spine_0", "bip_spine_1", meg_pos["Spine"], meg_pos["Spine1"], thickness_scale=1.0, preserve_length=False)
pose_segment_world(arm, "bip_spine_1", "bip_neck", meg_pos["Spine1"], meg_pos["Neck"], thickness_scale=1.0, preserve_length=False)
pose_segment_world(arm, "bip_neck", "bip_head", meg_pos["Neck"], meg_pos["Head"], thickness_scale=1.0, preserve_length=False)

# STEP C: POSE LEGS (Children of Pelvis!)
for side, sgn in (("L", 1.0), ("R", -1.0)):
    meg_side = "Left" if side == "L" else "Right"
    hip_t = meg_pos[f"{meg_side}UpLeg"].copy()
    k_t = meg_pos[f"{meg_side}Leg"].copy()
    f_t = meg_pos[f"{meg_side}Foot"].copy()
    t_t = meg_pos[f"{meg_side}ToeBase"].copy()
    pose_segment_world(arm, f"bip_hip_{side}", f"bip_knee_{side}", hip_t, k_t, thickness_scale=0.96, preserve_length=False)
    pose_segment_world(arm, f"bip_knee_{side}", f"bip_foot_{side}", k_t, f_t, thickness_scale=0.96, preserve_length=False)
    pose_segment_world(arm, f"bip_foot_{side}", f"bip_toe_{side}", f_t, t_t, thickness_scale=0.96, preserve_length=True)

# STEP D: POSE ARMS, HANDS & 30 FINGERS
for side, sgn in (("L", 1.0), ("R", -1.0)):
    meg_side = "Left" if side == "L" else "Right"
    ua_name = f"bip_upperArm_{side}"
    la_name = f"bip_lowerArm_{side}"
    h_name = f"bip_hand_{side}"

    ua_h = pb_head_w(arm, ua_name)
    wri_t = meg_pos[f"{meg_side}Hand"].copy()
    elb_t = meg_pos[f"{meg_side}ForeArm"].copy()
    arm_t = meg_pos[f"{meg_side}Arm"].copy()

    pose_segment_world(arm, ua_name, la_name, Vector((arm_t.x, ua_h.y, arm_t.z)), elb_t, thickness_scale=0.96, preserve_length=False)
    pose_segment_world(arm, la_name, h_name, elb_t, wri_t, thickness_scale=0.96, preserve_length=False)

# Evaluate vertices bounding box!
bpy.ops.object.mode_set(mode="OBJECT")
deps = bpy.context.evaluated_depsgraph_get()
min_z, max_z = 999.0, -999.0
min_x, max_x = 999.0, -999.0
min_y, max_y = 999.0, -999.0
for obj in robot_objs:
    ev = obj.evaluated_get(deps)
    em = ev.to_mesh()
    for v in em.vertices:
        w = ev.matrix_world @ v.co
        min_x, max_x = min(min_x, w.x), max(max_x, w.x)
        min_y, max_y = min(min_y, w.y), max(max_y, w.y)
        min_z, max_z = min(min_z, w.z), max(max_z, w.z)
    ev.to_mesh_clear()

print(f"\nHierarchical Pose Evaluated Bounds:")
print(f"  World X: [{min_x:.3f}, {max_x:.3f}]")
print(f"  World Y: [{min_y:.3f}, {max_y:.3f}]")
print(f"  World Z: [{min_z:.3f}, {max_z:.3f}] (span={max_z - min_z:.3f})")
print(f"  Foot bottom min_z = {min_z:.3f}m")


# Check mesh objects and vertex groups
body_obj = bpy.data.objects.get("RB_Blastoff_CHARSKEL_Body.001.dmx")
if body_obj:
    print(f"Body vertex count: {len(body_obj.data.vertices)}")
    vg_names = [vg.name for vg in body_obj.vertex_groups]
    leg_vgs = [name for name in vg_names if any(k in name.lower() for k in ("foot", "toe", "knee", "hip", "leg"))]
    print(f"Body leg vertex groups: {leg_vgs}")
    # Check evaluated bounds of Body specifically
    deps = bpy.context.evaluated_depsgraph_get()
    ev = body_obj.evaluated_get(deps)
    em = ev.to_mesh()
    b_zs = [(ev.matrix_world @ v.co).z for v in em.vertices]
    print(f"Body evaluated Z range: [{min(b_zs):.3f}, {max(b_zs):.3f}]")
    ev.to_mesh_clear()
bpy.ops.object.mode_set(mode="OBJECT")
deps = bpy.context.evaluated_depsgraph_get()
min_z, max_z = 999.0, -999.0
min_x, max_x = 999.0, -999.0
min_y, max_y = 999.0, -999.0
for obj in robot_objs:
    ev = obj.evaluated_get(deps)
    em = ev.to_mesh()
    for v in em.vertices:
        w = ev.matrix_world @ v.co
        min_x, max_x = min(min_x, w.x), max(max_x, w.x)
        min_y, max_y = min(min_y, w.y), max(max_y, w.y)
        min_z, max_z = min(min_z, w.z), max(max_z, w.z)
    ev.to_mesh_clear()

# Check bone head positions
print("\n--- Bone Heads in World ---")
for bn in ["bip_pelvis", "bip_spine_0", "bip_spine_1", "bip_neck", "bip_head", "bip_hip_L", "bip_knee_L", "bip_foot_L", "bip_toe_L"]:
    if bn in arm.pose.bones:
        h = arm.matrix_world @ arm.pose.bones[bn].head
        print(f"  {bn:15s}: X={h.x:.3f}, Y={h.y:.3f}, Z={h.z:.3f}")

print(f"\nHierarchical Pose Evaluated Bounds:")
print(f"  World X: [{min_x:.3f}, {max_x:.3f}]")
print(f"  World Y: [{min_y:.3f}, {max_y:.3f}]")
print(f"  World Z: [{min_z:.3f}, {max_z:.3f}] (span={max_z - min_z:.3f})")
print(f"  Foot bottom min_z = {min_z:.3f}m")
