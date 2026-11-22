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

print("=== [Swindle] Gate 1 & 2 Master Robot Pipeline (FOC -> 2048 Atlas -> 53-Bone Retarget) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
DONOR_JSON = ROOT / "3rd-party-models" / "Swindle" / "00_donor_reference" / "wheeljack_donor_summary.json"
TEX_DIR = ROOT / "3rd-party-models" / "Swindle" / "02_textures"
ALIGNED_DIR = ROOT / "3rd-party-models" / "Swindle" / "01_aligned_mesh"
FBX_OUT_DIR = ROOT / "3rd-party-models" / "Swindle" / "03_fbx_exports"
UNITY_SWINDLE_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Swindle"
RENDERS_DIR = ROOT / "renders" / "swindle"

for d in (ALIGNED_DIR, FBX_OUT_DIR, UNITY_SWINDLE_DIR, RENDERS_DIR):
    d.mkdir(parents=True, exist_ok=True)

SWINDLE_MESH_NAMES = [
    "RB_Swindle_CHARSKEL_Head.mo.dmx",
    "RB_Swindle_CHARSKEL_Chest.mo.dmx",
    "RB_Swindle_CHARSKEL_CapL.mo.dmx",
    "RB_Swindle_CHARSKEL_CapR.mo.dmx",
    "RB_Swindle_CHARSKEL_ArmLoL.mo.dmx",
    "Bazooka_ARM.dmx",
    "RB_Swindle_CHARSKEL_Legs.mo.dmx",
    "RB_Swindle_STAT_Wheel.mo.001.dmx",
    "RB_Swindle_STAT_Wheel.mo.002.dmx",
    "RB_Swindle_STAT_Wheel.mo.003.dmx",
    "RB_Swindle_STAT_Wheel.mo.dmx",
]

# 2048 Atlas UV Boxes (u_scale, u_off, v_scale, v_off)
ROBOT_UV_MAP = {
    "RB_Swindle_Chest_INST":        (0.5,   0.0,   0.5,  0.5),
    "WEP_Bazooka_MATINST":          (0.5,   0.5,   0.5,  0.5),
    "RB_Swindle_Legs_INST":         (0.5,   0.0,   0.5,  0.0),
    "RB_Swindle_Head_INST":         (0.25,  0.5,   0.25, 0.25),
    "RB_Swindle_ArmLo_INST":        (0.25,  0.75,  0.25, 0.25),
    "RB_Swindle_ArmUp_INST":        (0.25,  0.5,   0.25, 0.0),
    "RB_Swindle_Wheel_INST":        (0.125, 0.75,  0.25, 0.0),
    "TR_FactionLogo_Mat_INST.003":  (0.125, 0.875, 0.25, 0.0),
}


def unity_to_blender(upos):
    return Vector((-float(upos[0]), -float(upos[2]), float(upos[1])))


def load_wheeljack_bones():
    donor = json.loads(DONOR_JSON.read_text(encoding="utf-8"))
    rest_pos = donor["rest_positions"]
    pos_b = {}
    for bname, upos in rest_pos.items():
        pos_b[bname] = unity_to_blender(upos)
    return pos_b, donor["bones"], donor["hierarchy"]


def remap_uvs_clean(obj, uv_map, default_box=(0.5, 0.0, 0.5, 0.5)):
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


def make_swindle_preview_material(name, prefix):
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


def split_ue3_2shell_fingers(arm, arm_mesh_obj, side="L"):
    adj = [set() for _ in range(len(arm_mesh_obj.data.vertices))]
    for e in arm_mesh_obj.data.edges:
        a, b = e.vertices[0], e.vertices[1]
        adj[a].add(b); adj[b].add(a)

    def find_shells(vset):
        seen = set()
        shells = []
        for start in sorted(vset):
            if start in seen: continue
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
    vg_map = {vg.name: vg.index for vg in arm_mesh_obj.vertex_groups}

    splits_info = []
    for fn in ("index", "middle", "ring", "pinky"):
        vg0_name = f"bip_{fn}_0_{side}"
        vg1_name = f"bip_{fn}_1_{side}"
        vg2_name = f"bip_{fn}_2_{side}"
        vg2 = arm_mesh_obj.vertex_groups.new(name=vg2_name)
        idx1 = vg_map[vg1_name]

        p0 = bone_heads[vg0_name]
        p1 = bone_heads[vg1_name]
        axis_dir = (p1 - p0).normalized()

        vset = {v.index for v in arm_mesh_obj.data.vertices if any(g.group == idx1 and g.weight > 0.25 for g in v.groups)}
        shells = find_shells(vset)
        major_shells = [s for s in shells if len(s) >= 10]
        major_shells.sort(key=lambda s: sum(((arm_mesh_obj.matrix_world @ arm_mesh_obj.data.vertices[vi].co) - p1).dot(axis_dir) for vi in s) / len(s))
        assert len(major_shells) >= 2, f"Expected >=2 major shells on {vg1_name}, got {[len(s) for s in shells]}"

        mid_shell = major_shells[0]
        tip_shell = major_shells[-1]
        mid_max = max(((arm_mesh_obj.matrix_world @ arm_mesh_obj.data.vertices[vi].co) - p1).dot(axis_dir) for vi in mid_shell)
        tip_min = min(((arm_mesh_obj.matrix_world @ arm_mesh_obj.data.vertices[vi].co) - p1).dot(axis_dir) for vi in tip_shell)
        tip_max = max(((arm_mesh_obj.matrix_world @ arm_mesh_obj.data.vertices[vi].co) - p1).dot(axis_dir) for vi in tip_shell)
        hinge_proj = 0.5 * (mid_max + tip_min)

        hinge_w = p1 + axis_dir * hinge_proj
        tip_w = p1 + axis_dir * max(tip_max, hinge_proj + 0.08)
        splits_info.append((vg1_name, vg2_name, f"bip_{fn}_tip_{side}", hinge_w, tip_w))

        for vi in tip_shell:
            w1 = 0.0
            for g in arm_mesh_obj.data.vertices[vi].groups:
                if g.group == idx1:
                    w1 = g.weight
            if w1 > 0.0:
                arm_mesh_obj.vertex_groups[idx1].remove([vi])
                vg2.add([vi], w1, "REPLACE")
        print(f"  [Split {fn:6s} {side}] mid={len(mid_shell)} verts -> {vg1_name}, tip={len(tip_shell)} verts -> {vg2_name}")

    # Split Thumb_1
    t1_name = f"bip_thumb_1_{side}"
    t2_name = f"bip_thumb_2_{side}"
    vg_t2 = arm_mesh_obj.vertex_groups.new(name=t2_name)
    idx_t1 = vg_map[t1_name]
    pt0 = bone_heads[f"bip_thumb_0_{side}"]
    pt1 = bone_heads[t1_name]
    t_dir = (pt1 - pt0).normalized()
    t1_verts = [v.index for v in arm_mesh_obj.data.vertices if any(g.group == idx_t1 and g.weight > 0.25 for g in v.groups)]
    projs = [((arm_mesh_obj.matrix_world @ arm_mesh_obj.data.vertices[vi].co) - pt1).dot(t_dir) for vi in t1_verts]
    p_mid = 0.5 * (min(projs) + max(projs))
    t_hinge_w = pt1 + t_dir * p_mid
    t_tip_w = pt1 + t_dir * max(max(projs), p_mid + 0.06)
    splits_info.append((t1_name, t2_name, f"bip_thumb_tip_{side}", t_hinge_w, t_tip_w))
    moved_t = 0
    for vi, pr in zip(t1_verts, projs):
        if pr >= p_mid:
            w1 = next((g.weight for g in arm_mesh_obj.data.vertices[vi].groups if g.group == idx_t1), 0.0)
            if w1 > 0.0:
                arm_mesh_obj.vertex_groups[idx_t1].remove([vi])
                vg_t2.add([vi], w1, "REPLACE")
                moved_t += 1
    print(f"  [Split thumb  {side}] mid={len(t1_verts)-moved_t} verts -> {t1_name}, tip={moved_t} verts -> {t2_name}")

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


def main():
    wheel_pos, wheel_bones, wheel_hierarchy = load_wheeljack_bones()

    # 1. Import FOC Combaticons FBX & isolate Swindle parts
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=FBX_PATH)

    keep_names = set(SWINDLE_MESH_NAMES) | {"Swindle_ARM"}
    for o in list(bpy.data.objects):
        if o.name not in keep_names:
            bpy.data.objects.remove(o, do_unlink=True)

    arm = bpy.data.objects.get("Swindle_ARM")
    assert arm is not None, "Missing Swindle_ARM!"
    robot_objs = [bpy.data.objects[n] for n in SWINDLE_MESH_NAMES if n in bpy.data.objects]
    assert len(robot_objs) == len(SWINDLE_MESH_NAMES), f"Expected {len(SWINDLE_MESH_NAMES)} meshes, found {len(robot_objs)}"

    # 2. Remap UVs
    for obj in robot_objs:
        remap_uvs_clean(obj, ROBOT_UV_MAP)
    print(f"[✓] Remapped UVs for all {len(robot_objs)} Swindle robot parts into 2048 Atlas.")

    # 3. Split Left and Right hand 2-shell fingers -> 3 phalanges
    arml_obj = bpy.data.objects["RB_Swindle_CHARSKEL_ArmLoL.mo.dmx"]
    baz_obj = bpy.data.objects["Bazooka_ARM.dmx"]
    split_ue3_2shell_fingers(arm, arml_obj, side="L")
    split_ue3_2shell_fingers(arm, baz_obj, side="R")

    # 4. Transform Swindle_ARM into Blender space (Left=+X, Forward=-Y, Up=+Z, det=+1)
    # Raw shoulder height: ~4.45m -> Wheeljack shoulder: 7.79m => Scale = 1.75
    SCALE_SWINDLE = 1.75
    arm.location = (0.0, 0.0, 0.0)
    arm.rotation_euler = (0.0, 0.0, math.radians(-90.0))
    arm.scale = (SCALE_SWINDLE, SCALE_SWINDLE, SCALE_SWINDLE)
    bpy.context.view_layer.update()

    test_lh = (arm.matrix_world @ arm.data.bones["bip_hand_L"].head_local)
    test_toe = (arm.matrix_world @ arm.data.bones["bip_toe_L"].head_local)
    print(f"[AxisVerify] Blender space: LeftHand={tuple(round(c,3) for c in test_lh)} (+X expected), LeftToe={tuple(round(c,3) for c in test_toe)} (-Y expected)")
    assert test_lh.x > 0.5 and test_toe.y < -0.1, f"Axis mismatch! LH={test_lh}, Toe={test_toe}"

    # 5. Pose Legs FIRST -> Ground via min_z -> Align Torso/Arms/Hands/Fingers!
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")

    # 5a. Pose Legs into Wheeljack's stance
    for side, sgn in (("L", 1.0), ("R", -1.0)):
        wj_side = "Left" if side == "L" else "Right"
        h_p = pb_head_w(arm, f"bip_hip_{side}")
        u_t = wheel_pos[f"{wj_side}UpLeg"]
        k_t = wheel_pos[f"{wj_side}Leg"]
        f_t = wheel_pos[f"{wj_side}Foot"]
        t_t = wheel_pos[f"{wj_side}ToeBase"]
        pose_segment_world(arm, f"bip_hip_{side}", f"bip_knee_{side}", u_t, k_t, thickness_scale=0.96, preserve_length=False)
        pose_segment_world(arm, f"bip_knee_{side}", f"bip_foot_{side}", k_t, f_t, thickness_scale=0.96, preserve_length=False)
        pose_segment_world(arm, f"bip_foot_{side}", f"bip_toe_{side}", f_t, t_t, thickness_scale=0.96, preserve_length=True)

    # 5b. Measure true foot bottom min_z and ground the armature
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
    print(f"[✓] Grounded Swindle_ARM (shifted Z by {-min_z:.4f}m BEFORE aligning arms & fingers)")

    # 5c. Pose Arms & All 30 Fingers 1:1 onto Wheeljack BindPose coordinates!
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")

    for side, sgn in (("L", 1.0), ("R", -1.0)):
        wj_side = "Left" if side == "L" else "Right"
        ua_name = f"bip_upperArm_{side}"
        la_name = f"bip_lowerArm_{side}"
        h_name = f"bip_hand_{side}"

        sh_t = wheel_pos[f"{wj_side}Shoulder"]
        arm_t = wheel_pos[f"{wj_side}Arm"]
        elb_t = wheel_pos[f"{wj_side}ForeArm"]
        wri_t = wheel_pos[f"{wj_side}Hand"]

        pose_segment_world(arm, ua_name, la_name, arm_t, elb_t, thickness_scale=0.96, preserve_length=False)
        pose_segment_world(arm, la_name, h_name, elb_t, wri_t, thickness_scale=0.96, preserve_length=False)

        # Orient Hand palm so fingers point down (-Z)
        pb_h = arm.pose.bones[h_name]
        w_h = arm.matrix_world @ pb_h.matrix
        kn_i = pb_head_w(arm, f"bip_index_0_{side}")
        kn_p = pb_head_w(arm, f"bip_pinky_0_{side}")
        curr_kn = 0.5 * (kn_i + kn_p)
        targ_kn = 0.5 * (wheel_pos[f"{wj_side}HandIndex1"] + wheel_pos[f"{wj_side}HandPinky1"])

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
        curr_span = pb_head_w(arm, f"bip_index_0_{side}") - pb_head_w(arm, f"bip_pinky_0_{side}")
        targ_span = wheel_pos[f"{wj_side}HandIndex1"] - wheel_pos[f"{wj_side}HandPinky1"]
        ah = v_th.normalized()
        c_perp = (curr_span - ah * curr_span.dot(ah)).normalized()
        t_perp = (targ_span - ah * targ_span.dot(ah)).normalized()
        q_y = c_perp.rotation_difference(t_perp)
        w_h_now = arm.matrix_world @ pb_h.matrix
        pb_h.matrix = arm.matrix_world.inverted() @ (
            Matrix.Translation(wri_t) @ q_y.to_matrix().to_4x4() @ Matrix.Translation(-wri_t) @ w_h_now
        )
        bpy.context.view_layer.update()

        # Align all 15 fingers 1:1 onto Wheeljack BindPose coordinates
        for fn_low, fn_cap in (("thumb", "Thumb"), ("index", "Index"), ("middle", "Middle"), ("ring", "Ring"), ("pinky", "Pinky")):
            p1 = wheel_pos[f"{wj_side}Hand{fn_cap}1"]
            p2 = wheel_pos[f"{wj_side}Hand{fn_cap}2"]
            p3 = wheel_pos[f"{wj_side}Hand{fn_cap}3"]
            pt = p3 + (p3 - p2) * 0.90
            is_thumb = (fn_low == "thumb")
            pose_segment_world(arm, f"bip_{fn_low}_0_{side}", f"bip_{fn_low}_1_{side}", p1, p2, thickness_scale=0.95, preserve_length=is_thumb)
            h2 = pb_head_w(arm, f"bip_{fn_low}_1_{side}") if is_thumb else p2
            pose_segment_world(arm, f"bip_{fn_low}_1_{side}", f"bip_{fn_low}_2_{side}", h2, p3, thickness_scale=0.95, preserve_length=is_thumb)
            h3 = pb_head_w(arm, f"bip_{fn_low}_2_{side}") if is_thumb else p3
            pose_segment_world(arm, f"bip_{fn_low}_2_{side}", f"bip_{fn_low}_tip_{side}", h3, pt, thickness_scale=0.95, preserve_length=True)

    bpy.ops.object.mode_set(mode="OBJECT")

    # 6. Apply Armature modifiers on all 11 posed meshes, then join
    for obj in robot_objs:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        if obj.data.shape_keys:
            obj.shape_key_clear()
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
    robot.name = "cha_swindle_gs_00"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # 7. Bone Weight Remapping to Wheeljack's 53 bones
    bone_map = {
        "bip_pelvis": "Hips",
        "bip_spine_0": "Spine",
        "bip_spine_1": "Spine1",
        "bip_neck": "Neck",
        "bip_head": "Head",
        "bip_Jaw": "Head",
        # Wheels
        "RB_Swindle_STAT_Wheel.mo.001": "LeftShoulder",
        "RB_Swindle_STAT_Wheel.mo.003": "RightShoulder",
        "RB_Swindle_STAT_Wheel.mo": "LeftLeg",
        "RB_Swindle_STAT_Wheel.mo.002": "RightLeg",
        # Left Arm & Shoulder Pad
        "bip_collar_L": "LeftShoulder",
        "bip_upperArm_L": "LeftArm",
        "L_ClavRobo01_XT": "LeftArm",
        "L_CloudA_PadRobo01_XT": "LeftArm",
        "L_CloudA_PadRobo02_XT": "LeftArm",
        "L_CloudA_PadRobo03_XT": "LeftArm",
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
        # Right Arm, Bazooka & Right Fingers
        "bip_collar_R": "RightShoulder",
        "bip_upperArm_R": "RightArm",
        "R_ClavRobo01_XT": "RightArm",
        "R_CloudA_PadRobo01_XT": "RightArm",
        "R_CloudA_PadRobo02_XT": "RightArm",
        "R_CloudA_PadRobo03_XT": "RightArm",
        "R_CloudA_PadRobo05_XT": "RightArm",
        "bip_lowerArm_R": "RightForeArm",
        "bip_hand_R": "RightHand",
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
        "WEP_Body_XB": "RightForeArm",
        # Legs
        "bip_hip_L": "LeftUpLeg",
        "bip_knee_L": "LeftLeg",
        "bip_foot_L": "LeftFoot",
        "bip_toe_L": "LeftToeBase",
        "bip_toe_L_end": "LeftToeBase",
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

    # 8. Build clean 53-bone Armature matching Wheeljack
    bpy.data.objects.remove(arm, do_unlink=True)
    arm_data = bpy.data.armatures.new("ARM_Swindle_Robot_Data")
    new_arm = bpy.data.objects.new("ARM_Swindle_Robot", arm_data)
    bpy.context.scene.collection.objects.link(new_arm)
    bpy.context.view_layer.objects.active = new_arm
    bpy.ops.object.mode_set(mode="EDIT")
    ebs = arm_data.edit_bones

    for bname in wheel_bones:
        p = wheel_pos[bname]
        eb = ebs.new(bname)
        eb.head = p
        p_name = wheel_hierarchy.get(bname)
        if p_name and p_name in wheel_pos:
            parent_p = wheel_pos[p_name]
            dir_v = (p - parent_p)
            if dir_v.length > 0.05:
                eb.tail = p + dir_v.normalized() * 0.15
            else:
                eb.tail = p + Vector((0, 0, 0.15))
        else:
            eb.tail = p + Vector((0, 0, 0.20))

    for bname in wheel_bones:
        p_name = wheel_hierarchy.get(bname)
        if p_name and p_name in ebs:
            ebs[bname].parent = ebs[p_name]

    bpy.ops.object.mode_set(mode="OBJECT")

    # 9. Apply vertex groups to robot mesh
    robot.vertex_groups.clear()
    for bname in wheel_bones:
        robot.vertex_groups.new(name=bname)

    vg_name_to_idx = {vg.name: vg.index for vg in robot.vertex_groups}
    for vi, wdict in enumerate(v_weights):
        for bname, w in wdict.items():
            if bname in vg_name_to_idx and w > 1e-4:
                robot.vertex_groups[vg_name_to_idx[bname]].add([vi], w, "REPLACE")

    robot.parent = new_arm
    mod = robot.modifiers.new("Armature", "ARMATURE")
    mod.object = new_arm

    # Material consolidation: 1 clean material
    robot.data.materials.clear()
    mat_r = make_swindle_preview_material("M_Swindle_Main", "cha_swindle_main")
    robot.data.materials.append(mat_r)
    for poly in robot.data.polygons:
        poly.material_index = 0

    # 10. Export prepared robot FBX
    bpy.ops.object.select_all(action="DESELECT")
    robot.select_set(True)
    new_arm.select_set(True)
    bpy.context.view_layer.objects.active = new_arm

    for fbx_out in (FBX_OUT_DIR / "swindle_robot_prepared.fbx", UNITY_SWINDLE_DIR / "swindle_robot_prepared.fbx"):
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
    print(f"[✓] Exported Prepared Robot FBX: {UNITY_SWINDLE_DIR / 'swindle_robot_prepared.fbx'}")
    bpy.ops.wm.save_as_mainfile(filepath=str(ALIGNED_DIR / "swindle_robot_aligned.blend"))


if __name__ == "__main__":
    main()
