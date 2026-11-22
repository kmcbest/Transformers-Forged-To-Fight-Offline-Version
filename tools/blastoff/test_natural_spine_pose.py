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

# 0. Center
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

# Check natural bone positions:
print("--- Natural Unsquashed Bone Positions (scaled 2.2928x) ---")
MEG_MAP = {
    "bip_pelvis": "Hips",
    "bip_spine_0": "Spine",
    "bip_spine_1": "Spine1",
    "bip_neck": "Neck",
    "bip_head": "Head",
    "bip_hip_L": "LeftUpLeg",
    "bip_knee_L": "LeftLeg",
    "bip_foot_L": "LeftFoot",
    "bip_toe_L": "LeftToeBase",
}
for bn, mbn in MEG_MAP.items():
    p = arm.matrix_world @ arm.data.bones[bn].head_local
    mp = meg_pos[mbn]
    print(f"  {bn:15s}: Z={p.z:6.3f} | Megatronus {mbn:12s}: Z={mp.z:6.3f} | Diff={p.z - mp.z:+6.3f}")
