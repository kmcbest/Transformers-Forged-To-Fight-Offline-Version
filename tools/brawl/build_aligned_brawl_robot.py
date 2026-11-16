import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import bmesh
import json
import math
from collections import deque
from mathutils import Vector, Matrix, Quaternion
from pathlib import Path

print("=== [Brawl] Gate 1 & 2 Master Robot Pipeline (FOC -> 2048 Atlas -> 39-Bone + 15L Finger Retarget) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
DONOR_JSON = ROOT / "3rd-party-models" / "Brawl" / "00_donor_reference" / "donor_summary.json"
DONOR_OBJ = ROOT / "3rd-party-models" / "Brawl" / "00_donor_reference" / "cha_megatron_cin_rotf_00_robot.obj"
TEX_DIR = ROOT / "3rd-party-models" / "Brawl" / "02_textures"
ALIGNED_DIR = ROOT / "3rd-party-models" / "Brawl" / "01_aligned_mesh"
FBX_OUT_DIR = ROOT / "3rd-party-models" / "Brawl" / "03_fbx_exports"
UNITY_BRAWL_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Brawl"
RENDERS_DIR = ROOT / "renders" / "brawl"

for d in (ALIGNED_DIR, FBX_OUT_DIR, UNITY_BRAWL_DIR, RENDERS_DIR):
    d.mkdir(parents=True, exist_ok=True)

MEGATRON_39_BONES = [
    "Spine", "Spine1", "Hips", "Neck", "Head", "Jaw",
    "RightUpLeg", "RightLeg", "LeftForeArm", "RightToeBase", "RightFoot",
    "RightShoulder", "RightArm", "LeftShoulder", "LeftArm", "LeftHand",
    "LeftHandMiddle1", "LeftHandMiddle2", "LeftHandMiddle3",
    "LeftHandThumb1", "LeftHandThumb2", "LeftHandThumb3",
    "LeftHandIndex1", "LeftHandIndex2", "LeftHandIndex3",
    "LeftHandRing1", "LeftHandRing2", "LeftHandRing3",
    "LeftHandPinky1", "LeftHandPinky2", "LeftHandPinky3",
    "LeftLeg", "LeftFoot", "LeftToeBase", "LeftUpLeg",
    "RightForeArm", "LeftToe", "LeftArmRoll", "RightArmRoll",
]

MEGATRON_PARENT_MAP = {
    "Hips": None,
    "Spine": "Hips",
    "Spine1": "Spine",
    "Neck": "Spine1",
    "Head": "Neck",
    "Jaw": "Head",
    "LeftShoulder": "Spine1",
    "LeftArm": "LeftShoulder",
    "LeftArmRoll": "LeftArm",
    "LeftForeArm": "LeftArmRoll",
    "LeftHand": "LeftForeArm",
    "LeftHandThumb1": "LeftHand",
    "LeftHandThumb2": "LeftHandThumb1",
    "LeftHandThumb3": "LeftHandThumb2",
    "LeftHandIndex1": "LeftHand",
    "LeftHandIndex2": "LeftHandIndex1",
    "LeftHandIndex3": "LeftHandIndex2",
    "LeftHandMiddle1": "LeftHand",
    "LeftHandMiddle2": "LeftHandMiddle1",
    "LeftHandMiddle3": "LeftHandMiddle2",
    "LeftHandRing1": "LeftHand",
    "LeftHandRing2": "LeftHandRing1",
    "LeftHandRing3": "LeftHandRing2",
    "LeftHandPinky1": "LeftHand",
    "LeftHandPinky2": "LeftHandPinky1",
    "LeftHandPinky3": "LeftHandPinky2",
    "RightShoulder": "Spine1",
    "RightArm": "RightShoulder",
    "RightArmRoll": "RightArm",
    "RightForeArm": "RightArmRoll",
    "LeftUpLeg": "Hips",
    "LeftLeg": "LeftUpLeg",
    "LeftFoot": "LeftLeg",
    "LeftToeBase": "LeftFoot",
    "LeftToe": "LeftToeBase",
    "RightUpLeg": "Hips",
    "RightLeg": "RightUpLeg",
    "RightFoot": "RightLeg",
    "RightToeBase": "RightFoot",
}

BRAWL_MESH_NAMES = [
    "RB_Brawl_CHARSKEL_Head.mo.dmx",
    "RB_Brawl_CHARSKEL_Chest.mo.dmx",
    "RB_Brawl_CHARSKEL_CapL.mo.dmx",
    "RB_Brawl_CHARSKEL_CapR.mo.dmx",
    "RB_Brawl_CHARSKEL_ArmLoL.mo.dmx",
    "RB_Brawl_CHARSKEL_ArmLoR.mo.dmx",
    "RB_Brawl_CHARSKEL_Legs.mo.dmx",
    "BrawlCannon_STAT.mo.dmx",
    "BrawlCannon_STAT.mo.001.dmx",
    "WEP_Hammer_SKEL.mo.dmx",
]

# OpenGL UV Atlas boxes: (u_scale, u_off, v_scale, v_off)
ROBOT_UV_MAP = {
    "RB_Brawl_Chest_Mat_INST_B":    (0.5,   0.0,   0.5,  0.5),
    "VH_Brawl_Cust_MatINST":        (0.25,  0.5,   0.25, 0.75),
    "WEP_Hammer_D_MATINST":         (0.25,  0.75,  0.25, 0.75),
    "WEP_Hammer_Spikes_MATINST":    (0.25,  0.5,   0.25, 0.5),
    "RB_Brawl_Legs_Mat_INST_B":     (0.5,   0.0,   0.5,  0.0),
    "RB_Brawl_Head_Mat_INST_B":     (0.25,  0.5,   0.25, 0.25),
    "RB_Brawl_ArmLo_Mat_INST_B":    (0.25,  0.75,  0.25, 0.25),
    "RB_Brawl_ArmUp_Mat_INST_B":    (0.25,  0.5,   0.25, 0.0),
    "VH_BrawInterior_Cust_MatINST": (0.125, 0.75,  0.25, 0.0),
    "TR_FactionLogo_Mat_INST":      (0.125, 0.875, 0.25, 0.0),
}


def unity_to_blender(upos):
    """Standard right-handed Blender coordinates (det=+1):
    Unity (ux, uy, uz) -> Blender (-ux, -uz, uy): Left=+X, Forward=-Y, Up=+Z.
    """
    return Vector((-float(upos[0]), -float(upos[2]), float(upos[1])))


def load_megatron_bones():
    import numpy as np
    donor = json.loads(DONOR_JSON.read_text(encoding="utf-8"))
    mesh_00 = donor["meshes"]["cha_megatron_cin_rotf_00"]
    avatar_tos = donor["avatars"]["cha_megatron_cin_rotf_00Avatar"]["tos"]
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


def remap_uvs_clean(obj, uv_map, default_box=(0.5, 0.0, 0.5, 0.5)):
    """Remap per-polygon UVs cleanly into atlas quadrants without seam-wrapping artifacts."""
    uv_layer = obj.data.uv_layers.active
    if not uv_layer:
        return
    mat_slots = [slot.material.name if slot.material else "" for slot in obj.material_slots]
    for poly in obj.data.polygons:
        mname = mat_slots[poly.material_index] if poly.material_index < len(mat_slots) else ""
        u_sc, u_off, v_sc, v_off = uv_map.get(mname, default_box)

        # Collect polygon loop UVs and repair half-float overflow junk if any
        pts = []
        for li in poly.loop_indices:
            uv = uv_layer.data[li].uv
            ux = 0.5 if (not math.isfinite(uv.x) or abs(uv.x) > 10.0) else uv.x
            vy = 0.5 if (not math.isfinite(uv.y) or abs(uv.y) > 10.0) else uv.y
            pts.append((li, ux, vy))

        mu = sum(p[1] for p in pts) / len(pts)
        mv = sum(p[2] for p in pts) / len(pts)
        du = math.floor(mu)
        dv = math.floor(mv)

        for li, ux, vy in pts:
            u_loc = min(0.994, max(0.006, ux - du))
            v_loc = min(0.994, max(0.006, vy - dv))
            uv_layer.data[li].uv = (u_loc * u_sc + u_off, v_loc * v_sc + v_off)
    obj.data.update()


def make_brawl_preview_material(name, prefix):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    ta = nt.nodes.new("ShaderNodeTexImage")
    ta.image = bpy.data.images.load(str(TEX_DIR / f"{prefix}_Diffuse.png"))
    nt.links.new(ta.outputs["Color"], bsdf.inputs["Base Color"])

    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = bpy.data.images.load(str(TEX_DIR / f"{prefix}_Normal_unity.png"))
    tn.image.colorspace_settings.name = "Non-Color"
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])

    te = nt.nodes.new("ShaderNodeTexImage")
    te.image = bpy.data.images.load(str(TEX_DIR / f"{prefix}_Emission.png"))
    nt.links.new(te.outputs["Color"], bsdf.inputs["Emission"])
    bsdf.inputs["Emission Strength"].default_value = 2.5
    bsdf.inputs["Roughness"].default_value = 0.65
    bsdf.inputs["Metallic"].default_value = 0.25
    return mat


