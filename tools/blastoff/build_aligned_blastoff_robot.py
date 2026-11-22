import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import bmesh
import json
import math
import numpy as np
from collections import deque
from mathutils import Vector, Matrix, Quaternion
from pathlib import Path

print("=== [Blast Off] Gate 2 Master Robot Pipeline (FOC -> 2048 Atlas -> 55-Bone + 30 Articulated Fingers Retarget) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
DONOR_JSON = ROOT / "3rd-party-models" / "BlastOff" / "00_donor_reference" / "donor_summary.json"
DONOR_OBJ = ROOT / "3rd-party-models" / "BlastOff" / "00_donor_reference" / "cha_megatronus_gs_kabam_00_robot.obj"
TEX_DIR = ROOT / "3rd-party-models" / "BlastOff" / "02_textures"
ALIGNED_DIR = ROOT / "3rd-party-models" / "BlastOff" / "01_aligned_mesh"
FBX_OUT_DIR = ROOT / "3rd-party-models" / "BlastOff" / "03_fbx_exports"
UNITY_BLASTOFF_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "BlastOff"
RENDERS_DIR = ROOT / "renders" / "blastoff"

for d in (ALIGNED_DIR, FBX_OUT_DIR, UNITY_BLASTOFF_DIR, RENDERS_DIR):
    d.mkdir(parents=True, exist_ok=True)

MEGATRONUS_55_BONES = [
    "Neck", "Spine", "Spine1", "Hips",
    "RightUpLeg", "RightToeBase", "RightFoot", "RightLeg", "Head",
    "LeftFoot", "RightShoulderPad", "RightForeArm", "RightArm", "RightShoulder", "RightArmRoll",
    "RightHand", "RightHandMiddle1", "RightHandMiddle2", "RightHandMiddle3",
    "RightHandThumb1", "RightHandThumb2", "RightHandThumb3",
    "RightHandIndex1", "RightHandIndex2", "RightHandIndex3",
    "RightHandRing1", "RightHandRing2", "RightHandRing3",
    "RightHandPinky1", "RightHandPinky2", "RightHandPinky3",
    "LeftUpLeg", "LeftToeBase", "LeftLeg", "LeftShoulderPad", "LeftForeArm", "LeftArm",
    "LeftShoulder", "LeftArmRoll", "LeftHand",
    "LeftHandMiddle1", "LeftHandMiddle2", "LeftHandMiddle3",
    "LeftHandThumb1", "LeftHandThumb2", "LeftHandThumb3",
    "LeftHandIndex1", "LeftHandIndex2", "LeftHandIndex3",
    "LeftHandRing1", "LeftHandRing2", "LeftHandRing3",
    "LeftHandPinky1", "LeftHandPinky2", "LeftHandPinky3",
]

MEGATRONUS_PARENT_MAP = {
    "Hips": None,
    "Spine": "Hips",
    "Spine1": "Spine",
    "Neck": "Spine1",
    "Head": "Neck",
    "LeftShoulder": "Spine1",
    "LeftShoulderPad": "LeftShoulder",
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
    "RightShoulderPad": "RightShoulder",
    "RightArm": "RightShoulder",
    "RightArmRoll": "RightArm",
    "RightForeArm": "RightArmRoll",
    "RightHand": "RightForeArm",
    "RightHandThumb1": "RightHand",
    "RightHandThumb2": "RightHandThumb1",
    "RightHandThumb3": "RightHandThumb2",
    "RightHandIndex1": "RightHand",
    "RightHandIndex2": "RightHandIndex1",
    "RightHandIndex3": "RightHandIndex2",
    "RightHandMiddle1": "RightHand",
    "RightHandMiddle2": "RightHandMiddle1",
    "RightHandMiddle3": "RightHandMiddle2",
    "RightHandRing1": "RightHand",
    "RightHandRing2": "RightHandRing1",
    "RightHandRing3": "RightHandRing2",
    "RightHandPinky1": "RightHand",
    "RightHandPinky2": "RightHandPinky1",
    "RightHandPinky3": "RightHandPinky2",
    "LeftUpLeg": "Hips",
    "LeftLeg": "LeftUpLeg",
    "LeftFoot": "LeftLeg",
    "LeftToeBase": "LeftFoot",
    "RightUpLeg": "Hips",
    "RightLeg": "RightUpLeg",
    "RightFoot": "RightLeg",
    "RightToeBase": "RightFoot",
}

BLASTOFF_MESH_NAMES = [
    "RB_Blastoff_CHARSKEL_Head.001.dmx",
    "RB_Blastoff_CHARSKEL_ArmLoL.001.dmx",
    "RB_Blastoff_CHARSKEL_ArmLoR.001.dmx",
    "RB_BlastoffWing_STAT.001.dmx",
    "RB_BlastoffWing_STAT.dmx",
]

# OpenGL UV Atlas boxes: (u_scale, u_off, v_scale, v_off)
ROBOT_UV_MAP = {
    "RB_Blastoff_Chest_Cust_MatINST":    (0.5,   0.0,   0.5,  0.5),   # (0, 0, 1024, 1024)
    "RB_Blastoff_Legs_Cust_MatINST":     (0.5,   0.0,   0.5,  0.0),   # (0, 1024, 1024, 1024)
    "RB_Blastoff_Head_Cust_MatINST":     (0.25,  0.5,   0.25, 0.75),  # (1024, 0, 512, 512)
    "RB_Blastoff_ArmLo_Cust_MatINST":    (0.25,  0.75,  0.25, 0.75),  # (1536, 0, 512, 512)
    "RB_Blastoff_ArmUp_Cust_MatINST":    (0.25,  0.5,   0.25, 0.5),   # (1024, 512, 512, 512)
    "TR_FactionLogo_Mat_INST.001":       (0.25,  0.75,  0.25, 0.5),   # (1536, 512, 512, 512)
    "VH_Blastoff_Cust_MatINST":          (0.5,   0.5,   0.5,  0.0),   # (1024, 1024, 1024, 1024)
}


def unity_to_blender(upos):
    """Standard right-handed Blender coordinates (det=+1):
    Unity (ux, uy, uz) -> Blender (-ux, -uz, uy): Left=+X, Forward=-Y, Up=+Z.
    """
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


def remap_uvs_clean(obj, uv_map, default_box=(0.5, 0.0, 0.5, 0.5)):
    """Remap per-polygon UVs cleanly into atlas quadrants without seam-wrapping artifacts."""
    uv_layer = obj.data.uv_layers.active
    if not uv_layer:
        return
    mat_slots = [slot.material.name if slot.material else "" for slot in obj.material_slots]
    for poly in obj.data.polygons:
        mname = mat_slots[poly.material_index] if poly.material_index < len(mat_slots) else ""
        u_sc, u_off, v_sc, v_off = uv_map.get(mname, default_box)

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


def make_blastoff_preview_material(name, prefix):
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
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])

    tem = nt.nodes.new("ShaderNodeTexImage")
    tem.image = bpy.data.images.load(str(TEX_DIR / f"{prefix}_Emission.png"))
    nt.links.new(tem.outputs["Color"], bsdf.inputs["Emission"])
    bsdf.inputs["Emission Strength"].default_value = 2.0
    bsdf.inputs["Roughness"].default_value = 0.55
    bsdf.inputs["Metallic"].default_value = 0.25
    return mat


