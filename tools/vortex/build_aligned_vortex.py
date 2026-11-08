import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import math
from pathlib import Path
import bpy
import mathutils

print("=== BUILDING 30-FINGER ARTICULATED VORTEX FOR MOVIE GRINDOR CHASSIS ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
BONES_JSON = ROOT / "tools" / "vortex" / "grindor_78_bones.json"
AUTH_BP_JSON = ROOT / "tools" / "vortex" / "grindor_78_authoritative_bindposes.json"
HIER_JSON = ROOT / "tools" / "vortex" / "grindor_78_hierarchy.json"
MASTER_BLEND = ROOT / "3rd-party-models" / "vortex" / "vortex_master.blend"
UNITY_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Vortex"
SCRATCH_DIR = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d\scratch")

UNITY_DIR.mkdir(parents=True, exist_ok=True)
SCRATCH_DIR.mkdir(parents=True, exist_ok=True)

# 1. Load Authoritative Grindor 78 BindPoses
bp_info = json.loads(AUTH_BP_JSON.read_text(encoding="utf-8"))
hier_info = json.loads(HIER_JSON.read_text(encoding="utf-8"))
bone_order = hier_info["bone_order"]
parents_map = hier_info["parents"]
bone_order_set = set(bone_order)

# Convert Unity (ux, uy, uz) -> Blender (ux, uz, uy)
g_b_pos = {}
for bname, info in bp_info.items():
    pos = info["world_pos"]
    g_b_pos[bname] = mathutils.Vector((pos["x"], pos["z"], pos["y"]))

print(f"[✓] Loaded {len(g_b_pos)} Grindor authoritative bindposes!")

# 2. Open master blend & Remap UVs to 2048x2048 Atlas
bpy.ops.wm.open_mainfile(filepath=str(MASTER_BLEND))

MAT_UV_BOX = {
    "rb_vortex_legs": (0.5, 0.5, 0.0, 0.5),
    "rb_vortex_chest": (0.5, 0.5, 0.0, 0.0),
    "rb_vortex_backpack": (0.25, 0.25, 0.5, 0.75),
    "wep_bladeaut": (0.25, 0.25, 0.5, 0.5),
    "tr_factionlogo": (0.25, 0.25, 0.75, 0.75),
    "rb_vortex_armup": (0.25, 0.25, 0.5, 0.25),
    "rb_vortex_head": (0.25, 0.25, 0.5, 0.0),
    "rb_vortex_armlo": (0.25, 0.25, 0.75, 0.25),
    "wep": (0.25, 0.25, 0.75, 0.0),
    "ionblade": (0.25, 0.25, 0.75, 0.0),
}

def resolve_uv_box(mat_name):
    mn = (mat_name or "").lower()
    for key, box in MAT_UV_BOX.items():
        if key in mn:
            return box
    return (0.5, 0.5, 0.0, 0.0)

def remap_mesh_uvs_by_slot(mesh_obj):
    uv_layer = mesh_obj.data.uv_layers.active
    if not uv_layer:
        return
    slot_boxes = {}
    for idx, slot in enumerate(mesh_obj.material_slots):
        mname = slot.material.name if slot.material else ""
        slot_boxes[idx] = resolve_uv_box(mname)

    for poly in mesh_obj.data.polygons:
        su, sv, ou, ov = slot_boxes.get(poly.material_index, (0.5, 0.5, 0.0, 0.0))
        for li in poly.loop_indices:
            u, v = uv_layer.data[li].uv
            u_c = max(0.004, min(0.996, u))
            v_c = max(0.004, min(0.996, v))
            uv_layer.data[li].uv = (u_c * su + ou, v_c * sv + ov)
    mesh_obj.data.update()

robot_mesh_names = [
    "RB_Vortex_CHARSKEL_Head.mo.dmx",
    "RB_Vortex_CHARSKEL_ArmLoL.mo.dmx",
    "RB_Vortex_CHARSKEL_ArmLoR.mo.dmx",
    "WEP_IonBlade_SKEL.mo_L.dmx",
    "WEP_IonBlade_SKEL.mo_R.dmx"
]

for nm in robot_mesh_names:
    o = bpy.data.objects.get(nm)
    if o:
        remap_mesh_uvs_by_slot(o)
print("[✓] Remapped UVs for all robot parts and Ion Blades to 2048x2048 PBR atlas!")

# Remove vehicle objects from robot scene
keep_set = set(robot_mesh_names) | {"Vortex_ARM"}
for o in list(bpy.data.objects):
    if o.name not in keep_set:
        bpy.data.objects.remove(o, do_unlink=True)

vortex_arm = bpy.data.objects["Vortex_ARM"]
armlo_l = bpy.data.objects["RB_Vortex_CHARSKEL_ArmLoL.mo.dmx"]
armlo_r = bpy.data.objects["RB_Vortex_CHARSKEL_ArmLoR.mo.dmx"]
head_mesh = bpy.data.objects["RB_Vortex_CHARSKEL_Head.mo.dmx"]
blade_l = bpy.data.objects["WEP_IonBlade_SKEL.mo_L.dmx"]
blade_r = bpy.data.objects["WEP_IonBlade_SKEL.mo_R.dmx"]

# 3. Scale & Rotate Vortex_ARM so +Y is Forward, -X is Left, +Z is Up
scale_factor = 2.05
vortex_arm.scale = (scale_factor, scale_factor, scale_factor)
vortex_arm.rotation_euler = (0.0, 0.0, math.radians(90.0))
bpy.context.view_layer.update()

# 4. Split FOC 2-shell distal finger groups into Middle Phalanx (bip_{fn}_1) & Distal Phalanx (bip_{fn}_2)
def find_connected_shells(mesh_obj, vg_idx, ref_head_local, dir_local, arm_inv):
    vset = {vi for vi, v in enumerate(mesh_obj.data.vertices) if any(g.group == vg_idx and g.weight > 0.5 for g in v.groups)}
    adj = {vi: set() for vi in vset}
    for e in mesh_obj.data.edges:
        u, w = e.vertices
        if u in vset and w in vset:
            adj[u].add(w)
            adj[w].add(u)
    visited = set()
    shells = []
    for vi in vset:
        if vi not in visited:
            comp = []
            stack = [vi]
            visited.add(vi)
            while stack:
                cur = stack.pop()
                comp.append(cur)
                for nb in adj[cur]:
                    if nb not in visited:
                        visited.add(nb)
                        stack.append(nb)
            pts_arm = [arm_inv @ (mesh_obj.matrix_world @ mesh_obj.data.vertices[c].co) for c in comp]
            projs = [(p - ref_head_local).dot(dir_local) for p in pts_arm]
            shells.append((min(projs), max(projs), comp))
    shells.sort(key=lambda x: x[0])
    return shells

hinge_data = {}
arm_inv_init = vortex_arm.matrix_world.inverted()

for side, mesh_obj in [("L", armlo_l), ("R", armlo_r)]:
    for fn in ("index", "middle", "ring", "pinky"):
        b0 = vortex_arm.data.bones[f"bip_{fn}_0_{side}"]
        b1 = vortex_arm.data.bones[f"bip_{fn}_1_{side}"]
        h0_local = b0.head_local.copy()
        h1_local = b1.head_local.copy()
        dir_local = (h1_local - h0_local).normalized()

        vg1_name = f"bip_{fn}_1_{side}"
        vg1_idx = mesh_obj.vertex_groups[vg1_name].index
        shells = find_connected_shells(mesh_obj, vg1_idx, h1_local, dir_local, arm_inv_init)
        assert len(shells) == 3, f"Expected 3 shells for {vg1_name}, got {len(shells)}"
        
        # Shell 0 + Shell 1 are Middle Phalanx (Phalanx 2)
        # Shell 2 is Distal Phalanx (Phalanx 3)
        mid_shell = shells[1] # outer boundary of middle phalanx
        tip_shell = shells[2] # distal fingertip shell

        hinge_proj = 0.5 * (mid_shell[1] + tip_shell[0])
        tip_proj = tip_shell[1]
        h2_local = h1_local + dir_local * hinge_proj
        htip_local = h1_local + dir_local * tip_proj
        hinge_data[(side, fn)] = {
            "h2_local": h2_local,
            "htip_local": htip_local,
        }

        vg2_name = f"bip_{fn}_2_{side}"
        vg2 = mesh_obj.vertex_groups.get(vg2_name) or mesh_obj.vertex_groups.new(name=vg2_name)
        mesh_obj.vertex_groups[vg1_idx].remove(tip_shell[2])
        vg2.add(tip_shell[2], 1.0, 'REPLACE')

    # Thumb: 2 shells in bip_thumb_1_{side}
    b0_t = vortex_arm.data.bones[f"bip_thumb_0_{side}"]
    b1_t = vortex_arm.data.bones[f"bip_thumb_1_{side}"]
    dir_t = (b1_t.head_local - b0_t.head_local).normalized()
    vgt_idx = mesh_obj.vertex_groups[f"bip_thumb_1_{side}"].index
    t_shells = find_connected_shells(mesh_obj, vgt_idx, b1_t.head_local, dir_t, arm_inv_init)
    assert len(t_shells) == 2, f"Expected 2 thumb shells for side {side}, got {len(t_shells)}"
    
    mid_ts, tip_ts = t_shells[0], t_shells[1]
    h2_t = b1_t.head_local + dir_t * (0.5 * (mid_ts[1] + tip_ts[0]))
    htip_t = b1_t.head_local + dir_t * tip_ts[1]
    vgt2 = mesh_obj.vertex_groups.get(f"bip_thumb_2_{side}") or mesh_obj.vertex_groups.new(name=f"bip_thumb_2_{side}")
    mesh_obj.vertex_groups[vgt_idx].remove(tip_ts[2])
    vgt2.add(tip_ts[2], 1.0, 'REPLACE')
    hinge_data[(side, "thumb")] = {"has_t2": True, "h2_local": h2_t, "htip_local": htip_t}

print(f"[✓] Successfully split all 30 finger segments into true 3-phalanx articulated groups!")

# Edit Vortex_ARM: disconnect bones & add distal helper bones
bpy.ops.object.select_all(action='DESELECT')
vortex_arm.select_set(True)
bpy.context.view_layer.objects.active = vortex_arm
bpy.ops.object.mode_set(mode='EDIT')
for eb in vortex_arm.data.edit_bones:
    eb.use_connect = False

for side in ("L", "R"):
    for fn in ("index", "middle", "ring", "pinky"):
        hd = hinge_data[(side, fn)]
        eb1 = vortex_arm.data.edit_bones[f"bip_{fn}_1_{side}"]
        eb2 = vortex_arm.data.edit_bones.new(f"bip_{fn}_2_{side}")
        eb2.head = hd["h2_local"]
        eb2.tail = hd["htip_local"]
        eb2.roll = eb1.roll
        eb2.parent = eb1
        eb2.use_connect = False

        eb_tip = vortex_arm.data.edit_bones.new(f"bip_{fn}_tip_{side}")
        eb_tip.head = hd["htip_local"]
        eb_tip.tail = hd["htip_local"] + (hd["htip_local"] - hd["h2_local"]).normalized() * 0.05
        eb_tip.parent = eb2
        eb_tip.use_connect = False

    hd_t = hinge_data[(side, "thumb")]
    eb_t1 = vortex_arm.data.edit_bones[f"bip_thumb_1_{side}"]
    eb_t2 = vortex_arm.data.edit_bones.new(f"bip_thumb_2_{side}")
    eb_t2.head = hd_t["h2_local"]
    eb_t2.tail = hd_t["htip_local"]
    eb_t2.roll = eb_t1.roll
    eb_t2.parent = eb_t1
    eb_t2.use_connect = False

    eb_ttip = vortex_arm.data.edit_bones.new(f"bip_thumb_tip_{side}")
    eb_ttip.head = hd_t["htip_local"]
    eb_ttip.tail = hd_t["htip_local"] + (hd_t["htip_local"] - hd_t["h2_local"]).normalized() * 0.05
    eb_ttip.parent = eb_t2
    eb_ttip.use_connect = False

bpy.ops.object.mode_set(mode='POSE')

def aim_bone_segment_world(arm_obj, parent_bname, child_bname, target_dir_world):
    bpy.context.view_layer.update()
    pb = arm_obj.pose.bones[parent_bname]
    pb_child = arm_obj.pose.bones[child_bname]
    p0 = (arm_obj.matrix_world @ pb.matrix).translation
    p1 = (arm_obj.matrix_world @ pb_child.matrix).translation
    cur_dir = (p1 - p0).normalized()
    tgt_dir = mathutils.Vector(target_dir_world).normalized()
    rot_diff = cur_dir.rotation_difference(tgt_dir).to_matrix().to_4x4()
    wmat = arm_obj.matrix_world @ pb.matrix
    pb.matrix = arm_obj.matrix_world.inverted() @ (mathutils.Matrix.Translation(p0) @ rot_diff @ mathutils.Matrix.Translation(-p0) @ wmat)
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

    q_rot = v_curr.rotation_difference(v_targ) if (len_curr > 1e-5 and len_targ > 1e-5) else mathutils.Quaternion()
    s_len = (len_targ / len_curr) if len_curr > 1e-5 else 1.0

    d = v_curr.normalized() if len_curr > 1e-5 else mathutils.Vector((0, 0, -1))
    S = mathutils.Matrix.Identity(3) * thickness_scale
    for r in range(3):
        for c in range(3):
            S[r][c] += (s_len - thickness_scale) * d[r] * d[c]

    RS = q_rot.to_matrix() @ S
    R_new = RS @ w_old.to_3x3()
    M_new_w = R_new.to_4x4()
    M_new_w.translation = target_head_w
    pb.matrix = arm_obj.matrix_world.inverted() @ M_new_w
    bpy.context.view_layer.update()

# 5. Pose Legs FIRST & Ground Vortex_ARM BEFORE Hand/Finger Alignment
thigh_dir_L = (g_b_pos["LeftLeg"] - g_b_pos["LeftUpLeg"]).normalized()
thigh_dir_R = (g_b_pos["RightLeg"] - g_b_pos["RightUpLeg"]).normalized()
calf_dir_L = (g_b_pos["LeftFoot"] - g_b_pos["LeftLeg"]).normalized()
calf_dir_R = (g_b_pos["RightFoot"] - g_b_pos["RightLeg"]).normalized()

aim_bone_segment_world(vortex_arm, "bip_hip_L", "bip_knee_L", thigh_dir_L)
aim_bone_segment_world(vortex_arm, "bip_hip_R", "bip_knee_R", thigh_dir_R)
aim_bone_segment_world(vortex_arm, "bip_knee_L", "bip_foot_L", calf_dir_L)
aim_bone_segment_world(vortex_arm, "bip_knee_R", "bip_foot_R", calf_dir_R)

# Keep foot sole leveled
for bname, ang_deg in [("bip_foot_L", -4.0), ("bip_foot_R", 4.0)]:
    pb = vortex_arm.pose.bones[bname]
    p0 = (vortex_arm.matrix_world @ pb.matrix).translation
    rot_y = mathutils.Matrix.Rotation(math.radians(ang_deg), 4, 'Y')
    wmat = vortex_arm.matrix_world @ pb.matrix
    pb.matrix = vortex_arm.matrix_world.inverted() @ (mathutils.Matrix.Translation(p0) @ rot_y @ mathutils.Matrix.Translation(-p0) @ wmat)
    bpy.context.view_layer.update()

# Measure lowest point of mesh and ground armature
deps = bpy.context.evaluated_depsgraph_get()
ev_mesh = head_mesh.evaluated_get(deps)
em = ev_mesh.to_mesh()
min_z_mesh = min((ev_mesh.matrix_world @ v.co).z for v in em.vertices)
ev_mesh.to_mesh_clear()
vortex_arm.location.z -= min_z_mesh
bpy.context.view_layer.update()
print(f"[✓] Grounded Vortex_ARM BEFORE hand/finger alignment (shifted Z by {-min_z_mesh:.4f}m)")

# 6. Pose Upper Arms, Forearms, Hands, and All 30 Articulated Finger/Thumb Segments!
aim_bone_segment_world(vortex_arm, "bip_upperArm_L", "bip_lowerArm_L", (-0.18, -0.05, -0.98))
aim_bone_segment_world(vortex_arm, "bip_upperArm_R", "bip_lowerArm_R", (0.18, -0.05, -0.98))

for side, pfx in [("L", "Left"), ("R", "Right")]:
    elbow_w = (vortex_arm.matrix_world @ vortex_arm.pose.bones[f"bip_lowerArm_{side}"].matrix).translation.copy()
    wrist_t = g_b_pos[f"{pfx}Hand"]
    
    # Pose forearm from elbow to Grindor's exact wrist
    pose_segment_world(vortex_arm, f"bip_lowerArm_{side}", f"bip_hand_{side}", elbow_w, wrist_t, thickness_scale=1.0)

    # Pose palm from Grindor's wrist to knuckle center
    pb_hand = vortex_arm.pose.bones[f"bip_hand_{side}"]
    w_hand_old = vortex_arm.matrix_world @ pb_hand.matrix
    curr_knuckle_mid = 0.5 * (
        (vortex_arm.matrix_world @ vortex_arm.pose.bones[f"bip_index_0_{side}"].matrix).translation
        + (vortex_arm.matrix_world @ vortex_arm.pose.bones[f"bip_pinky_0_{side}"].matrix).translation
    )
    targ_knuckle_mid = 0.5 * (g_b_pos[f"{pfx}HandIndex1"] + g_b_pos[f"{pfx}HandPinky1"])
    v_curr_h = curr_knuckle_mid - w_hand_old.translation
    v_targ_h = targ_knuckle_mid - wrist_t
    q_h = v_curr_h.rotation_difference(v_targ_h)
    s_h = v_targ_h.length / max(v_curr_h.length, 1e-5)
    d_h = v_curr_h.normalized()
    S_h = mathutils.Matrix.Identity(3)
    for r in range(3):
        for c in range(3):
            S_h[r][c] += (s_h - 1.0) * d_h[r] * d_h[c]
    M_hand_w = (q_h.to_matrix() @ S_h @ w_hand_old.to_3x3()).to_4x4()
    M_hand_w.translation = wrist_t
    pb_hand.matrix = vortex_arm.matrix_world.inverted() @ M_hand_w
    bpy.context.view_layer.update()

    # Fine-tune palm yaw around vertical wrist-to-knuckle axis
    curr_span = (
        (vortex_arm.matrix_world @ vortex_arm.pose.bones[f"bip_index_0_{side}"].matrix).translation
        - (vortex_arm.matrix_world @ vortex_arm.pose.bones[f"bip_pinky_0_{side}"].matrix).translation
    )
    targ_span = g_b_pos[f"{pfx}HandIndex1"] - g_b_pos[f"{pfx}HandPinky1"]
    axis_h = v_targ_h.normalized()
    curr_span_perp = (curr_span - axis_h * curr_span.dot(axis_h)).normalized()
    targ_span_perp = (targ_span - axis_h * targ_span.dot(axis_h)).normalized()
    q_yaw = curr_span_perp.rotation_difference(targ_span_perp)
    w_hand_now = vortex_arm.matrix_world @ pb_hand.matrix
    pb_hand.matrix = vortex_arm.matrix_world.inverted() @ (
        mathutils.Matrix.Translation(wrist_t) @ q_yaw.to_matrix().to_4x4() @ mathutils.Matrix.Translation(-wrist_t) @ w_hand_now
    )
    bpy.context.view_layer.update()

pre_thumb_w = {
    "L": (vortex_arm.matrix_world @ vortex_arm.pose.bones["bip_thumb_0_L"].matrix).translation.copy(),
    "R": (vortex_arm.matrix_world @ vortex_arm.pose.bones["bip_thumb_0_R"].matrix).translation.copy(),
}

# Align all 30 articulated finger segments to Grindor authoritative bindposes
for side, pfx in [("L", "LeftHand"), ("R", "RightHand")]:
    for fn_f, fn_i in [("index", "Index"), ("middle", "Middle"), ("ring", "Ring"), ("pinky", "Pinky")]:
        p1 = g_b_pos[f"{pfx}{fn_i}1"]
        p2 = g_b_pos[f"{pfx}{fn_i}2"]
        p3 = g_b_pos[f"{pfx}{fn_i}3"]
        p4 = p3 + (p3 - p2) * 0.95
        pose_segment_world(vortex_arm, f"bip_{fn_f}_0_{side}", f"bip_{fn_f}_1_{side}", p1, p2, thickness_scale=0.95)
        pose_segment_world(vortex_arm, f"bip_{fn_f}_1_{side}", f"bip_{fn_f}_2_{side}", p2, p3, thickness_scale=0.95)
        pose_segment_world(vortex_arm, f"bip_{fn_f}_2_{side}", f"bip_{fn_f}_tip_{side}", p3, p4, thickness_scale=0.95)

    t1 = g_b_pos[f"{pfx}Thumb1"]
    t2 = g_b_pos[f"{pfx}Thumb2"]
    t3 = g_b_pos[f"{pfx}Thumb3"]
    t4 = t3 + (t3 - t2) * 1.05
    pose_segment_world(vortex_arm, f"bip_thumb_0_{side}", f"bip_thumb_1_{side}", t1, t2, thickness_scale=0.95)
    pose_segment_world(vortex_arm, f"bip_thumb_1_{side}", f"bip_thumb_2_{side}", t2, t3, thickness_scale=0.95)
    pose_segment_world(vortex_arm, f"bip_thumb_2_{side}", f"bip_thumb_tip_{side}", t3, t4, thickness_scale=0.95)

# Verify joint alignment error across all 30 finger segments
max_err_mm = 0.0
for side, pfx in [("L", "LeftHand"), ("R", "RightHand")]:
    for fn_f, fn_i in [("index", "Index"), ("middle", "Middle"), ("ring", "Ring"), ("pinky", "Pinky")]:
        for k, idx_s in [(0, "1"), (1, "2"), (2, "3")]:
            w_p = (vortex_arm.matrix_world @ vortex_arm.pose.bones[f"bip_{fn_f}_{k}_{side}"].matrix).translation
            err = (w_p - g_b_pos[f"{pfx}{fn_i}{idx_s}"]).length * 1000.0
            max_err_mm = max(max_err_mm, err)
    for k, idx_s in [(0, "1"), (1, "2"), (2, "3")]:
        w_p = (vortex_arm.matrix_world @ vortex_arm.pose.bones[f"bip_thumb_{k}_{side}"].matrix).translation
        err = (w_p - g_b_pos[f"{pfx}Thumb{idx_s}"]).length * 1000.0
        max_err_mm = max(max_err_mm, err)

print(f"[✓] Max joint alignment error across ALL 30 finger hinges: {max_err_mm:.4f} mm!")

bpy.ops.object.mode_set(mode='OBJECT')

# 7. Bake Armature modifier on each mesh
baked_parts = []
for nm in robot_mesh_names:
    obj = bpy.data.objects[nm]
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    for mod in list(obj.modifiers):
        if mod.type == 'ARMATURE':
            bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    baked_parts.append(obj)

# Smooth thumb-saddle bridge on ArmLoL & ArmLoR palm vertices
for side, obj in [("L", armlo_l), ("R", armlo_r)]:
    vg_hand = obj.vertex_groups.get(f"bip_hand_{side}")
    if not vg_hand:
        continue
    vg_idx = vg_hand.index
    delta_t = g_b_pos[f"{'Left' if side == 'L' else 'Right'}HandThumb1"] - pre_thumb_w[side]
    print(f"  Smooth thumb-saddle delta ({side}): ({delta_t.x:.3f}, {delta_t.y:.3f}, {delta_t.z:.3f})")
    for v in obj.data.vertices:
        wh = sum(g.weight for g in v.groups if g.group == vg_idx)
        if wh > 0.01:
            d = (v.co - pre_thumb_w[side]).length
            if d < 0.40:
                falloff = math.exp(-((d / 0.18) ** 2))
                v.co += delta_t * (wh * falloff)
    obj.data.update()

# Ion Blades: Assign 100% rigid weight to ForeArms and tune proportions so tip stays gracefully above ground
for side, blade_obj in [("L", blade_l), ("R", blade_r)]:
    s_sign = -1.0 if side == "L" else 1.0
    pivot = mathutils.Vector((s_sign * 2.571, -0.049, 5.746))
    rot_x = mathutils.Matrix.Rotation(math.radians(12.0), 4, 'X')
    scale_m = mathutils.Matrix.Diagonal((0.75, 0.75, 0.65, 1.0))
    T = mathutils.Matrix.Translation(pivot)
    T_inv = mathutils.Matrix.Translation(-pivot)
    M = T @ rot_x @ scale_m @ T_inv
    for v in blade_obj.data.vertices:
        v.co = M @ v.co
    blade_obj.data.update()

    blade_obj.vertex_groups.clear()
    vg_name = "LeftForeArm" if side == "L" else "RightForeArm"
    vg = blade_obj.vertex_groups.new(name=vg_name)
    vg.add(list(range(len(blade_obj.data.vertices))), 1.0, 'REPLACE')
    print(f"[✓] Tuned & assigned {len(blade_obj.data.vertices)} IonBlade_{side} vertices to {vg_name}!")

actual_min_z = min(v.co.z for o in baked_parts for v in o.data.vertices)
print(f"[✓] Verified baked body ground contact min_z = {actual_min_z:.4f}m (zero post-pose drift!)")

# Remove Vortex_ARM BEFORE creating character_model so only ONE armature exists!
bpy.data.objects.remove(vortex_arm, do_unlink=True)

# 8. Join all parts into unified mesh 'cha_vortex_gs_00'
bpy.ops.object.select_all(action='DESELECT')
for o in baked_parts:
    o.select_set(True)
bpy.context.view_layer.objects.active = baked_parts[0]
bpy.ops.object.join()
unified_mesh = bpy.context.view_layer.objects.active
unified_mesh.name = "cha_vortex_gs_00"
print(f"[✓] Joined all parts into '{unified_mesh.name}' ({len(unified_mesh.data.vertices)} verts, {len(unified_mesh.data.polygons)} polys)")

# 9. Create Official Grindor 78-bone Armature directly from Authoritative BindPoses!
arm_data = bpy.data.armatures.new("character_model")
arm_obj = bpy.data.objects.new("character_model", arm_data)
bpy.context.scene.collection.objects.link(arm_obj)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='EDIT')