def split_ue3_2shell_fingers(arm, arml_obj, side="L"):
    """Per Pipeline Section 9.4: Split bip_{fn}_1_{side} into proximal/middle & distal tip,
    and split bip_thumb_1_{side} into mid/tip so all 15 finger phalanges articulate cleanly.
    """
    adj = [set() for _ in range(len(arml_obj.data.vertices))]
    for e in arml_obj.data.edges:
        a, b = e.vertices[0], e.vertices[1]
        adj[a].add(b)
        adj[b].add(a)

    def find_shells(vset):
        seen = set()
        shells = []
        for start in sorted(vset):
            if start in seen:
                continue
            comp = []
            q = deque([start])
            seen.add(start)
            while q:
                u = q.popleft()
                comp.append(u)
                for nb in adj[u]:
                    if nb in vset and nb not in seen:
                        seen.add(nb)
                        q.append(nb)
            shells.append(comp)
        return shells

    # Get armature-space finger bone positions BEFORE parenting/mode switching
    bone_heads = {b.name: (arm.matrix_world @ b.head_local).copy() for b in arm.data.bones}
    vg_map = {vg.name: vg.index for vg in arml_obj.vertex_groups}

    splits_info = []
    for fn in ("index", "middle", "ring", "pinky"):
        vg0_name = f"bip_{fn}_0_{side}"
        vg1_name = f"bip_{fn}_1_{side}"
        vg2_name = f"bip_{fn}_2_{side}"
        vg2 = arml_obj.vertex_groups.new(name=vg2_name)
        idx0 = vg_map[vg0_name]
        idx1 = vg_map[vg1_name]

        p0 = bone_heads[vg0_name]
        p1 = bone_heads[vg1_name]
        axis_dir = (p1 - p0).normalized()

        vset = {v.index for v in arml_obj.data.vertices if any(g.group == idx1 and g.weight > 0.25 for g in v.groups)}
        shells = find_shells(vset)
        # Rank shells by projection along finger direction; major distal shell goes to vg2
        major_shells = [s for s in shells if len(s) >= 10]
        major_shells.sort(key=lambda s: sum(((arml_obj.matrix_world @ arml_obj.data.vertices[vi].co) - p1).dot(axis_dir) for vi in s) / len(s))
        assert len(major_shells) >= 2, f"Expected 2 major shells on {vg1_name}, got {[len(s) for s in shells]}"
        mid_shell = major_shells[0]
        tip_shell = major_shells[-1]
        mid_max = max(((arml_obj.matrix_world @ arml_obj.data.vertices[vi].co) - p1).dot(axis_dir) for vi in mid_shell)
        tip_min = min(((arml_obj.matrix_world @ arml_obj.data.vertices[vi].co) - p1).dot(axis_dir) for vi in tip_shell)
        tip_max = max(((arml_obj.matrix_world @ arml_obj.data.vertices[vi].co) - p1).dot(axis_dir) for vi in tip_shell)
        hinge_proj = 0.5 * (mid_max + tip_min)

        hinge_w = p1 + axis_dir * hinge_proj
        tip_w = p1 + axis_dir * max(tip_max, hinge_proj + 0.08)
        splits_info.append((vg1_name, vg2_name, f"bip_{fn}_tip_{side}", hinge_w, tip_w))

        # Reassign tip_shell vertices strictly to vg2_name
        for vi in tip_shell:
            w1 = 0.0
            for g in arml_obj.data.vertices[vi].groups:
                if g.group == idx1:
                    w1 = g.weight
            if w1 > 0.0:
                arml_obj.vertex_groups[idx1].remove([vi])
                vg2.add([vi], w1, "REPLACE")
        print(f"  [Split {fn:6s} {side}] mid={len(mid_shell)} verts -> {vg1_name}, tip={len(tip_shell)} verts -> {vg2_name}")

    # Split Thumb_1 (single 30-vert shell) cleanly by projection midpoint along thumb vector
    t1_name = f"bip_thumb_1_{side}"
    t2_name = f"bip_thumb_2_{side}"
    vg_t2 = arml_obj.vertex_groups.new(name=t2_name)
    idx_t1 = vg_map[t1_name]
    pt0 = bone_heads[f"bip_thumb_0_{side}"]
    pt1 = bone_heads[t1_name]
    t_dir = (pt1 - pt0).normalized()
    t1_verts = [v.index for v in arml_obj.data.vertices if any(g.group == idx_t1 and g.weight > 0.25 for g in v.groups)]
    projs = [((arml_obj.matrix_world @ arml_obj.data.vertices[vi].co) - pt1).dot(t_dir) for vi in t1_verts]
    p_mid = 0.5 * (min(projs) + max(projs))
    t_hinge_w = pt1 + t_dir * p_mid
    t_tip_w = pt1 + t_dir * max(max(projs), p_mid + 0.06)
    splits_info.append((t1_name, t2_name, f"bip_thumb_tip_{side}", t_hinge_w, t_tip_w))
    moved_t = 0
    for vi, pr in zip(t1_verts, projs):
        if pr >= p_mid:
            w1 = next((g.weight for g in arml_obj.data.vertices[vi].groups if g.group == idx_t1), 0.0)
            if w1 > 0.0:
                arml_obj.vertex_groups[idx_t1].remove([vi])
                vg_t2.add([vi], w1, "REPLACE")
                moved_t += 1
    print(f"  [Split thumb  {side}] mid={len(t1_verts)-moved_t} verts -> {t1_name}, tip={moved_t} verts -> {t2_name}")

    # Create new EditBones in brawl_ARM matching those exact world positions
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    ebs = arm.data.edit_bones
    inv_aw = arm.matrix_world.inverted()
    for p1_name, p2_name, tip_name, hinge_w, tip_w in splits_info:
        eb1 = ebs[p1_name]
        eb1.tail = inv_aw @ hinge_w
        eb2 = ebs.new(p2_name)
        eb2.head = inv_aw @ hinge_w
        eb2.tail = inv_aw @ tip_w
        eb2.parent = eb1
        eb2.use_connect = True

        eb_tip = ebs.new(tip_name)
        eb_tip.head = inv_aw @ tip_w
        eb_tip.tail = inv_aw @ (tip_w + (tip_w - hinge_w).normalized() * 0.15)
        eb_tip.parent = eb2
        eb_tip.use_connect = True
    bpy.ops.object.mode_set(mode="OBJECT")