def split_ue3_2shell_fingers(arm, arm_obj, side="L"):
    """Per Pipeline Section 9.4: Split bip_{fn}_1_{side} into proximal/middle & distal tip,
    and split bip_thumb_1_{side} into mid/tip so all 15 finger phalanges articulate cleanly.
    """
    adj = [set() for _ in range(len(arm_obj.data.vertices))]
    for e in arm_obj.data.edges:
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

    bone_heads = {b.name: (arm.matrix_world @ b.head_local).copy() for b in arm.data.bones}
    vg_map = {vg.name: vg.index for vg in arm_obj.vertex_groups}

    splits_info = []
    for fn in ("index", "middle", "ring", "pinky"):
        vg0_name = f"bip_{fn}_0_{side}"
        vg1_name = f"bip_{fn}_1_{side}"
        vg2_name = f"bip_{fn}_2_{side}"
        vg2 = arm_obj.vertex_groups.new(name=vg2_name)
        idx0 = vg_map[vg0_name]
        idx1 = vg_map[vg1_name]

        p0 = bone_heads[vg0_name]
        p1 = bone_heads[vg1_name]
        axis_dir = (p1 - p0).normalized()

        vset = {v.index for v in arm_obj.data.vertices if any(g.group == idx1 and g.weight > 0.25 for g in v.groups)}
        shells = find_shells(vset)
        major_shells = [s for s in shells if len(s) >= 10]
        major_shells.sort(key=lambda s: sum(((arm_obj.matrix_world @ arm_obj.data.vertices[vi].co) - p1).dot(axis_dir) for vi in s) / len(s))
        assert len(major_shells) >= 2, f"Expected 2 major shells on {vg1_name}, got {[len(s) for s in shells]}"
        mid_shell = major_shells[0]
        tip_shell = major_shells[-1]
        mid_max = max(((arm_obj.matrix_world @ arm_obj.data.vertices[vi].co) - p1).dot(axis_dir) for vi in mid_shell)
        tip_min = min(((arm_obj.matrix_world @ arm_obj.data.vertices[vi].co) - p1).dot(axis_dir) for vi in tip_shell)
        tip_max = max(((arm_obj.matrix_world @ arm_obj.data.vertices[vi].co) - p1).dot(axis_dir) for vi in tip_shell)
        hinge_proj = 0.5 * (mid_max + tip_min)

        hinge_w = p1 + axis_dir * hinge_proj
        tip_w = p1 + axis_dir * max(tip_max, hinge_proj + 0.08)
        splits_info.append((vg1_name, vg2_name, f"bip_{fn}_tip_{side}", hinge_w, tip_w))

        for vi in tip_shell:
            w1 = 0.0
            for g in arm_obj.data.vertices[vi].groups:
                if g.group == idx1:
                    w1 = g.weight
            if w1 > 0.0:
                arm_obj.vertex_groups[idx1].remove([vi])
                vg2.add([vi], w1, "REPLACE")
        print(f"  [Split {fn:6s} {side}] mid={len(mid_shell)} verts -> {vg1_name}, tip={len(tip_shell)} verts -> {vg2_name}")

    # Split Thumb_1 cleanly by projection midpoint along thumb vector
    t1_name = f"bip_thumb_1_{side}"
    t2_name = f"bip_thumb_2_{side}"
    vg_t2 = arm_obj.vertex_groups.new(name=t2_name)
    idx_t1 = vg_map[t1_name]
    pt0 = bone_heads[f"bip_thumb_0_{side}"]
    pt1 = bone_heads[t1_name]
    t_dir = (pt1 - pt0).normalized()
    t1_verts = [v.index for v in arm_obj.data.vertices if any(g.group == idx_t1 and g.weight > 0.25 for g in v.groups)]
    projs = [((arm_obj.matrix_world @ arm_obj.data.vertices[vi].co) - pt1).dot(t_dir) for vi in t1_verts]
    p_mid = 0.5 * (min(projs) + max(projs))
    t_hinge_w = pt1 + t_dir * p_mid
    t_tip_w = pt1 + t_dir * max(max(projs), p_mid + 0.06)
    splits_info.append((t1_name, t2_name, f"bip_thumb_tip_{side}", t_hinge_w, t_tip_w))
    moved_t = 0
    for vi, pr in zip(t1_verts, projs):
        if pr >= p_mid:
            w1 = next((g.weight for g in arm_obj.data.vertices[vi].groups if g.group == idx_t1), 0.0)
            if w1 > 0.0:
                arm_obj.vertex_groups[idx_t1].remove([vi])
                vg_t2.add([vi], w1, "REPLACE")
                moved_t += 1
    print(f"  [Split thumb  {side}] mid={len(t1_verts)-moved_t} verts -> {t1_name}, tip={moved_t} verts -> {t2_name}")

    # Create new EditBones in armature matching those exact world positions
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
    bpy.context.view_layer.update()
    return arm_obj.matrix_world @ arm_obj.pose.bones[bname].head


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    meg_pos = load_megatronus_bones()
    SCALE_FACTOR = 1.0  # Preserve 1.0x BindPose matching Megatronus prefab bones exactly (M_bone * M_bind^-1 = I)
    meg_pos = {b: pos * SCALE_FACTOR for b, pos in meg_pos.items()}
    print(f"[✓] Loaded {len(meg_pos)} Megatronus bone coordinates at native 1.0x scale.")

    print(f"[*] Importing FBX from {FBX_PATH}...")
    bpy.ops.import_scene.fbx(filepath=FBX_PATH)

    arm = bpy.data.objects.get("Blast-off_ARM")
    assert arm, "Missing Blast-off_ARM!"

    robot_objs = [bpy.data.objects[n] for n in BLASTOFF_MESH_NAMES if n in bpy.data.objects]
    print(f"[✓] Found {len(robot_objs)} robot mesh objects for Blast Off.")

    # Remove all other objects in scene
    keep_objs = set(robot_objs) | {arm}
    for o in list(bpy.data.objects):
        if o not in keep_objs:
            bpy.data.objects.remove(o, do_unlink=True)

    # 0. Center Blast Off to world origin: In raw FOC scene, Blast Off was offset at Y = -10.0118
    RAW_OFFSET_Y = 10.0118
    arm.location.y += RAW_OFFSET_Y
    for obj in robot_objs:
        obj.location.y += RAW_OFFSET_Y
    bpy.context.view_layer.update()

    # 1. Coordinate Transform: R_z(-90)
    # FOC (+X=Fwd, +Y=Left, +Z=Up) -> Blender (-Y=Fwd, +X=Left, +Z=Up)
    # R_z(-90) rotation matrix det = +1
    R_z90 = Matrix.Rotation(math.radians(-90), 4, 'Z')
    arm.matrix_world = R_z90 @ arm.matrix_world
    for obj in robot_objs:
        obj.matrix_world = R_z90 @ obj.matrix_world
    bpy.context.view_layer.update()

    # Apply transform so rotation is baked into geometry
    bpy.ops.object.select_all(action="DESELECT")
    for obj in robot_objs:
        obj.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    print("[✓] Applied R_z(-90) rotation cleanly to Blast Off robot and armature.")

    # 2. Remap per-polygon UVs into 2048 atlas
    for obj in robot_objs:
        remap_uvs_clean(obj, ROBOT_UV_MAP)
    print("[✓] Remapped all robot polygon UVs into atlas quadrants.")

    # 3. Disconnect finger edit bones and split 2-shell fingers on both Left & Right hands!
    arml_obj = bpy.data.objects.get("RB_Blastoff_CHARSKEL_ArmLoL.001.dmx")
    armr_obj = bpy.data.objects.get("RB_Blastoff_CHARSKEL_ArmLoR.001.dmx")

    split_ue3_2shell_fingers(arm, arml_obj, side="L")
    split_ue3_2shell_fingers(arm, armr_obj, side="R")
    print("[✓] Split all 10 fingers into 30 articulated phalanges on both Left and Right hands!")

    # 4. Scale Blast Off armature and meshes cleanly (2.2928x * SCALE_FACTOR)
    SCALE_BLASTOFF = 2.2928 * SCALE_FACTOR
    arm.scale = (SCALE_BLASTOFF, SCALE_BLASTOFF, SCALE_BLASTOFF)
    for obj in robot_objs:
        obj.scale = (SCALE_BLASTOFF, SCALE_BLASTOFF, SCALE_BLASTOFF)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in robot_objs:
        obj.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    print(f"[✓] Scaled Blast Off by {SCALE_BLASTOFF:.4f}x ({SCALE_FACTOR}x) to match Combaticons scale.")

    # Attach Armature modifier to all robot mesh objects so posing deforms vertices
    for obj in robot_objs:
        arm_mod = obj.modifiers.get("Armature")
        if not arm_mod:
            arm_mod = obj.modifiers.new("Armature", "ARMATURE")
        arm_mod.object = arm
    print(f"[✓] Attached Armature modifier to all {len(robot_objs)} robot mesh objects.")

    # 5. GATE 2 NATURAL PROPORTIONS: Preserve Natural Torso/Chest/Neck/Head Heights (Pipeline §9)
    # Never forcibly squash spine/neck onto hunchbacked donors, which destroys neck clearance and covers the head.
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")

    # 5a. Pose Legs cleanly into Megatronus stance width & foot ground placement
    for side, sgn in (("L", 1.0), ("R", -1.0)):
        meg_side = "Left" if side == "L" else "Right"
        h_p = pb_head_w(arm, f"bip_hip_{side}")
        stance_x = 0.8965 * SCALE_FACTOR * sgn
        k_t = Vector((stance_x, meg_pos[f"{meg_side}Leg"].y, meg_pos[f"{meg_side}Leg"].z))
        f_t = Vector((stance_x, meg_pos[f"{meg_side}Foot"].y, meg_pos[f"{meg_side}Foot"].z))
        t_t = Vector((stance_x, meg_pos[f"{meg_side}ToeBase"].y, meg_pos[f"{meg_side}ToeBase"].z))
        pose_segment_world(arm, f"bip_hip_{side}", f"bip_knee_{side}", Vector((stance_x, h_p.y, h_p.z)), k_t, thickness_scale=0.96, preserve_length=False)
        pose_segment_world(arm, f"bip_knee_{side}", f"bip_foot_{side}", k_t, f_t, thickness_scale=0.96, preserve_length=False)
        pose_segment_world(arm, f"bip_foot_{side}", f"bip_toe_{side}", f_t, t_t, thickness_scale=0.96, preserve_length=True)

    # 5b. Pose Torso, Arms & Wrists & All 30 Fingers 1:1 to Megatronus BindPose!
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

        # Palm dual-axis alignment
        pb_h = arm.pose.bones[h_name]
        w_h = arm.matrix_world @ pb_h.matrix
        kn_i = pb_head_w(arm, f"bip_index_0_{side}")
        kn_p = pb_head_w(arm, f"bip_pinky_0_{side}")
        curr_kn = 0.5 * (kn_i + kn_p)
        targ_kn = 0.5 * (meg_pos[f"{meg_side}HandIndex1"] + meg_pos[f"{meg_side}HandPinky1"])

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

        # Yaw twist alignment: Index -> Pinky span
        curr_span = pb_head_w(arm, f"bip_index_0_{side}") - pb_head_w(arm, f"bip_pinky_0_{side}")
        targ_span = meg_pos[f"{meg_side}HandIndex1"] - meg_pos[f"{meg_side}HandPinky1"]
        ah = v_th.normalized()
        c_perp = (curr_span - ah * curr_span.dot(ah)).normalized()
        t_perp = (targ_span - ah * targ_span.dot(ah)).normalized()
        q_y = c_perp.rotation_difference(t_perp)
        w_h_now = arm.matrix_world @ pb_h.matrix
        pb_h.matrix = arm.matrix_world.inverted() @ (
            Matrix.Translation(wri_t) @ q_y.to_matrix().to_4x4() @ Matrix.Translation(-wri_t) @ w_h_now
        )
        bpy.context.view_layer.update()

        # Align all 15 finger bones 1:1 onto Megatronus BindPose coordinates!
        for fn_low, fn_cap in (("thumb", "Thumb"), ("index", "Index"), ("middle", "Middle"), ("ring", "Ring"), ("pinky", "Pinky")):
            p1 = meg_pos[f"{meg_side}Hand{fn_cap}1"]
            p2 = meg_pos[f"{meg_side}Hand{fn_cap}2"]
            p3 = meg_pos[f"{meg_side}Hand{fn_cap}3"]
            pt = p3 + (p3 - p2) * 0.90
            is_thumb = (fn_low == "thumb")
            pose_segment_world(arm, f"bip_{fn_low}_0_{side}", f"bip_{fn_low}_1_{side}", p1, p2, thickness_scale=0.95, preserve_length=is_thumb)
            h2 = pb_head_w(arm, f"bip_{fn_low}_1_{side}") if is_thumb else p2
            pose_segment_world(arm, f"bip_{fn_low}_1_{side}", f"bip_{fn_low}_2_{side}", h2, p3, thickness_scale=0.95, preserve_length=is_thumb)
            h3 = pb_head_w(arm, f"bip_{fn_low}_2_{side}") if is_thumb else p3
            pose_segment_world(arm, f"bip_{fn_low}_2_{side}", f"bip_{fn_low}_tip_{side}", h3, pt, thickness_scale=0.95, preserve_length=True)

    print("[✓] Posed all 30 fingers (Left & Right) 1:1 onto Megatronus BindPose!")

    # 6. Apply Armature modifiers and join into unified mesh
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    for obj in robot_objs:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        for m in list(obj.modifiers):
            if m.type == "ARMATURE":
                bpy.ops.object.modifier_apply(modifier=m.name)

    # Join robot meshes into single mesh
    bpy.context.view_layer.objects.active = robot_objs[0]
    bpy.ops.object.join()
    robot_mesh = bpy.context.view_layer.objects.active
    robot_mesh.name = "cha_blastoff_robot"
    print(f"[✓] Joined robot meshes into '{robot_mesh.name}' ({len(robot_mesh.data.vertices)} vertices).")

    # Precise grounding shift to floor level (Z = 0.000m)
    min_z = min(v.co.z for v in robot_mesh.data.vertices)
    max_z = max(v.co.z for v in robot_mesh.data.vertices)
    print(f"[Grounding] Mesh Z before shift: [{min_z:.4f}, {max_z:.4f}]")
    for v in robot_mesh.data.vertices:
        v.co.z -= min_z
    print(f"[Grounding] Mesh Z after shift: [{min(v.co.z for v in robot_mesh.data.vertices):.4f}, {max(v.co.z for v in robot_mesh.data.vertices):.4f}]")

    # 7. Remap all 123 vertex groups -> Megatronus 55 Bones
    BONE_REMAP = {
        # Core
        "bip_pelvis": "Hips",
        "bip_spine_0": "Spine",
        "bip_spine_1": "Spine1",
        "bip_neck": "Neck",
        "bip_head": "Head",
        "C_Face01_Jaw_XF2": "Head",
        "C_Head01_Face_XF2": "Head",
        # Back wings
        "RB_BlastoffWing_STAT": "Spine1",
        "RB_BlastoffWing_STAT.001": "Spine1",
        # Left Leg
        "bip_hip_L": "LeftUpLeg",
        "L_ThighRobo01_XT": "LeftUpLeg",
        "bip_knee_L": "LeftLeg",
        "bip_foot_L": "LeftFoot",
        "bip_toe_L": "LeftToeBase",
        # Right Leg
        "bip_hip_R": "RightUpLeg",
        "R_ThighRobo01_XT": "RightUpLeg",
        "bip_knee_R": "RightLeg",
        "bip_foot_R": "RightFoot",
        "bip_toe_R": "RightToeBase",
        # Left Arm & Pad
        "bip_collar_L": "LeftShoulder",
        "L_CloudA_ClavRobo01_XT": "LeftShoulder",
        "bip_upperArm_L": "LeftArm",
        "bip_lowerArm_L": "LeftForeArm",
        "bip_hand_L": "LeftHand",
        # Right Arm & Pad
        "bip_collar_R": "RightShoulder",
        "R_CloudA_ClavRobo01_XT": "RightShoulder",
        "bip_upperArm_R": "RightArm",
        "bip_lowerArm_R": "RightForeArm",
        "bip_hand_R": "RightHand",
        # Left Fingers (15)
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
        # Right Fingers (15)
        "bip_thumb_0_R": "RightHandThumb1",
        "bip_thumb_1_R": "RightHandThumb2",
        "bip_thumb_2_R": "RightHandThumb3",
        "bip_index_0_R": "RightHandIndex1",
        "bip_index_1_R": "RightHandIndex2",
        "bip_index_2_R": "RightHandIndex3",
        "bip_middle_0_R": "RightHandMiddle1",
        "bip_middle_1_R": "RightHandMiddle2",
        "bip_middle_2_R": "RightHandMiddle3",
        "bip_ring_0_R": "RightHandRing1",
        "bip_ring_1_R": "RightHandRing2",
        "bip_ring_2_R": "RightHandRing3",
        "bip_pinky_0_R": "RightHandPinky1",
        "bip_pinky_1_R": "RightHandPinky2",
        "bip_pinky_2_R": "RightHandPinky3",
    }

    # Additional patterns:
    # Lumbar -> Spine / Spine1
    # Face -> Head
    # CloudA_Pad -> ShoulderPad
    # CloudA_Shoulder -> Arm
    # CloudA_Elbow -> ForeArm
    # Knee -> Leg
    def resolve_target_bone(vg_name):
        if vg_name in BONE_REMAP:
            return BONE_REMAP[vg_name]
        low = vg_name.lower()
        if "pad" in low:
            return "LeftShoulderPad" if "_l" in low or "l_" in low else "RightShoulderPad"
        if "clav" in low:
            return "LeftShoulder" if "_l" in low or "l_" in low else "RightShoulder"
        if "shoulder" in low:
            return "LeftArm" if "_l" in low or "l_" in low else "RightArm"
        if "elbow" in low:
            return "LeftForeArm" if "_l" in low or "l_" in low else "RightForeArm"
        if "knee" in low:
            return "LeftLeg" if "_l" in low or "l_" in low else "RightLeg"
        if "thigh" in low:
            return "LeftUpLeg" if "_l" in low or "l_" in low else "RightUpLeg"
        if "lumbar" in low:
            return "Spine1"
        if "face" in low or "eyelid" in low or "cheek" in low or "lip" in low:
            return "Head"
        if "wing" in low:
            return "Spine1"
        return "Spine1"

    # Merge weights into Megatronus 55 bone vertex groups
    old_vgs = {vg.name: vg.index for vg in robot_mesh.vertex_groups}
    new_vgs = {}
    for b in MEGATRONUS_55_BONES:
        new_vgs[b] = robot_mesh.vertex_groups.new(name=b)

    for v in robot_mesh.data.vertices:
        w_acc = {}
        for g in v.groups:
            if g.group in old_vgs.values():
                vg_orig = [k for k, val in old_vgs.items() if val == g.group][0]
                targ_b = resolve_target_bone(vg_orig)
                w_acc[targ_b] = w_acc.get(targ_b, 0.0) + g.weight

        # Normalize weights
        tot_w = sum(w_acc.values())
        if tot_w > 1e-4:
            for tb, tw in w_acc.items():
                new_vgs[tb].add([v.index], tw / tot_w, "REPLACE")
        else:
            # Zero-weight fallback: bind based on height
            wz = (robot_mesh.matrix_world @ v.co).z
            fb = "Spine1" if wz > 8.0 * SCALE_FACTOR else ("Hips" if wz > 5.0 * SCALE_FACTOR else "LeftLeg")
            new_vgs[fb].add([v.index], 1.0, "REPLACE")

    # Clean up old vertex groups
    for old_name in old_vgs:
        if old_name not in MEGATRONUS_55_BONES:
            vg = robot_mesh.vertex_groups.get(old_name)
            if vg:
                robot_mesh.vertex_groups.remove(vg)

    print("[✓] Consolidated all vertex groups into Megatronus 55 bones.")

    # 8. Rebuild Clean Megatronus Armature with all 55 bones at exact authoritative coordinates
    bpy.data.objects.remove(arm, do_unlink=True)
    new_arm_data = bpy.data.armatures.new("cha_blastoff_armature")
    new_arm = bpy.data.objects.new("cha_blastoff_armature", new_arm_data)
    bpy.context.collection.objects.link(new_arm)
    bpy.context.view_layer.objects.active = new_arm
    bpy.ops.object.mode_set(mode="EDIT")
    ebs = new_arm_data.edit_bones

    for bname in MEGATRONUS_55_BONES:
        eb = ebs.new(bname)
        head_pos = meg_pos[bname]
        eb.head = head_pos
        # Set clean tail offset
        if "Foot" in bname:
            eb.tail = head_pos + Vector((0, -0.45 * SCALE_FACTOR, -0.65 * SCALE_FACTOR))
        elif "Hand" in bname and any(f in bname for f in ["Thumb", "Index", "Middle", "Ring", "Pinky"]):
            eb.tail = head_pos + Vector((0, 0, -0.25 * SCALE_FACTOR)) if "Thumb" not in bname else head_pos + Vector((0, -0.25 * SCALE_FACTOR, 0))
        elif "Hand" in bname:
            eb.tail = head_pos + Vector((0, 0, -0.45 * SCALE_FACTOR))
        elif "Head" in bname:
            eb.tail = head_pos + Vector((0, 0, 0.75 * SCALE_FACTOR))
        elif "Pad" in bname:
            eb.tail = head_pos + Vector((0.3 * SCALE_FACTOR if "Left" in bname else -0.3 * SCALE_FACTOR, 0, 0.4 * SCALE_FACTOR))
        else:
            eb.tail = head_pos + Vector((0, 0, 0.45 * SCALE_FACTOR))

    for bname, pname in MEGATRONUS_PARENT_MAP.items():
        if pname and pname in ebs and bname in ebs:
            ebs[bname].parent = ebs[pname]

    bpy.ops.object.mode_set(mode="OBJECT")
    print(f"[✓] Created clean 55-bone Megatronus armature for Blast Off.")

    # 9. Bind mesh to new armature
    robot_mesh.modifiers.clear()
    arm_mod = robot_mesh.modifiers.new("Armature", "ARMATURE")
    arm_mod.object = new_arm
    robot_mesh.parent = new_arm

    # Assign single unified preview material
    mat = make_blastoff_preview_material("mat_blastoff_robot", "cha_blastoff_main")
    robot_mesh.data.materials.clear()
    robot_mesh.data.materials.append(mat)

    # 10. Render Side-by-Side Verification with Megatronus official OBJ
    print("=== Rendering Gate 2 Side-by-Side Comparison ===")
    if DONOR_OBJ.exists():
        bpy.ops.wm.obj_import(filepath=str(DONOR_OBJ))
        host_obj = bpy.context.selected_objects[0]
        host_obj.name = "Megatronus_Host_Reference"
        # Move donor to the left (-X in Blender, which is Right in Unity)
        host_obj.location.x = -6.8
        robot_mesh.location.x = 0.0

        cam_data = bpy.data.cameras.new("Gate2_Camera")
        cam_obj = bpy.data.objects.new("Gate2_Camera", cam_data)
        bpy.context.collection.objects.link(cam_obj)
        # Position camera in front (-Y in Blender)
        cam_data.lens = 32.0
        cam_obj.location = (-3.4, -32.0, 6.2)
        cam_obj.rotation_euler = (math.radians(88), 0, 0)
        bpy.context.scene.camera = cam_obj

        # Add key lighting
        light_data = bpy.data.lights.new("Gate2_Sun", "SUN")
        light_data.energy = 3.5
        light_obj = bpy.data.objects.new("Gate2_Sun", light_data)
        bpy.context.collection.objects.link(light_obj)
        light_obj.rotation_euler = (math.radians(45), math.radians(25), 0)

        bpy.context.scene.render.resolution_x = 1920
        bpy.context.scene.render.resolution_y = 1080
        out_render = RENDERS_DIR / "gate2_blender_robot_sbs.png"
        bpy.context.scene.render.filepath = str(out_render)
        bpy.ops.render.render(write_still=True)
        print(f"[✓] Rendered Gate 2 Side-by-Side: {out_render}")

        bpy.data.objects.remove(host_obj, do_unlink=True)
        bpy.data.objects.remove(cam_obj, do_unlink=True)
        bpy.data.objects.remove(light_obj, do_unlink=True)

    # 11. Export prepared robot FBX
    fbx_out = FBX_OUT_DIR / "blastoff_robot_prepared.fbx"
    unity_fbx_out = UNITY_BLASTOFF_DIR / "blastoff_robot_prepared.fbx"

    bpy.ops.object.select_all(action="DESELECT")
    robot_mesh.select_set(True)
    new_arm.select_set(True)
    bpy.context.view_layer.objects.active = new_arm

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
    print(f"[✓] Exported {fbx_out} ({fbx_out.stat().st_size} bytes)")

    import shutil
    shutil.copy2(fbx_out, unity_fbx_out)
    print(f"[✓] Synced FBX -> {unity_fbx_out}")


if __name__ == "__main__":
    main()