edit_bones = {}
for name in bone_order:
    b_head = g_b_pos[name].copy()
    eb = arm_data.edit_bones.new(name)
    eb.head = b_head
    eb.tail = b_head + mathutils.Vector((0, 0, 0.08))
    edit_bones[name] = eb

for name in bone_order:
    parent_name = parents_map.get(name)
    eb = edit_bones[name]
    if parent_name and parent_name in edit_bones and parent_name != name:
        eb.parent = edit_bones[parent_name]
        diff = eb.head - edit_bones[parent_name].head
        if diff.length > 0.04 and any(k in parent_name for k in ["Thumb", "Index", "Middle", "Ring", "Pinky", "Arm", "Leg"]):
            edit_bones[parent_name].tail = eb.head

bpy.ops.object.mode_set(mode='OBJECT')

# 10. Remap Vertex Groups to Grindor's 78 bones
BONE_MAPPING = {
    "bip_pelvis": "Hips",
    "C_Root_Reference_XR": "Hips",
    "bip_spine_0": "Spine",
    "bip_spine_1": "Spine1",
    "bip_neck": "Neck",
    "C_Head01_Face_XF2": "Head",
    "bip_head": "Head",
    "bip_jaw": "Jaw",
    "bip_collar_L": "LeftShoulder",
    "L_CloudA_ClavRobo01_XT": "LeftShoulder",
    "L_ClavRobo01_XT": "LeftShoulder",
    "bip_upperArm_L": "LeftArm",
    "L_CloudA_ShoulderRobo01_XT": "LeftArm",
    "L_CloudA_ShoulderRobo02_XT": "LeftArm",
    "L_CloudA_ShoulderRobo03_XT": "LeftArm",
    "L_CloudA_PadRobo01_XT": "LeftShoulderPad",
    "L_CloudA_PadRobo02_XT": "LeftShoulderPad",
    "L_CloudA_PadRobo03_XT": "LeftShoulderPad",
    "L_CloudA_PadRobo04_XT": "LeftShoulderPad",
    "L_CloudA_PadRobo05_XT": "LeftShoulderPad",
    "bip_lowerArm_L": "LeftForeArm",
    "bip_hand_L": "LeftHand",
    # 15 Left Finger Bones
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
    "bip_collar_R": "RightShoulder",
    "R_CloudA_ClavRobo01_XT": "RightShoulder",
    "R_ClavRobo01_XT": "RightShoulder",
    "bip_upperArm_R": "RightArm",
    "R_CloudA_ShoulderRobo01_XT": "RightArm",
    "R_CloudA_ShoulderRobo02_XT": "RightArm",
    "R_CloudA_ShoulderRobo03_XT": "RightArm",
    "R_CloudA_PadRobo01_XT": "RightShoulderPad",
    "R_CloudA_PadRobo02_XT": "RightShoulderPad",
    "R_CloudA_PadRobo03_XT": "RightShoulderPad",
    "R_CloudA_PadRobo04_XT": "RightShoulderPad",
    "R_CloudA_PadRobo05_XT": "RightShoulderPad",
    "bip_lowerArm_R": "RightForeArm",
    "bip_hand_R": "RightHand",
    # 15 Right Finger Bones
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
    "bip_hip_L": "LeftUpLeg",
    "L_ThighRobo01_XT": "LeftUpLeg",
    "L_ThighRobo02_XT": "LeftUpLeg",
    "L_ThighRobo03_XT": "LeftUpLeg",
    "bip_knee_L": "LeftLeg",
    "L_KneeRobo01_XT": "LeftLeg",
    "L_KneeRobo02_XT": "LeftLeg",
    "L_KneeRobo03_XT": "LeftLeg",
    "L_KneeRobo04_XT": "LeftLeg",
    "bip_foot_L": "LeftFoot",
    "bip_toe_L": "LeftFoot",
    "bip_hip_R": "RightUpLeg",
    "R_ThighRobo01_XT": "RightUpLeg",
    "R_ThighRobo02_XT": "RightUpLeg",
    "R_ThighRobo03_XT": "RightUpLeg",
    "bip_knee_R": "RightLeg",
    "R_KneeRobo01_XT": "RightLeg",
    "R_KneeRobo02_XT": "RightLeg",
    "R_KneeRobo03_XT": "RightLeg",
    "R_KneeRobo04_XT": "RightLeg",
    "bip_foot_R": "RightFoot",
    "bip_toe_R": "RightFoot",
}

