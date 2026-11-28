import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy, bmesh, json, math
from mathutils import Vector, Matrix, Quaternion
from pathlib import Path

print("=== [WildRider] Stage 2A Robot Alignment (Alliance FBX -> Prowl 50-Bone Rig, Smooth Torso + Articulated Fists) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
WR_DIR = ROOT / "3rd-party-models" / "WildRider"
FBX_SRC = WR_DIR / "source" / "WildRider_pbr.fbx"
OUT_FBX_DIR = WR_DIR / "03_fbx_exports"
OUT_FBX_DIR.mkdir(parents=True, exist_ok=True)
UNITY_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "WildRider"
UNITY_DIR.mkdir(parents=True, exist_ok=True)

PROWL_TRUTH = json.loads((WR_DIR / "prowl_50_bones.json").read_text(encoding="utf-8"))
PROWL_50_BONES = [b["name"] for b in PROWL_TRUTH["bones"]]
prowl_pos_map = {
    b["name"]: Vector((-float(b["unity_pos"][0]), -float(b["unity_pos"][2]), float(b["unity_pos"][1])))
    for b in PROWL_TRUTH["bones"]
}

# Exact base VG -> Prowl 50-bone map (fingers & torso refined cleanly after remap)
VGROUP_MAP = {
    "Bone_Head": "Head",
    "Bone_Pelvis": "Hips",
    "Bone_Spine": "Spine",
    "Bone_Spine01": "Spine1",
    "Car Bumper": "Spine1",
    "Car Up": "Spine1",
    "Engine": "Spine1",

    # Left Leg
    "Bone_L_Thigh": "LeftUpLeg",
    "Bone_L_Calf": "LeftLeg",
    "Knee_L": "LeftLeg",
    "Tire_B_R": "LeftLeg",     # Verified physical X = +1.539 (Left side!)
    "Foot_L": "LeftLeg",
    "Toe_01_L": "LeftToeBase",

    # Right Leg
    "Bone_R_Thigh": "RightUpLeg",
    "Bone_R_Calf": "RightLeg",
    "Knee_R": "RightLeg",
    "Tire_B_L": "RightLeg",    # Verified physical X = -1.557 (Right side!)
    "Foot_R": "RightLeg",
    "Toe_01_R": "RightToeBase",

    # Left Arm & Articulated Fingers (Track A: Open-pose aligned to Prowl m_BindPose -> Thumb1, Index1/2/3, Middle1/2/3)
    "Bone_L_UpperArm": "LeftArm",
    "Tire_F_L": "LeftArm",
    "Bone_L_Forearm": "LeftForeArm",
    "Door_L": "LeftForeArm",
    "Bone_L_Hand": "LeftHand",
    "Bone_L_Finger0": "LeftHandThumb1",
    "Bone_L_Finger01": "LeftHandThumb2",
    "Bone_L_Finger02": "LeftHandThumb3",
    "Bone_L_Finger1": "LeftHandIndex1",
    "Bone_L_Finger11": "LeftHandIndex2",
    "Bone_L_Finger12": "LeftHandIndex3",
    "Bone_L_Finger2": "LeftHandMiddle1",
    "Bone_L_Finger21": "LeftHandMiddle2",
    "Bone_L_Finger22": "LeftHandMiddle3",

    # Right Arm & Articulated Fingers (Track A)
    "Bone_R_UpperArm": "RightArm",
    "Tire_F_R": "RightArm",
    "Bone_R_Forearm": "RightForeArm",
    "Door_R": "RightForeArm",
    "Bone_R_Hand": "RightHand",
    "Bone_R_Finger0": "RightHandThumb1",
    "Bone_R_Finger01": "RightHandThumb2",
    "Bone_R_Finger02": "RightHandThumb3",
    "Bone_R_Finger1": "RightHandIndex1",
    "Bone_R_Finger11": "RightHandIndex2",
    "Bone_R_Finger12": "RightHandIndex3",
    "Bone_R_Finger2": "RightHandMiddle1",
    "Bone_R_Finger21": "RightHandMiddle2",
    "Bone_R_Finger22": "RightHandMiddle3",
}

PROWL_PARENT_MAP = {
    "Hips": None,
    "Spine": "Hips",
    "Spine1": "Spine",
    "Head": "Spine1",
    "LeftUpLeg": "Hips",
    "LeftLeg": "LeftUpLeg",
    "LeftToeBase": "LeftLeg",
    "RightUpLeg": "Hips",
    "RightLeg": "RightUpLeg",
    "RightToeBase": "RightLeg",
    "LeftShoulder": "Spine1",
    "LeftArm": "LeftShoulder",
    "LeftArmRoll": "LeftArm",
    "LeftForeArm": "LeftArmRoll",
    "LeftHand": "LeftForeArm",
    "RightShoulder": "Spine1",
    "RightArm": "RightShoulder",
    "RightArmRoll": "RightArm",
    "RightForeArm": "RightArmRoll",
    "RightHand": "RightForeArm",
}
for fn in ("Thumb", "Index", "Middle", "Ring", "Pinky"):
    PROWL_PARENT_MAP[f"LeftHand{fn}1"] = "LeftHand"
    PROWL_PARENT_MAP[f"LeftHand{fn}2"] = f"LeftHand{fn}1"
    PROWL_PARENT_MAP[f"LeftHand{fn}3"] = f"LeftHand{fn}2"
    PROWL_PARENT_MAP[f"RightHand{fn}1"] = "RightHand"
    PROWL_PARENT_MAP[f"RightHand{fn}2"] = f"RightHand{fn}1"
    PROWL_PARENT_MAP[f"RightHand{fn}3"] = f"RightHand{fn}2"


def pose_bone_mesh_axis_curl(arm, rot_arm_to_mesh, bname: str, mesh_axis: Vector, angle_deg: float):
    pb = arm.pose.bones.get(bname)
    if not pb:
        return
    bone_in_mesh = (rot_arm_to_mesh @ pb.bone.matrix_local.to_3x3()).normalized()
    local_axis = (bone_in_mesh.inverted() @ mesh_axis.normalized()).normalized()
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = Quaternion(local_axis, math.radians(angle_deg))


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    print("[*] Importing WildRider_pbr.fbx...")
    bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

    arm_src = bpy.data.objects.get("Bip001")
    mesh = bpy.data.objects.get("WildRider.001")
    sym_dc = bpy.data.objects.get("Symbol_DC")
    assert arm_src and mesh and sym_dc, "Missing Bip001, WildRider.001, or Symbol_DC!"

    # 0. Track A Open-Hand Pose Alignment via native Bip001 (X=0 mirrored thumbs along -Y, 4 fingers straightened along -Z)
    arm_src.animation_data_clear()
    bpy.context.view_layer.objects.active = arm_src
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.pose.transforms_clear()

    mat_arm_to_mesh = mesh.matrix_world.inverted() @ arm_src.matrix_world
    rot_arm_to_mesh = mat_arm_to_mesh.to_3x3()

    for bname, deg in [
        ("Bone_L_Finger1", -4), ("Bone_L_Finger11", -14), ("Bone_L_Finger12", -18),
        ("Bone_L_Finger2", -4), ("Bone_L_Finger21", -14), ("Bone_L_Finger22", -18),
    ]:
        pose_bone_mesh_axis_curl(arm_src, rot_arm_to_mesh, bname, Vector((0.0, 1.0, 0.0)), deg)

    for bname, deg in [
        ("Bone_R_Finger1", -4), ("Bone_R_Finger11", -14), ("Bone_R_Finger12", -18),
        ("Bone_R_Finger2", -4), ("Bone_R_Finger21", -14), ("Bone_R_Finger22", -18),
    ]:
        pose_bone_mesh_axis_curl(arm_src, rot_arm_to_mesh, bname, Vector((0.0, -1.0, 0.0)), deg)

    ax_t_open = Vector((-0.948, 0.047, 0.314)).normalized()
    pose_bone_mesh_axis_curl(arm_src, rot_arm_to_mesh, "Bone_L_Finger0", ax_t_open, 65.0)
    pose_bone_mesh_axis_curl(arm_src, rot_arm_to_mesh, "Bone_L_Finger01", ax_t_open, -10.0)
    pose_bone_mesh_axis_curl(arm_src, rot_arm_to_mesh, "Bone_L_Finger02", ax_t_open, -10.0)

    for rname, ax_l, deg in [
        ("Bone_R_Finger0", ax_t_open, 65.0),
        ("Bone_R_Finger01", ax_t_open, -10.0),
        ("Bone_R_Finger02", ax_t_open, -10.0),
    ]:
        ax_r = Vector((-ax_l.x, ax_l.y, ax_l.z)).normalized()
        pose_bone_mesh_axis_curl(arm_src, rot_arm_to_mesh, rname, ax_r, -deg)

    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.update()

    deps = bpy.context.evaluated_depsgraph_get()
    baked_data = bpy.data.meshes.new_from_object(mesh.evaluated_get(deps))
    for i, v in enumerate(mesh.data.vertices):
        v.co = baked_data.vertices[i].co
    mesh.data.update()
    bpy.data.meshes.remove(baked_data)

    for o in bpy.data.objects:
        if o.animation_data:
            o.animation_data_clear()

    mesh.modifiers.clear()
    keep = {mesh, sym_dc}
    for o in list(bpy.data.objects):
        if o not in keep:
            bpy.data.objects.remove(o, do_unlink=True)

    for o in keep:
        o.parent = None
        o.matrix_world = Matrix.Identity(4)

    # 1. Scale uniformly to Prowl 9.304m height
    raw_zs = [v.co.z for v in mesh.data.vertices]
    SCALE = 9.304 / (max(raw_zs) - min(raw_zs))
    print(f"[*] Uniform scale factor: {SCALE:.5f}")
    scale_mat = Matrix.Scale(SCALE, 4)
    mesh.data.transform(scale_mat)
    sym_dc.data.transform(scale_mat)

    # 2. Ground at Z = 0.000m
    min_z = min(v.co.z for v in mesh.data.vertices)
    ground_mat = Matrix.Translation(Vector((0.0, 0.0, -min_z)))
    mesh.data.transform(ground_mat)
    sym_dc.data.transform(ground_mat)
    mesh.data.update()
    sym_dc.data.update()

    # 2b. Subtle 4.5-deg outward arm A-pose flare around shoulder joints (+1.45/-1.45, 0, 7.85)
    #     Keeps shoulders tight in torso socket while placing wrists & knuckles right on Prowl's X=±2.05m pivots
    for side, pivot_x, angle_deg in (("L", 1.45, -4.5), ("R", -1.45, 4.5)):
        arm_vgs = {
            mesh.vertex_groups[n].index
            for n in (
                f"Bone_{side}_UpperArm", f"Tire_F_{side}", f"Bone_{side}_Forearm", f"Door_{side}",
                f"Bone_{side}_Hand",
                f"Bone_{side}_Finger0", f"Bone_{side}_Finger01", f"Bone_{side}_Finger02",
                f"Bone_{side}_Finger1", f"Bone_{side}_Finger11", f"Bone_{side}_Finger12",
                f"Bone_{side}_Finger2", f"Bone_{side}_Finger21", f"Bone_{side}_Finger22",
            )
            if n in mesh.vertex_groups
        }
        pivot = Vector((pivot_x, 0.0, 7.85))
        rot_y = Matrix.Rotation(math.radians(angle_deg), 4, 'Y')
        moved = 0
        for v in mesh.data.vertices:
            w_arm = sum(g.weight for g in v.groups if g.group in arm_vgs)
            if w_arm > 0.35:
                v.co = pivot + (rot_y @ (v.co - pivot))
                moved += 1
        print(f"[*] Flared {side} arm outward {angle_deg:+.1f} deg ({moved} verts) -> wrist aligns with Prowl X=±2.03m")

    # 2c. C^0-continuous piecewise-linear Z alignment mapping EXACT WildRider proximal finger heads -> Prowl m_BindPose!
    def map_finger_z(z: float) -> float:
        anchors = [
            (4.597, 4.597),  # Prowl LeftHand wrist cuff locked
            (4.078, 3.970),  # Bone_*_Finger1/2 head -> Prowl Index1/Middle1
            (3.903, 3.640),  # Bone_*_Finger11/21 head -> Prowl Index2/Middle2
            (3.758, 3.374),  # Bone_*_Finger12/22 head -> Prowl Index3/Middle3
        ]
        if z >= anchors[0][0]:
            return z
        for i in range(len(anchors) - 1):
            z_hi, t_hi = anchors[i]
            z_lo, t_lo = anchors[i + 1]
            if z >= z_lo:
                u = (z - z_lo) / (z_hi - z_lo)
                return t_lo + u * (t_hi - t_lo)
        return anchors[-1][1] + (z - anchors[-1][0])

    for side in ("L", "R"):
        hand_vgs = {
            mesh.vertex_groups[n].index
            for n in (
                f"Bone_{side}_Hand",
                *(f"Bone_{side}_Finger{k}" for k in ("1", "11", "12", "2", "21", "22")),
            )
            if n in mesh.vertex_groups
        }
        thumb_vgs = {mesh.vertex_groups[f"Bone_{side}_Finger{k}"].index for k in ("0", "01", "02") if f"Bone_{side}_Finger{k}" in mesh.vertex_groups}
        for v in mesh.data.vertices:
            wh = sum(g.weight for g in v.groups if g.group in hand_vgs)
            wt = sum(g.weight for g in v.groups if g.group in thumb_vgs)
            w_eff = wh * max(0.0, 1.0 - wt)
            if w_eff > 0.05 and v.co.z < 4.597:
                v.co.z = v.co.z + (map_finger_z(v.co.z) - v.co.z) * min(1.0, w_eff)

    # 2d. C^0-continuous piecewise-linear Y alignment mapping WildRider Thumb -> Prowl Thumb1 (-0.311) -> Thumb2 (-0.656 -> -0.76 tip)
    #     Keeps base socket (y >= -0.150) welded inside Bone_*_Hand while extending thumb forward proportionally in -Y_b so curls wrap OUTSIDE the palm cleanly!
    def map_thumb_y(y: float) -> float:
        anchors = [
            (-0.150, -0.150),
            (-0.250, -0.320),
            (-0.390, -0.570),
            (-0.509, -0.760),
        ]
        if y >= anchors[0][0]:
            return y
        for i in range(len(anchors) - 1):
            y_hi, t_hi = anchors[i]
            y_lo, t_lo = anchors[i + 1]
            if y >= y_lo:
                u = (y - y_lo) / (y_hi - y_lo)
                return t_lo + u * (t_hi - t_lo)
        return anchors[-1][1] + (y - anchors[-1][0]) * 1.5

    for side, side_sign in (("L", 1.0), ("R", -1.0)):
        thumb_vgs = {mesh.vertex_groups[f"Bone_{side}_Finger{k}"].index for k in ("0", "01", "02") if f"Bone_{side}_Finger{k}" in mesh.vertex_groups}
        hand_vg = mesh.vertex_groups.get(f"Bone_{side}_Hand")
        hand_idx = hand_vg.index if hand_vg else -1
        for v in mesh.data.vertices:
            wt = sum(g.weight for g in v.groups if g.group in thumb_vgs)
            wh = sum(g.weight for g in v.groups if g.group == hand_idx)
            w_eff = wt if wt > 0.05 else 0.0
            if w_eff > 0.05 and v.co.y < -0.150:
                u_tip = min(1.0, (-0.150 - v.co.y) / (-0.150 - (-0.509)))
                blend = min(1.0, wt / max(1e-4, wt + wh))
                new_y = map_thumb_y(v.co.y)
                v.co.y = v.co.y + (new_y - v.co.y) * blend
                v.co.x += side_sign * 0.06 * u_tip * blend
                v.co.z += 0.05 * u_tip * blend

    mesh.data.update()

    lh_vg = mesh.vertex_groups.get("Bone_L_Hand")
    rh_vg = mesh.vertex_groups.get("Bone_R_Hand")
    lh_x = sum(v.co.x for v in mesh.data.vertices if any(g.group == lh_vg.index and g.weight > 0.3 for g in v.groups)) / len([v for v in mesh.data.vertices if any(g.group == lh_vg.index and g.weight > 0.3 for g in v.groups)])
    rh_x = sum(v.co.x for v in mesh.data.vertices if any(g.group == rh_vg.index and g.weight > 0.3 for g in v.groups)) / len([v for v in mesh.data.vertices if any(g.group == rh_vg.index and g.weight > 0.3 for g in v.groups)])
    print(f"[*] Axis & Arm Check: LeftHand mean X={lh_x:+.3f} (+X), RightHand mean X={rh_x:+.3f} (-X)")
    assert lh_x > 1.8 and rh_x < -1.8, f"Axis mismatch: LH={lh_x}, RH={rh_x}"

    # 3. Prepare Symbol_DC (+0.015m -Y lift + clean purple/charcoal UV palette)
    sym_dc.data.transform(Matrix.Translation(Vector((0.0, -0.015, 0.0))))
    sym_dc.data.update()
    target_uv_name = mesh.data.uv_layers[0].name if mesh.data.uv_layers else "UV0"
    if not sym_dc.data.uv_layers:
        sym_dc.data.uv_layers.new(name=target_uv_name)
    else:
        sym_dc.data.uv_layers.active.name = target_uv_name
    uvl = sym_dc.data.uv_layers[target_uv_name].data
    for p in sym_dc.data.polygons:
        target_uv = (0.296875, 0.9375) if p.material_index == 0 else (0.34375, 0.9375)
        for li in p.loop_indices:
            uvl[li].uv = target_uv

    mesh.data.materials.clear()
    mat_main = bpy.data.materials.new(name="cha_wildrider_main")
    mesh.data.materials.append(mat_main)
    sym_dc.data.materials.clear()
    sym_dc.data.materials.append(mat_main)

    sym_dc.vertex_groups.clear()
    sg = sym_dc.vertex_groups.new(name="Bone_Spine01")
    sg.add(list(range(len(sym_dc.data.vertices))), 1.0, 'REPLACE')

    # Join Symbol_DC into WildRider.001
    bpy.ops.object.select_all(action='DESELECT')
    sym_dc.select_set(True)
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.join()
    mesh.name = "cha_wildrider_robot"
    print(f"[✓] Joined Symbol_DC. Total verts: {len(mesh.data.vertices)}")

    # 4. Identify pure torso vertices (Bone_Pelvis / Bone_Spine / Bone_Spine01) BEFORE remapping so we can apply
    #    a smooth vertical Hips <-> Spine <-> Spine1 waist gradient that eliminates the frontend chest/abs shear!
    vg_dict = {vg.name: vg for vg in mesh.vertex_groups}
    torso_src_idxs = {vg_dict[n].index for n in ("Bone_Pelvis", "Bone_Spine", "Bone_Spine01") if n in vg_dict}
    torso_blend_verts = set()
    for v in mesh.data.vertices:
        w_t = sum(g.weight for g in v.groups if g.group in torso_src_idxs)
        if w_t > 0.75:
            torso_blend_verts.add(v.index)

    target_vgs = {bn: mesh.vertex_groups.new(name=bn) for bn in PROWL_50_BONES}
    old_to_tgt = {vg_dict[old].index: target_vgs[tgt] for old, tgt in VGROUP_MAP.items() if old in vg_dict and tgt in target_vgs}

    for v in mesh.data.vertices:
        w_acc = {}
        for g in v.groups:
            if g.group in old_to_tgt:
                tvg = old_to_tgt[g.group]
                w_acc[tvg] = w_acc.get(tvg, 0.0) + g.weight
        for tvg, w in w_acc.items():
            tvg.add([v.index], w, 'REPLACE')

    for old_vg in [vg for vg in mesh.vertex_groups if vg.name not in PROWL_50_BONES]:
        mesh.vertex_groups.remove(old_vg)

    # 4b. Soft knuckle-seam weight blend on Index1/2/3 & Middle1/2/3 so rigid finger segments stay flush across 0..100 deg curls
    half_band = 0.045
    j1_z, j2_z, j3_z = 3.970, 3.640, 3.374
    knuckle_blended = 0
    for side_prefix in ("LeftHand", "RightHand"):
        hand_vg = target_vgs[side_prefix]
        for chain in ("Index", "Middle"):
            vg1 = target_vgs[f"{side_prefix}{chain}1"]
            vg2 = target_vgs[f"{side_prefix}{chain}2"]
            vg3 = target_vgs[f"{side_prefix}{chain}3"]
            chain_idxs = {vg1.index, vg2.index, vg3.index}
            for v in mesh.data.vertices:
                w_chain = sum(g.weight for g in v.groups if g.group in chain_idxs)
                if w_chain <= 0.5:
                    continue
                for idx in chain_idxs | {hand_vg.index}:
                    mesh.vertex_groups[idx].remove([v.index])
                z = v.co.z
                if z >= j1_z + half_band:
                    hand_vg.add([v.index], 1.0, 'REPLACE')
                elif z > j1_z - half_band:
                    u = (z - (j1_z - half_band)) / (2.0 * half_band)
                    hand_vg.add([v.index], u, 'REPLACE')
                    vg1.add([v.index], 1.0 - u, 'REPLACE')
                elif z >= j2_z + half_band:
                    vg1.add([v.index], 1.0, 'REPLACE')
                elif z > j2_z - half_band:
                    u = (z - (j2_z - half_band)) / (2.0 * half_band)
                    vg1.add([v.index], u, 'REPLACE')
                    vg2.add([v.index], 1.0 - u, 'REPLACE')
                elif z >= j3_z + half_band:
                    vg2.add([v.index], 1.0, 'REPLACE')
                elif z > j3_z - half_band:
                    u = (z - (j3_z - half_band)) / (2.0 * half_band)
                    vg2.add([v.index], u, 'REPLACE')
                    vg3.add([v.index], 1.0 - u, 'REPLACE')
                else:
                    vg3.add([v.index], 1.0, 'REPLACE')
                knuckle_blended += 1

        # Articulated Thumb1 (-0.311) -> Thumb2 (-0.656) soft Y-seam blend;
        # vertices behind Thumb1 (-0.311 + half_band) bind 100% to Hand so the socket never folds inward!
        t1_y, t2_y = -0.311, -0.656
        tvg1 = target_vgs[f"{side_prefix}Thumb1"]
        tvg2 = target_vgs[f"{side_prefix}Thumb2"]
        tvg3 = target_vgs[f"{side_prefix}Thumb3"]
        t_idxs = {tvg1.index, tvg2.index, tvg3.index}
        for v in mesh.data.vertices:
            w_th = sum(g.weight for g in v.groups if g.group in t_idxs)
            if w_th <= 0.5:
                continue
            for idx in t_idxs | {hand_vg.index}:
                mesh.vertex_groups[idx].remove([v.index])
            y = v.co.y
            if y >= t1_y + half_band:
                hand_vg.add([v.index], 1.0, 'REPLACE')
            elif y > t1_y - half_band:
                u = (y - (t1_y - half_band)) / (2.0 * half_band)
                hand_vg.add([v.index], u, 'REPLACE')
                tvg1.add([v.index], 1.0 - u, 'REPLACE')
            elif y >= t2_y + half_band:
                tvg1.add([v.index], 1.0, 'REPLACE')
            elif y > t2_y - half_band:
                u = (y - (t2_y - half_band)) / (2.0 * half_band)
                tvg1.add([v.index], u, 'REPLACE')
                tvg2.add([v.index], 1.0 - u, 'REPLACE')
            else:
                tvg2.add([v.index], 1.0, 'REPLACE')
            knuckle_blended += 1

    # Apply smooth torso vertical skinning across [5.65..6.25] (Hips->Spine) & [6.25..6.95] (Spine->Spine1)
    # so the rigid white chest plate & black ribbed abs flex together smoothly without diagonal step/shear!
    hips_vg = target_vgs["Hips"]
    spine_vg = target_vgs["Spine"]
    spine1_vg = target_vgs["Spine1"]
    smoothed_torso = 0
    for vi in torso_blend_verts:
        v = mesh.data.vertices[vi]
        z = v.co.z
        if 5.65 < z < 6.95:
            for g in list(v.groups):
                mesh.vertex_groups[g.group].remove([vi])
            if z <= 6.25:
                t = (z - 5.65) / (6.25 - 5.65)
                if 1.0 - t > 1e-4: hips_vg.add([vi], 1.0 - t, 'REPLACE')
                if t > 1e-4: spine_vg.add([vi], t, 'REPLACE')
            else:
                t = (z - 6.25) / (6.95 - 6.25)
                if 1.0 - t > 1e-4: spine_vg.add([vi], 1.0 - t, 'REPLACE')
                if t > 1e-4: spine1_vg.add([vi], t, 'REPLACE')
            smoothed_torso += 1

    # Rigid clamp ONLY for non-torso / non-finger limb joints? Actually preserve natural multi-bone finger & torso blends,
    # only normalize all vertex weights cleanly so sum(w) == 1.0!
    zero_cnt = 0
    for v in mesh.data.vertices:
        gs = list(v.groups)
        tot = sum(g.weight for g in gs)
        if tot < 1e-4:
            hips_vg.add([v.index], 1.0, 'REPLACE')
            zero_cnt += 1
        elif abs(tot - 1.0) > 1e-4:
            for g in gs:
                mesh.vertex_groups[g.group].add([v.index], g.weight / tot, 'REPLACE')
    print(f"[✓] Remapped 50 bones (Track A articulated open-aligned fingers + {knuckle_blended} knuckle verts) + smoothed {smoothed_torso} waist/lower-chest verts (zero-weight fixed: {zero_cnt})")

    # 5. Build Prowl 50-Bone Armature
    arm_data = bpy.data.armatures.new("cha_prowl_gs_deluxe2016_00_arm")
    arm_obj = bpy.data.objects.new("cha_prowl_gs_deluxe2016_00_arm", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')

    edit_bones = {}
    for bn in PROWL_50_BONES:
        b = arm_data.edit_bones.new(bn)
        wp = prowl_pos_map[bn]
        b.head = wp
        b.tail = wp + Vector((0.0, 0.0, 0.25))
        edit_bones[bn] = b

    for bn, pname in PROWL_PARENT_MAP.items():
        if bn in edit_bones and pname in edit_bones:
            edit_bones[bn].parent = edit_bones[pname]
            pb = edit_bones[pname]
            if (edit_bones[bn].head - pb.head).length > 0.05:
                pb.tail = edit_bones[bn].head

    bpy.ops.object.mode_set(mode='OBJECT')
    mesh.parent = arm_obj
    mod = mesh.modifiers.new("Armature", 'ARMATURE')
    mod.object = arm_obj

    blend_dir = WR_DIR / "01_aligned_mesh"
    blend_dir.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_dir / "wildrider_robot_aligned.blend"))

    for out_fbx in (OUT_FBX_DIR / "wildrider_robot_prepared.fbx", UNITY_DIR / "wildrider_robot_prepared.fbx"):
        bpy.ops.object.select_all(action='DESELECT')
        arm_obj.select_set(True)
        mesh.select_set(True)
        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.export_scene.fbx(
            filepath=str(out_fbx),
            use_selection=True,
            use_active_collection=False,
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
            axis_forward='-Z',
            axis_up='Y',
            armature_nodetype='NULL',
            bake_anim=False,
        )
        print(f"[✓] Exported {out_fbx} ({out_fbx.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