def pose_segment_world(arm_obj, bname, child_bname, target_head_w, target_end_w, thickness_scale=1.0, preserve_length=False):
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


def pb_head_w(arm_obj, bname):
    return (arm_obj.matrix_world @ arm_obj.pose.bones[bname].matrix).translation.copy()


def rotate_pose_bone_world(arm_obj, bname, axis_w, angle_deg):
    bpy.context.view_layer.update()
    pb = arm_obj.pose.bones[bname]
    w_old = arm_obj.matrix_world @ pb.matrix
    q = Quaternion(axis_w.normalized(), math.radians(angle_deg))
    R_new = q.to_matrix() @ w_old.to_3x3()
    M_new_w = R_new.to_4x4()
    M_new_w.translation = w_old.translation.copy()
    pb.matrix = arm_obj.matrix_world.inverted() @ M_new_w
    bpy.context.view_layer.update()


def curl_right_fingers_around_hammer(arm_obj):
    """Curl all 5 articulated right fingers cleanly around the WEP_Body_XB_R hammer shaft."""
    bpy.context.view_layer.update()
    p_pommel = pb_head_w(arm_obj, "C_Robo08_XT_R")
    p_head = pb_head_w(arm_obj, "C_Robo03_XT_R")
    p_grip = pb_head_w(arm_obj, "WEP_Body_XB_R")
    shaft_axis = (p_head - p_pommel).normalized()

    # Determine palm inward curl axis using middle finger -> shaft center
    p_mid0 = pb_head_w(arm_obj, "bip_middle_0_R")
    p_mid1 = pb_head_w(arm_obj, "bip_middle_1_R")
    v_finger = (p_mid1 - p_mid0).normalized()
    c_mid = p_grip + shaft_axis * (p_mid0 - p_grip).dot(shaft_axis)
    v_to_shaft = (c_mid - p_mid0).normalized()
    curl_axis = v_finger.cross(v_to_shaft).normalized()
    # Project strictly onto shaft_axis polarity so all 4 fingers curl parallel around cylinder
    if curl_axis.dot(shaft_axis) >= 0.0:
        curl_axis = shaft_axis
    else:
        curl_axis = -shaft_axis

    # Curl 4 main fingers tightly around shaft handle (joint 0 -> 1 -> 2)
    for fn, a0, a1, a2 in (
        ("index",  42.0, 72.0, 58.0),
        ("middle", 45.0, 75.0, 62.0),
        ("ring",   45.0, 75.0, 62.0),
        ("pinky",  48.0, 78.0, 65.0),
    ):
        rotate_pose_bone_world(arm_obj, f"bip_{fn}_0_R", curl_axis, a0)
        rotate_pose_bone_world(arm_obj, f"bip_{fn}_1_R", curl_axis, a1)
        rotate_pose_bone_world(arm_obj, f"bip_{fn}_2_R", curl_axis, a2)

    # Curl thumb downward/outward across top-front of hammer shaft toward curled index finger
    pt0 = pb_head_w(arm_obj, "bip_thumb_0_R")
    pt1 = pb_head_w(arm_obj, "bip_thumb_1_R")
    p_idx1 = pb_head_w(arm_obj, "bip_index_1_R")
    v_th = (pt1 - pt0).normalized()
    c_th = p_grip + shaft_axis * (pt0 - p_grip).dot(shaft_axis)
    v_th_targ = (0.5 * (c_th + p_idx1) - pt0).normalized()
    th_axis = v_th.cross(v_th_targ)
    if th_axis.length > 1e-4:
        th_axis.normalize()
        rotate_pose_bone_world(arm_obj, "bip_thumb_0_R", th_axis, 32.0)
        rotate_pose_bone_world(arm_obj, "bip_thumb_1_R", th_axis, 38.0)
        rotate_pose_bone_world(arm_obj, "bip_thumb_2_R", th_axis, 28.0)
    print("[✓] Curled 15 right-hand finger phalanges cleanly around hammer handle!")