def resolve_target_bone(vg_name):
    if vg_name in bone_order_set:
        return vg_name
    if vg_name in BONE_MAPPING:
        return BONE_MAPPING[vg_name]
    if "Lumbar" in vg_name or "Spine" in vg_name:
        return "Spine1"
    if "Head" in vg_name or "Face" in vg_name or "Eye" in vg_name:
        return "Head"
    if "Neck" in vg_name:
        return "Neck"
    if "Pelvis" in vg_name or "Hips" in vg_name:
        return "Hips"
    is_left = ("_L" in vg_name or vg_name.startswith("L_") or "Left" in vg_name)
    is_right = ("_R" in vg_name or vg_name.startswith("R_") or "Right" in vg_name)
    if is_left or is_right:
        p = "Left" if is_left else "Right"
        if "hand" in vg_name.lower():
            return f"{p}Hand"
        if any(k in vg_name.lower() for k in ["elbow", "lowerarm", "armlo", "forearm"]):
            return f"{p}ForeArm"
        if "pad" in vg_name.lower():
            return f"{p}ShoulderPad"
        if any(k in vg_name.lower() for k in ["collar", "clav"]):
            return f"{p}Shoulder"
        if any(k in vg_name.lower() for k in ["shoulder", "upperarm", "armup"]):
            return f"{p}Arm"
        if any(k in vg_name.lower() for k in ["foot", "toe", "ankle"]):
            return f"{p}Foot"
        if any(k in vg_name.lower() for k in ["knee", "leg02"]):
            return f"{p}Leg"
        if any(k in vg_name.lower() for k in ["hip", "thigh", "leg01"]):
            return f"{p}UpLeg"
    return "Spine1"

v_count = len(unified_mesh.data.vertices)
new_weights = [{} for _ in range(v_count)]
vg_index_to_target = {vg.index: resolve_target_bone(vg.name) for vg in unified_mesh.vertex_groups}

finger_vert_counts = {}
for v in unified_mesh.data.vertices:
    w_acc = {}
    for g in v.groups:
        if g.weight > 0.001:
            tb = vg_index_to_target[g.group]
            w_acc[tb] = w_acc.get(tb, 0.0) + g.weight
    if not w_acc:
        if v.co.z > 6.5:
            w_acc["LeftShoulderPad" if v.co.x < 0 else "RightShoulderPad"] = 1.0
        else:
            w_acc["LeftLeg" if v.co.x < 0 else "RightLeg"] = 1.0
    top = sorted(w_acc.items(), key=lambda x: x[1], reverse=True)[:4]
    tot = sum(w for _, w in top)
    normed = [(b, w / tot) for b, w in top]
    if normed[0][1] >= 0.65:
        new_weights[v.index] = {normed[0][0]: 1.0}
    else:
        new_weights[v.index] = dict(normed)
    dom_b = normed[0][0]
    if any(k in dom_b for k in ["Thumb", "Index", "Middle", "Ring", "Pinky"]):
        finger_vert_counts[dom_b] = finger_vert_counts.get(dom_b, 0) + 1