def main():
    meg_pos = load_megatron_bones()

    # 1. Import FOC Combaticons FBX & isolate strictly Brawl + brawl_ARM
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=FBX_PATH)

    keep_names = set(BRAWL_MESH_NAMES) | {"brawl_ARM"}
    for o in list(bpy.data.objects):
        if o.name not in keep_names:
            bpy.data.objects.remove(o, do_unlink=True)

    arm = bpy.data.objects.get("brawl_ARM")
    assert arm is not None, "Missing brawl_ARM!"
    robot_objs = [bpy.data.objects[n] for n in BRAWL_MESH_NAMES if n in bpy.data.objects]
    assert len(robot_objs) == 10, f"Expected 10 Brawl robot parts (incl. WEP_Hammer), found {len(robot_objs)}"

    # 2. Remap UVs BEFORE joining & material consolidation (zero-bleed 2048 Atlas!)
    for obj in robot_objs:
        remap_uvs_clean(obj, ROBOT_UV_MAP)
    print("[✓] Remapped UVs cleanly for all 10 Brawl robot parts (incl. Right Hammer) into 2048 Atlas.")

    # 3. Split Left & Right Hand 2-shell fingers -> 3 articulated phalanges BEFORE transforming armature
    arml_obj = bpy.data.objects["RB_Brawl_CHARSKEL_ArmLoL.mo.dmx"]
    armr_obj = bpy.data.objects["RB_Brawl_CHARSKEL_ArmLoR.mo.dmx"]
    split_ue3_2shell_fingers(arm, arml_obj, side="L")
    split_ue3_2shell_fingers(arm, armr_obj, side="R")

    # 4. Place Brawl at (0,0,0), rotate +90deg around Z so (+X=Left, -Y=Forward, +Z=Up, det=+1),
    # and scale cleanly (~1.96x so shoulder height matches Megatron's 9.48m!).
    # Verify scale: bip_upperArm_L raw z = 4.8762 -> 9.4803 / 4.8762 = 1.9442
    # Verify foot-to-head: 5.323 * 1.96 = 10.43m (Megatron Head = 10.10m, crown = 11.14m).
    SCALE_BRAWL = 1.96
    arm.location = (0.0, 0.0, 0.0)
    arm.rotation_euler = (0.0, 0.0, math.radians(-90.0))
    arm.scale = (SCALE_BRAWL, SCALE_BRAWL, SCALE_BRAWL)
    bpy.context.view_layer.update()

    # Check direction after transform!
    test_lh = (arm.matrix_world @ arm.data.bones["bip_hand_L"].head_local)
    test_toe = (arm.matrix_world @ arm.data.bones["bip_toe_L"].head_local)
    print(f"[AxisVerify] Blender space: LeftHand={tuple(round(c,3) for c in test_lh)} (+X expected), LeftToe={tuple(round(c,3) for c in test_toe)} (-Y expected)")
    assert test_lh.x > 1.0 and test_toe.y < -0.1, f"Axis mismatch! LH={test_lh}, Toe={test_toe}"

    # 5. GATE 2 IRON LAW: Pose Legs FIRST -> Ground via min_z -> Align Torso/Arms/Wrists/15 Fingers!
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")

    # 5a. Align Legs straight into Megatron's vertical stance (|X|=0.84) with chunky volume preserved
    for side, sgn in (("L", 1.0), ("R", -1.0)):
        meg_side = "Left" if side == "L" else "Right"
        h_p = pb_head_w(arm, f"bip_hip_{side}")
        k_t = Vector((0.88 * sgn, meg_pos[f"{meg_side}Leg"].y, meg_pos[f"{meg_side}Leg"].z))
        f_t = Vector((0.88 * sgn, meg_pos[f"{meg_side}Foot"].y, meg_pos[f"{meg_side}Foot"].z))
        t_t = Vector((0.88 * sgn, meg_pos[f"{meg_side}ToeBase"].y, meg_pos[f"{meg_side}ToeBase"].z))
        pose_segment_world(arm, f"bip_hip_{side}", f"bip_knee_{side}", Vector((0.88 * sgn, h_p.y, h_p.z)), k_t, thickness_scale=0.96, preserve_length=False)
        pose_segment_world(arm, f"bip_knee_{side}", f"bip_foot_{side}", k_t, f_t, thickness_scale=0.96, preserve_length=False)
        pose_segment_world(arm, f"bip_foot_{side}", f"bip_toe_{side}", f_t, t_t, thickness_scale=0.96, preserve_length=True)

    # 5b. Measure true evaluated foot bottom min_z across all meshes and ground the armature!
    bpy.ops.object.mode_set(mode="OBJECT")
    deps = bpy.context.evaluated_depsgraph_get()
    min_z = 999.0
    for obj in robot_objs:
        ev = obj.evaluated_get(deps)
        em = ev.to_mesh()
        for v in em.vertices:
            wz = (ev.matrix_world @ v.co).z
            if wz < min_z:
                min_z = wz
        ev.to_mesh_clear()
    arm.location.z -= min_z
    bpy.context.view_layer.update()
    print(f"[✓] Grounded brawl_ARM (shifted Z by {-min_z:.4f}m BEFORE aligning arms & fingers)")

    # 5c. Pose Left & Right Arms + Wrists + All 15 Left Fingers 1:1 to Megatron's BindPose!
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")

    for side, sgn in (("L", 1.0), ("R", -1.0)):
        meg_side = "Left" if side == "L" else "Right"
        ua_name = f"bip_upperArm_{side}"
        la_name = f"bip_lowerArm_{side}"
        h_name = f"bip_hand_{side}"

        # Pull clavicle slightly if needed? Keep shoulder anchored naturally, align UpperArm -> ForeArm -> Hand!
        ua_h = pb_head_w(arm, ua_name)
        la_len = (pb_head_w(arm, h_name) - pb_head_w(arm, la_name)).length

        wri_t = meg_pos["LeftHand"].copy() if side == "L" else Vector((-meg_pos["LeftHand"].x, meg_pos["LeftHand"].y, meg_pos["LeftHand"].z))
        elb_t = meg_pos[f"{meg_side}ForeArm"].copy()
        arm_t = meg_pos[f"{meg_side}Arm"].copy()

        # Keep natural shoulder X but align elbow/wrist directly on Megatron's X = +/- 2.473, Z = 7.625 -> 5.527
        pose_segment_world(arm, ua_name, la_name, Vector((arm_t.x, ua_h.y, arm_t.z)), elb_t, thickness_scale=0.96, preserve_length=False)
        pose_segment_world(arm, la_name, h_name, elb_t, wri_t, thickness_scale=0.96, preserve_length=False)

        if side == "L":
            # Dual-axis orient Left Hand palm so fingers point down & Index(-Y) -> Pinky(+Y)
            pb_h = arm.pose.bones[h_name]
            w_h = arm.matrix_world @ pb_h.matrix
            kn_i = pb_head_w(arm, "bip_index_0_L")
            kn_p = pb_head_w(arm, "bip_pinky_0_L")
            curr_kn = 0.5 * (kn_i + kn_p)
            targ_kn = 0.5 * (meg_pos["LeftHandIndex1"] + meg_pos["LeftHandPinky1"])

            v_ch = curr_kn - w_h.translation
            v_th = targ_kn - wri_t
            q_h = v_ch.rotation_difference(v_th)
            s_h = min(1.15, max(0.85, v_th.length / max(v_ch.length, 1e-5)))
            d_h = v_ch.normalized()
            S_h = Matrix.Identity(3)
            for r in range(3):
                for c in range(3):
                    S_h[r][c] += (s_h - 1.0) * d_h[r] * d_h[c]
            M_h = (q_h.to_matrix() @ S_h @ w_h.to_3x3()).to_4x4()
            M_h.translation = wri_t
            pb_h.matrix = arm.matrix_world.inverted() @ M_h
            bpy.context.view_layer.update()

            # Yaw twist alignment: Index -> Pinky
            curr_span = pb_head_w(arm, "bip_index_0_L") - pb_head_w(arm, "bip_pinky_0_L")
            targ_span = meg_pos["LeftHandIndex1"] - meg_pos["LeftHandPinky1"]
            ah = v_th.normalized()
            c_perp = (curr_span - ah * curr_span.dot(ah)).normalized()
            t_perp = (targ_span - ah * targ_span.dot(ah)).normalized()
            q_y = c_perp.rotation_difference(t_perp)
            w_h_now = arm.matrix_world @ pb_h.matrix
            pb_h.matrix = arm.matrix_world.inverted() @ (
                Matrix.Translation(wri_t) @ q_y.to_matrix().to_4x4() @ Matrix.Translation(-wri_t) @ w_h_now
            )
            bpy.context.view_layer.update()

            # Align ALL 15 Left Finger bones 1:1 onto Megatron BindPose coordinates!
            # Keep Thumb preserve_length=True so Brawl's chunky thumb preserves natural blocky length in open hand
            for fn_low, fn_cap in (("thumb", "Thumb"), ("index", "Index"), ("middle", "Middle"), ("ring", "Ring"), ("pinky", "Pinky")):
                p1 = meg_pos[f"LeftHand{fn_cap}1"]
                p2 = meg_pos[f"LeftHand{fn_cap}2"]
                p3 = meg_pos[f"LeftHand{fn_cap}3"]
                pt = p3 + (p3 - p2) * 0.90
                is_thumb = (fn_low == "thumb")
                pose_segment_world(arm, f"bip_{fn_low}_0_L", f"bip_{fn_low}_1_L", p1, p2, thickness_scale=0.95, preserve_length=is_thumb)
                h2 = pb_head_w(arm, f"bip_{fn_low}_1_L") if is_thumb else p2
                pose_segment_world(arm, f"bip_{fn_low}_1_L", f"bip_{fn_low}_2_L", h2, p3, thickness_scale=0.95, preserve_length=is_thumb)
                h3 = pb_head_w(arm, f"bip_{fn_low}_2_L") if is_thumb else p3
                pose_segment_world(arm, f"bip_{fn_low}_2_L", f"bip_{fn_low}_tip_L", h3, pt, thickness_scale=0.95, preserve_length=True)
        else:
            # Right Hand points vertically down (-Z) with hammer shaft pointing dead forward (-Y)
            pb_h = arm.pose.bones[h_name]
            w_h = arm.matrix_world @ pb_h.matrix
            kn_m = pb_head_w(arm, "bip_middle_0_R")
            v_ch = kn_m - w_h.translation
            v_th = Vector((0.0, 0.0, -v_ch.length))
            q_h = v_ch.rotation_difference(v_th)
            M_h = (q_h.to_matrix() @ w_h.to_3x3()).to_4x4()
            M_h.translation = wri_t
            pb_h.matrix = arm.matrix_world.inverted() @ M_h
            bpy.context.view_layer.update()

            # Yaw twist alignment around Z: aim hammer shaft forward (-Y) & ~18deg outward (-X) so it clears thigh & face
            s_vec = pb_head_w(arm, "C_Robo03_XT_R") - pb_head_w(arm, "C_Robo08_XT_R")
            s_xy = Vector((s_vec.x, s_vec.y, 0.0)).normalized()
            targ_fwd = Vector((-0.32, -0.95, 0.0)).normalized()
            if s_xy.length > 1e-4:
                q_y = s_xy.rotation_difference(targ_fwd)
                w_h_now = arm.matrix_world @ pb_h.matrix
                pb_h.matrix = arm.matrix_world.inverted() @ (
                    Matrix.Translation(wri_t) @ q_y.to_matrix().to_4x4() @ Matrix.Translation(-wri_t) @ w_h_now
                )
                bpy.context.view_layer.update()

            # Curl articulated Right fingers tightly around the hammer handle
            curl_right_fingers_around_hammer(arm)

    bpy.ops.object.mode_set(mode="OBJECT")

    # 6. Apply Armature modifiers cleanly on all 9 posed meshes, then join
    for obj in robot_objs:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        for mod in list(obj.modifiers):
            if mod.type == "ARMATURE":
                bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
        obj.modifiers.clear()

    bpy.ops.object.select_all(action="DESELECT")
    for obj in robot_objs:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = robot_objs[0]
    bpy.ops.object.join()
    robot = bpy.context.active_object
    robot.name = "cha_brawl_gs_00"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # 7. Exact Bone Weight Remapping + Same-Shell-Same-Bone + Hard-Surface Truncation (>= 0.65 -> 1.0)
    bone_map = {
        "bip_pelvis": "Hips",
        "bip_spine_0": "Spine",
        "bip_spine_1": "Spine1",
        "bip_neck": "Neck",
        "bip_head": "Head",
        "bip_Jaw": "Jaw",
        "C_Head01_Face_XF2": "Head",
        "BrawlCannon_STAT.mo": "Spine1",
        "BrawlCannon_STAT.mo.001": "Spine1",
        # Left Arm & Shoulder Pad
        "bip_collar_L": "LeftShoulder",
        "bip_upperArm_L": "LeftArm",
        "L_ClavRobo01_XT": "LeftArm",
        "L_CloudA_PadRobo01_XT": "LeftArm",
        "L_CloudA_PadRobo02_XT": "LeftArm",
        "L_CloudA_PadRobo03_XT": "LeftArm",
        "L_CloudA_PadRobo04_XT": "LeftArm",
        "L_CloudA_PadRobo05_XT": "LeftArm",
        "bip_lowerArm_L": "LeftForeArm",
        "bip_hand_L": "LeftHand",
        "bip_thumb_0_L": "LeftHandThumb1",
        "bip_thumb_1_L": "LeftHandThumb2",
        "bip_thumb_2_L": "LeftHandThumb3",
        "bip_index_0_L": "LeftHandIndex1",
        "bip_index_1_L": "LeftHandIndex2",
        "bip_index_2_L": "LeftHandIndex3",
        "bip_middle_0_L": "LeftHandMiddle1",
        "bip_middle_1_L": "LeftHandMiddle2",
        "bip_middle_2_L": "LeftHandMiddle3",
        "bip_ring_0_L": "LeftHandRing1",
        "bip_ring_1_L": "LeftHandRing2",
        "bip_ring_2_L": "LeftHandRing3",
        "bip_pinky_0_L": "LeftHandPinky1",
        "bip_pinky_1_L": "LeftHandPinky2",
        "bip_pinky_2_L": "LeftHandPinky3",
        # Right Arm & Shoulder Pad (Megatron right arm ends at RightForeArm)
        "bip_collar_R": "RightShoulder",
        "bip_upperArm_R": "RightArm",
        "R_ClavRobo01_XT": "RightArm",
        "R_CloudA_PadRobo01_XT": "RightArm",
        "R_CloudA_PadRobo02_XT": "RightArm",
        "R_CloudA_PadRobo03_XT": "RightArm",
        "R_CloudA_PadRobo04_XT": "RightArm",
        "R_CloudA_PadRobo05_XT": "RightArm",
        "bip_lowerArm_R": "RightForeArm",
        "bip_hand_R": "RightForeArm",
        "bip_thumb_0_R": "RightForeArm",
        "bip_thumb_1_R": "RightForeArm",
        "bip_thumb_2_R": "RightForeArm",
        "bip_index_0_R": "RightForeArm",
        "bip_index_1_R": "RightForeArm",
        "bip_index_2_R": "RightForeArm",
        "bip_middle_0_R": "RightForeArm",
        "bip_middle_1_R": "RightForeArm",
        "bip_middle_2_R": "RightForeArm",
        "bip_ring_0_R": "RightForeArm",
        "bip_ring_1_R": "RightForeArm",
        "bip_ring_2_R": "RightForeArm",
        "bip_pinky_0_R": "RightForeArm",
        "bip_pinky_1_R": "RightForeArm",
        "bip_pinky_2_R": "RightForeArm",
        "WEP_Reference_XR_R": "RightForeArm",
        "WEP_Body_XB_R": "RightForeArm",
        "C_Robo01_XT_R": "RightForeArm",
        "C_Robo02_XT_R": "RightForeArm",
        "C_Robo03_XT_R": "RightForeArm",
        "C_Robo04_XT_R": "RightForeArm",
        "C_Robo05_XT_R": "RightForeArm",
        "C_Robo06_XT_R": "RightForeArm",
        "C_Robo07_XT_R": "RightForeArm",
        "C_Robo08_XT_R": "RightForeArm",
        "C_Robo09_XT_R": "RightForeArm",
        "C_Robo10_XT_R": "RightForeArm",
        "C_Robo11_XT_R": "RightForeArm",
        "C_Robo12_XT_R": "RightForeArm",
        "C_Robo13_XT_R": "RightForeArm",
        # Legs
        "bip_hip_L": "LeftUpLeg",
        "bip_knee_L": "LeftLeg",
        "bip_foot_L": "LeftFoot",
        "bip_toe_L": "LeftToeBase",
        "bip_toe_L_end": "LeftToe",
        "bip_hip_R": "RightUpLeg",
        "bip_knee_R": "RightLeg",
        "bip_foot_R": "RightFoot",
        "bip_toe_R": "RightToeBase",
        "bip_toe_R_end": "RightToeBase",
    }

    def resolve_target_bone(bname):
        if bname in bone_map:
            return bone_map[bname]
        b = arm.data.bones.get(bname)
        curr = b
        while curr:
            if curr.name in bone_map:
                return bone_map[curr.name]
            curr = curr.parent
        return "Spine1"

    vg_idx_to_name = {vg.index: vg.name for vg in robot.vertex_groups}
    v_weights = []
    zero_w_fixed = 0
    rigid_snapped = 0
    for v in robot.data.vertices:
        wdict = {}
        for g in v.groups:
            orig_n = vg_idx_to_name.get(g.group, "")
            tgt_n = resolve_target_bone(orig_n)
            wdict[tgt_n] = wdict.get(tgt_n, 0.0) + g.weight
        tot = sum(wdict.values())
        if tot <= 1e-6:
            wdict = {"Spine1": 1.0}
            zero_w_fixed += 1
        else:
            for k in wdict:
                wdict[k] /= tot
            top_b, top_w = max(wdict.items(), key=lambda kv: kv[1])
            if top_w >= 0.65:
                wdict = {top_b: 1.0}
                rigid_snapped += 1
        v_weights.append(wdict)

    print(f"[✓] Audited weights: verts={len(v_weights)}, zero_w_fixed={zero_w_fixed}, hard_surface_rigid={rigid_snapped}")

    # Remove old brawl_ARM, build clean exact 39-bone Megatron Armature in Blender space
    bpy.data.objects.remove(arm, do_unlink=True)
    arm_data = bpy.data.armatures.new("ARM_Brawl_Robot_Data")
    new_arm = bpy.data.objects.new("ARM_Brawl_Robot", arm_data)
    bpy.context.scene.collection.objects.link(new_arm)
    bpy.context.view_layer.objects.active = new_arm
    bpy.ops.object.mode_set(mode="EDIT")
    ebs = arm_data.edit_bones
    for bname in MEGATRON_39_BONES:
        p = meg_pos[bname]
        eb = ebs.new(bname)
        eb.head = p
        if "Thumb" in bname:
            eb.tail = p + Vector((0, -0.15, 0))
        elif any(f in bname for f in ("Index", "Middle", "Ring", "Pinky")):
            eb.tail = p + Vector((0, 0, -0.15))
        elif "Leg" in bname or "Foot" in bname or "Arm" in bname or "Hand" in bname:
            eb.tail = p + Vector((0, 0, -0.30))
        else:
            eb.tail = p + Vector((0, 0, 0.30))
    for bname in MEGATRON_39_BONES:
        pn = MEGATRON_PARENT_MAP.get(bname)
        if pn and pn in ebs:
            ebs[bname].parent = ebs[pn]
            ebs[bname].use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")

    robot.vertex_groups.clear()
    new_vgs = {bname: robot.vertex_groups.new(name=bname) for bname in MEGATRON_39_BONES}
    for vi, wd in enumerate(v_weights):
        for bn, w in wd.items():
            if bn in new_vgs and w > 0.001:
                new_vgs[bn].add([vi], w, "REPLACE")

    robot.parent = new_arm
    mod = robot.modifiers.new("Armature", "ARMATURE")
    mod.object = new_arm

    # Consolidate to single unified PBR Preview Material
    robot.data.materials.clear()
    mat_prev = make_brawl_preview_material("M_Brawl_Main", "cha_brawl_main")
    robot.data.materials.append(mat_prev)
    for poly in robot.data.polygons:
        poly.material_index = 0

    # Verify bounds & normals
    xs = [v.co.x for v in robot.data.vertices]
    ys = [v.co.y for v in robot.data.vertices]
    zs = [v.co.z for v in robot.data.vertices]
    print(f"[Bounds] Robot Blender space: X=[{min(xs):.3f},{max(xs):.3f}] Y=[{min(ys):.3f},{max(ys):.3f}] Z=[{min(zs):.3f},{max(zs):.3f}]")

    # 8. Export Standard Blender Z-up FBX (axis_forward='-Z', axis_up='Y' is Blender default! Wait: let's export with standard Y-up, -Z forward or -Y/+Z handled cleanly)
    # Using axis_forward='-Z', axis_up='Y' transforms Blender (+X, -Y_fwd, +Z_up) -> FBX (+X, +Y_up, -Z_fwd)
    # Wait: BuildTarnInspectionScene.DetectAxisSpec inspects vertex coords & bone weights inside Unity and sets AxisSpec automatically!
    bpy.ops.object.select_all(action="DESELECT")
    robot.select_set(True)
    new_arm.select_set(True)
    bpy.context.view_layer.objects.active = new_arm
    for fbx_out in (FBX_OUT_DIR / "brawl_robot_prepared.fbx", UNITY_BRAWL_DIR / "brawl_robot_prepared.fbx"):
        bpy.ops.export_scene.fbx(
            filepath=str(fbx_out),
            use_selection=True,
            object_types={"ARMATURE", "MESH"},
            apply_scale_options="FBX_SCALE_ALL",
            axis_forward="-Z",
            axis_up="Y",
            add_leaf_bones=False,
            bake_anim=False,
        )
    print(f"[✓] Exported Prepared Robot FBX: {UNITY_BRAWL_DIR / 'brawl_robot_prepared.fbx'}")

    bpy.ops.wm.save_as_mainfile(filepath=str(ALIGNED_DIR / "brawl_robot_aligned.blend"))

    # 9. Render Gate 2 Blender Side-by-Side Comparison (Official Megatron OBJ + Brawl)
    bpy.ops.wm.obj_import(filepath=str(DONOR_OBJ))
    meg_ref = bpy.context.selected_objects[0]
    meg_ref.name = "Megatron_Donor_Ref"
    # Note: OBJ import maps OBJ Y-up -> Blender Z-up automatically (+X left vs -X?)
    # Check Megatron OBJ Left/Right & position side-by-side at X = -4.2 (screen left from -Y cam!)
    meg_xs = [(meg_ref.matrix_world @ v.co).x for v in meg_ref.data.vertices]
    meg_ref.location = (-4.2 - 0.5 * (min(meg_xs) + max(meg_xs)), 0.0, 0.0)
    new_arm.location = (4.2, 0.0, 0.0)
    bpy.context.view_layer.update()

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    if scene.world is None:
        scene.world = bpy.data.worlds.new("World")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.12, 0.13, 0.16, 1.0)
        bg.inputs[1].default_value = 0.8

    for lx, ly, lz, energy in [(6, -12, 12, 3000), (-8, -10, 8, 2000), (0, 12, 10, 1800)]:
        ld = bpy.data.lights.new("L", type="POINT")
        ld.energy = energy
        lo = bpy.data.objects.new("Light", ld)
        lo.location = (lx, ly, lz)
        scene.collection.objects.link(lo)

    cam_d = bpy.data.cameras.new("Cam")
    cam_d.lens = 45
    cam = bpy.data.objects.new("Cam", cam_d)
    cam.location = (0.0, -24.0, 6.2)
    direction = Vector((0.0, 0.0, 5.5)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(cam)
    scene.camera = cam

    out_png = RENDERS_DIR / "gate2_blender_robot_sbs.png"
    scene.render.filepath = str(out_png)
    bpy.ops.render.render(write_still=True)
    print(f"[✓] Rendered Gate 2 Blender SBS: {out_png}")

    # Close-up of Right Hand gripping Hammer (Brawl offset at X=4.2, RightHand at X = 4.2 - 2.47 = 1.73)
    wri_world = new_arm.location + meg_pos["RightForeArm"]
    # Estimate hand height around Z=5.1, Y=-0.5, X=4.2 + meg_pos["LeftHand"].x*(-1) = 4.2 - 2.47 = 1.73
    rh_focus = Vector((4.2 - meg_pos["LeftHand"].x, meg_pos["LeftHand"].y - 0.6, meg_pos["LeftHand"].z - 0.2))
    cam.location = rh_focus + Vector((-4.8, -4.5, 1.4))
    cam.rotation_euler = (rh_focus - cam.location).to_track_quat("-Z", "Y").to_euler()
    out_rh = RENDERS_DIR / "gate2_blender_rhand_hammer.png"
    scene.render.filepath = str(out_rh)
    bpy.ops.render.render(write_still=True)
    print(f"[✓] Rendered Gate 2 Right-Hand Hammer Grip Closeup: {out_rh}")


if __name__ == "__main__":
    main()