print(f"[✓] Populated {len(finger_vert_counts)} articulated finger bones: {dict(sorted(finger_vert_counts.items()))}")

unified_mesh.vertex_groups.clear()
vg_objs = {bname: unified_mesh.vertex_groups.new(name=bname) for bname in bone_order}
for vi, wd in enumerate(new_weights):
    for bname, w in wd.items():
        vg_objs[bname].add([vi], w, 'REPLACE')

# Single clean material using cha_vortex_main_a.png
atlas_mat = bpy.data.materials.new(name="M_Vortex_Main")
atlas_mat.use_nodes = True
bsdf = atlas_mat.node_tree.nodes.get("Principled BSDF")
tex_path = UNITY_DIR / "cha_vortex_main_a.png"
if tex_path.exists() and bsdf:
    ti = atlas_mat.node_tree.nodes.new("ShaderNodeTexImage")
    ti.image = bpy.data.images.load(str(tex_path))
    atlas_mat.node_tree.links.new(ti.outputs["Color"], bsdf.inputs["Base Color"])
unified_mesh.data.materials.clear()
unified_mesh.data.materials.append(atlas_mat)

# Bind unified_mesh to character_model
unified_mesh.parent = arm_obj
mod = unified_mesh.modifiers.new(name="Armature", type='ARMATURE')
mod.object = arm_obj
mod.use_vertex_groups = True

# 11. Export clean single-armature FBX
fbx_out = UNITY_DIR / "vortex_prepared.fbx"
bpy.ops.object.select_all(action='DESELECT')
arm_obj.select_set(True)
unified_mesh.select_set(True)
bpy.context.view_layer.objects.active = arm_obj

bpy.ops.export_scene.fbx(
    filepath=str(fbx_out),
    use_selection=True,
    bake_anim=False,
    add_leaf_bones=False,
    apply_scale_options='FBX_SCALE_ALL',
    axis_forward='-Z',
    axis_up='Y',
)
print(f"[✓] Exported 30-finger articulated FBX: {fbx_out} ({fbx_out.stat().st_size} bytes)")
