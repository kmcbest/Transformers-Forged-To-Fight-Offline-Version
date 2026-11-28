import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy, bmesh, json, math
from mathutils import Vector, Matrix, Quaternion
from pathlib import Path

print("=== [DragStrip] Stage 2A Robot Alignment (Alliance FBX -> Mirage 59-Bone Rig) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
DS_DIR = ROOT / "3rd-party-models" / "DragStrip"
FBX_SRC = DS_DIR / "source" / "source" / "Dragstrip.fbx"
OUT_FBX_DIR = DS_DIR / "03_fbx_exports"
OUT_FBX_DIR.mkdir(parents=True, exist_ok=True)
UNITY_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "DragStrip"
UNITY_DIR.mkdir(parents=True, exist_ok=True)

MIRAGE_TRUTH = json.loads((DS_DIR / "mirage_00_bones.json").read_text(encoding="utf-8"))
MIRAGE_59_BONES = [b["name"] for b in MIRAGE_TRUTH["bones"]]
mirage_pos_map = {
    b["name"]: Vector((-float(b["unity_pos"][0]), -float(b["unity_pos"][2]), float(b["unity_pos"][1])))
    for b in MIRAGE_TRUTH["bones"]
}

# Exact 63-VG -> Mirage 59-bone map (physically verified!)
# Traps prevented:
#   1) Dummy_Knee_R002 (+X) -> LeftLeg; Dummy_Knee_L002 (-X) -> RightLeg!
#   2) Point L/R Clavicle (+1.91/-1.91) -> LeftArm/RightArm; Dummy_Shoulder_01_L/R001 (+1.22/-1.22) -> Left/RightShoulder!
#   3) Track B (Swoop pattern): Symmetrical combat fists pre-baked in Blender via Bip001 (Right thumb X=0 mirror),
#      then ALL Bone Finge_L_1..9 -> LeftHand and Bone Finge_R_1..9 -> RightHand so Mirage Thumb1 never splays outward!
VGROUP_MAP = {
    "Point Head": "Head",
    "Point Neck": "Neck",
    "Point Pelvis": "Hips",
    "Point Spine": "Spine",
    "Point Spine1": "Spine1",
    "Dummy_Back_01": "Spine1",
    "Dummy_Back_02_L002": "Spine1",
    "Dummy_Back_02_R02": "Spine1",
    "Dummy_Back_03_L001": "Spine1",
    "Dummy_Back_03_L002": "Spine1",  # -X back piece
    "Dummy_Back_04_L01": "Spine1",
    "Dummy_Back_04_R01": "Spine1",
    "Dummy_engine": "Spine1",
    "Dummy_Front_003": "Spine1",
    "Dummy_Object": "Spine1",

    # Left Leg
    "Point L Thigh": "LeftUpLeg",
    "Point L Calf": "LeftLeg",
    "Dummy_Calf_02_L002": "LeftLeg",
    "Dummy_Knee_R002": "LeftLeg",    # Swapped name! X=[+0.24,+1.13] -> Left!
    "Dummy_L_leg_tire": "LeftLeg",
    "Point L Foot": "LeftFoot",
    "Dummy_Foot_03_L002": "LeftFoot",
    "Dummy_Foot_02_L002": "LeftToeBase",

    # Right Leg
    "Point R Thigh": "RightUpLeg",
    "Point R Calf": "RightLeg",
    "Dummy_Calf_02_R002": "RightLeg",
    "Dummy_Knee_L002": "RightLeg",   # Swapped name! X=[-1.13,-0.24] -> Right!
    "Dummy_R_leg_tire001": "RightLeg",
    "Point R Foot": "RightFoot",
    "Dummy_Foot_03_R002": "RightFoot",
    "Dummy_Foot_02_R002": "RightToeBase",

    # Left Arm & Fingers (Track A: Open-pose aligned to Mirage m_BindPose -> Thumb/Index/Middle1..3, fused 2/8/9 locked uniformly to Middle1..3 to prevent tearing!)
    "Dummy_Shoulder_01_L001": "LeftShoulder",
    "Point L Clavicle": "LeftArm",
    "Dummy_Shoulder_L_Object": "LeftArm",
    "Dummy_L_Arm_tire01": "LeftArm",
    "Dummy_L_Arm_tire02": "LeftArm",
    "Point L Forearm": "LeftForeArm",
    "Point L Hand": "LeftHand",
    "Bone Finge_L_1": "LeftHandThumb1",
    "Bone Finge_L_4": "LeftHandThumb1",
    "Bone Finge_L_5": "LeftHandThumb1",
    "Bone Finge_L_3": "LeftHandIndex1",
    "Bone Finge_L_6": "LeftHandIndex2",
    "Bone Finge_L_7": "LeftHandIndex3",
    "Bone Finge_L_2": "LeftHandMiddle1",
    "Bone Finge_L_8": "LeftHandMiddle2",
    "Bone Finge_L_9": "LeftHandMiddle3",

    # Right Arm & Fingers (Track A: Open-pose aligned to Mirage m_BindPose -> Thumb/Index/Middle1..3)
    "Dummy_Shoulder_01_R001": "RightShoulder",
    "Point R Clavicle": "RightArm",
    "Dummy_Shoulder_R_Object": "RightArm",
    "Dummy_R_Arm_tire01": "RightArm",
    "Dummy_R_Arm_tire02": "RightArm",
    "Point R Forearm": "RightForeArm",
    "Point R Hand": "RightHand",
    "Bone Finge_R_1": "RightHandThumb1",
    "Bone Finge_R_4": "RightHandThumb1",
    "Bone Finge_R_5": "RightHandThumb1",
    "Bone Finge_R_3": "RightHandIndex1",
    "Bone Finge_R_6": "RightHandIndex2",
    "Bone Finge_R_7": "RightHandIndex3",
    "Bone Finge_R_2": "RightHandMiddle1",
    "Bone Finge_R_8": "RightHandMiddle2",
    "Bone Finge_R_9": "RightHandMiddle3",
}

MIRAGE_PARENT_MAP = {
    "Hips": None,
    "Spine": "Hips",
    "Spine1": "Spine",
    "Neck": "Spine1",
    "Head": "Neck",
    "LeftUpLeg": "Hips",
    "LeftLeg": "LeftUpLeg",
    "LeftFoot": "LeftLeg",
    "LeftToeBase": "LeftFoot",
    "LeftToe": "LeftToeBase",
    "RightUpLeg": "Hips",
    "RightLeg": "RightUpLeg",
    "RightFoot": "RightLeg",
    "RightToeBase": "RightFoot",
    "RightToe": "RightToeBase",
    "LeftShoulder": "Spine1",
    "LeftArm": "LeftShoulder",
    "LeftArmRoll": "LeftArm",
    "LeftForeArm": "LeftArmRoll",
    "LeftForeArmRoll": "LeftForeArm",
    "LeftHand": "LeftForeArmRoll",
    "LeftProp": "LeftHand",
    "RightShoulder": "Spine1",
    "RightArm": "RightShoulder",
    "RightArmRoll": "RightArm",
    "RightForeArm": "RightArmRoll",
    "RightForeArmRoll": "RightForeArm",
    "RightHand": "RightForeArmRoll",
    "RightProp": "RightHand",
}
for fn in ("Thumb", "Index", "Middle", "Ring", "Pinky"):
    MIRAGE_PARENT_MAP[f"LeftHand{fn}1"] = "LeftHand"
    MIRAGE_PARENT_MAP[f"LeftHand{fn}2"] = f"LeftHand{fn}1"
    MIRAGE_PARENT_MAP[f"LeftHand{fn}3"] = f"LeftHand{fn}2"
    MIRAGE_PARENT_MAP[f"RightHand{fn}1"] = "RightHand"
    MIRAGE_PARENT_MAP[f"RightHand{fn}2"] = f"RightHand{fn}1"
    MIRAGE_PARENT_MAP[f"RightHand{fn}3"] = f"RightHand{fn}2"


def wrap_polygon_uvs_clean(mesh_obj):
    """Shift any polygon with min U >= 0.99 left by -1.0 (zero seam tearing!), clamp cleanly to [0.0005, 0.9995]."""
    uvl = mesh_obj.data.uv_layers.active
    if not uvl:
        return 0
    uvd = uvl.data
    shifted = 0
    for p in mesh_obj.data.polygons:
        us = [uvd[li].uv.x for li in p.loop_indices]
        if min(us) >= 0.99:
            for li in p.loop_indices:
                uvd[li].uv.x -= 1.0
            shifted += 1
        for li in p.loop_indices:
            uvd[li].uv.x = min(0.9995, max(0.0005, uvd[li].uv.x))
            uvd[li].uv.y = min(0.9995, max(0.0005, uvd[li].uv.y))
    return shifted


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
    print("[*] Importing Dragstrip.fbx...")
    bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

    arm = bpy.data.objects.get("Bip001")
    mesh = bpy.data.objects.get("Dragstrip.001")
    sym_dc = bpy.data.objects.get("Symbol_DC")
    assert arm and mesh and sym_dc, "Missing Bip001, Dragstrip.001 or Symbol_DC!"

    # 0. Track A Open-Hand Pose Alignment via native Bip001 (match Mirage m_BindPose:
    #    - Thumbs lifted forward along -Y (horizontal) so Unity Thumb1 curls into fist AND relaxes open!
    #    - 4 fingers straightened slightly downward along -Z so open victory/idle hands spread cleanly!)
    arm.animation_data_clear()
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.pose.transforms_clear()

    mat_arm_to_mesh = mesh.matrix_world.inverted() @ arm.matrix_world
    rot_arm_to_mesh = mat_arm_to_mesh.to_3x3()

    # Straighten 4 fingers slightly from Dragstrip's pre-curved rest into vertical -Z open pose
    for bname, deg in [
        ("Bone Finge_L_3", -4), ("Bone Finge_L_6", -14), ("Bone Finge_L_7", -18),
        ("Bone Finge_L_2", -4), ("Bone Finge_L_8", -14), ("Bone Finge_L_9", -18),
    ]:
        pose_bone_mesh_axis_curl(arm, rot_arm_to_mesh, bname, Vector((0.0, 1.0, 0.0)), deg)

    for bname, deg in [
        ("Bone Finge_R_3", -4), ("Bone Finge_R_6", -14), ("Bone Finge_R_7", -18),
        ("Bone Finge_R_2", -4), ("Bone Finge_R_8", -14), ("Bone Finge_R_9", -18),
    ]:
        pose_bone_mesh_axis_curl(arm, rot_arm_to_mesh, bname, Vector((0.0, -1.0, 0.0)), deg)

    # Rotate Left thumb up/forward from (-0.48, -0.35, -0.80) into (-0.05, -1.00, 0.00) matching Mirage Thumb1..3
    ax_open_t0 = Vector((-0.80, 0.04, 0.46)).normalized()
    ax_open_t1 = Vector((-0.80, 0.04, 0.46)).normalized()
    pose_bone_mesh_axis_curl(arm, rot_arm_to_mesh, "Bone Finge_L_1", ax_open_t0, 68)
    pose_bone_mesh_axis_curl(arm, rot_arm_to_mesh, "Bone Finge_L_4", ax_open_t1, -12)
    pose_bone_mesh_axis_curl(arm, rot_arm_to_mesh, "Bone Finge_L_5", ax_open_t1, -12)

    # Exact X=0 mirror onto Right Thumb
    for rname, ax_l, deg in [
        ("Bone Finge_R_1", ax_open_t0, 68),
        ("Bone Finge_R_4", ax_open_t1, -12),
        ("Bone Finge_R_5", ax_open_t1, -12),
    ]:
        ax_r = Vector((-ax_l.x, ax_l.y, ax_l.z)).normalized()
        pose_bone_mesh_axis_curl(arm, rot_arm_to_mesh, rname, ax_r, -deg)

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

    # 1. Scale uniformly to Mirage 00 height (9.090m)
    raw_zs = [v.co.z for v in mesh.data.vertices]
    SCALE = 9.090 / (max(raw_zs) - min(raw_zs))
    print(f"[*] Uniform scale factor: {SCALE:.5f}")
    s_mat = Matrix.Scale(SCALE, 4)
    mesh.data.transform(s_mat)
    sym_dc.data.transform(s_mat)

    # 2. Ground at Z = 0.000m
    min_z = min(v.co.z for v in mesh.data.vertices)
    g_mat = Matrix.Translation(Vector((0.0, 0.0, -min_z)))
    mesh.data.transform(g_mat)
    sym_dc.data.transform(g_mat)
    mesh.data.update()
    sym_dc.data.update()

    # 2b. Subtle 2.0-deg outward arm flare around shoulder pivot (±1.45, 0, 7.80) so wrists match Mirage X=±2.03m!
    #     Note Symbol_DC sits on Left shoulder armor (+1.75..+2.12, Z=7.16..7.59), so rotate Symbol_DC with Left arm!
    for side, pivot_x, angle_deg in (("L", 1.45, -2.0), ("R", -1.45, 2.0)):
        arm_vgs = {
            mesh.vertex_groups[n].index
            for n in (
                f"Point {side} Clavicle", f"Dummy_Shoulder_{side}_Object",
                f"Dummy_{side}_Arm_tire01", f"Dummy_{side}_Arm_tire02",
                f"Point {side} Forearm", f"Point {side} Hand",
                *(f"Bone Finge_{side}_{k}" for k in range(1, 10)),
            )
            if n in mesh.vertex_groups
        }
        pivot = Vector((pivot_x, 0.0, 7.80))
        rot_y = Matrix.Rotation(math.radians(angle_deg), 4, 'Y')
        for v in mesh.data.vertices:
            if sum(g.weight for g in v.groups if g.group in arm_vgs) > 0.35:
                v.co = pivot + (rot_y @ (v.co - pivot))
        if side == "L":
            for v in sym_dc.data.vertices:
                v.co = pivot + (rot_y @ (v.co - pivot))

    # 2c. C^0-continuous piecewise-linear Z alignment mapping EXACT Alliance finger joint heads -> Mirage m_BindPose bone heads!
    #     (Previously mapped segment midpoints, leaving L_3 bottom/L_6 head 5-10cm above Index2 pivot so 90-deg curls opened a gap.)
    def map_finger_z(z: float) -> float:
        anchors = [
            (4.542, 4.542),  # Forearm cuff seam stays 100% locked
            (4.062, 3.923),  # Bone Finge_*_3/2 head -> Mirage Index1 / Middle1
            (3.874, 3.595),  # Bone Finge_*_6/8 head -> Mirage Index2 / Middle2
            (3.716, 3.334),  # Bone Finge_*_7/9 head -> Mirage Index3 / Middle3
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
                f"Point {side} Hand",
                *(f"Bone Finge_{side}_{k}" for k in ("2", "3", "6", "7", "8", "9")),
            )
            if n in mesh.vertex_groups
        }
        thumb_vgs = {mesh.vertex_groups[f"Bone Finge_{side}_{k}"].index for k in ("1", "4", "5") if f"Bone Finge_{side}_{k}" in mesh.vertex_groups}
        for v in mesh.data.vertices:
            wh = sum(g.weight for g in v.groups if g.group in hand_vgs)
            wt = sum(g.weight for g in v.groups if g.group in thumb_vgs)
            # Only apply Z-map cleanly below cuff on non-thumb vertices (smoothly fades at cuff & thumb base)
            w_eff = wh * max(0.0, 1.0 - wt)
            if w_eff > 0.05 and v.co.z < 4.542:
                v.co.z = v.co.z + (map_finger_z(v.co.z) - v.co.z) * min(1.0, w_eff)
    mesh.data.update()

    lh_vg = mesh.vertex_groups["Point L Hand"]
    rh_vg = mesh.vertex_groups["Point R Hand"]
    lh_x = sum(v.co.x for v in mesh.data.vertices if any(g.group == lh_vg.index and g.weight > 0.3 for g in v.groups)) / len([v for v in mesh.data.vertices if any(g.group == lh_vg.index and g.weight > 0.3 for g in v.groups)])
    rh_x = sum(v.co.x for v in mesh.data.vertices if any(g.group == rh_vg.index and g.weight > 0.3 for g in v.groups)) / len([v for v in mesh.data.vertices if any(g.group == rh_vg.index and g.weight > 0.3 for g in v.groups)])
    print(f"[*] Axis & Hand X check: LeftHand={lh_x:+.3f}, RightHand={rh_x:+.3f} (Mirage=±2.033m)")
    assert lh_x > 1.7 and rh_x < -1.7

    # 3. Clean U>1.0 wrapping + assign Symbol_DC (+0.015m -Y lift + free-island Decepticon UVs)
    shifted = wrap_polygon_uvs_clean(mesh)
    print(f"[*] Wrapped {shifted} mirrored-UV polygons cleanly into [0, 1]")

    sym_dc.data.transform(Matrix.Translation(Vector((0.0, -0.015, 0.0))))
    sym_dc.data.update()
    target_uv_name = mesh.data.uv_layers[0].name if mesh.data.uv_layers else "UV0"
    if not sym_dc.data.uv_layers:
        sym_dc.data.uv_layers.new(name=target_uv_name)
    else:
        sym_dc.data.uv_layers.active.name = target_uv_name
    uvl = sym_dc.data.uv_layers[target_uv_name].data
    for p in sym_dc.data.polygons:
        t_uv = (0.867188, 0.914062) if p.material_index == 0 else (0.929688, 0.914062)
        for li in p.loop_indices:
            uvl[li].uv = t_uv

    mesh.data.materials.clear()
    mat_main = bpy.data.materials.new(name="cha_dragstrip_main")
    mesh.data.materials.append(mat_main)
    sym_dc.data.materials.clear()
    sym_dc.data.materials.append(mat_main)

    # Pin Symbol_DC onto Point L Clavicle -> LeftArm (its true parent on Left shoulder!)
    sym_dc.vertex_groups.clear()
    sg = sym_dc.vertex_groups.new(name="Point L Clavicle")
    sg.add(list(range(len(sym_dc.data.vertices))), 1.0, 'REPLACE')

    bpy.ops.object.select_all(action='DESELECT')
    sym_dc.select_set(True)
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.join()
    mesh.name = "cha_dragstrip_robot"
    print(f"[✓] Joined Symbol_DC (on LeftArm shoulder). Total verts: {len(mesh.data.vertices)}")

    # 4. Identify pure core torso verts (Point Pelvis/Spine/Spine1) BEFORE remapping for smooth waist flex
    vg_dict = {vg.name: vg for vg in mesh.vertex_groups}
    torso_src_idxs = {vg_dict[n].index for n in ("Point Pelvis", "Point Spine", "Point Spine1") if n in vg_dict}
    torso_blend_verts = {
        v.index for v in mesh.data.vertices
        if sum(g.weight for g in v.groups if g.group in torso_src_idxs) > 0.75
    }

    target_vgs = {bn: mesh.vertex_groups.new(name=bn) for bn in MIRAGE_59_BONES}
    old_to_tgt = {vg_dict[old].index: target_vgs[tgt] for old, tgt in VGROUP_MAP.items() if old in vg_dict and tgt in target_vgs}

    for v in mesh.data.vertices:
        w_acc = {}
        for g in v.groups:
            if g.group in old_to_tgt:
                tvg = old_to_tgt[g.group]
                w_acc[tvg] = w_acc.get(tvg, 0.0) + g.weight
        for tvg, w in w_acc.items():
            tvg.add([v.index], w, 'REPLACE')

    for old_vg in [vg for vg in mesh.vertex_groups if vg.name not in MIRAGE_59_BONES]:
        mesh.vertex_groups.remove(old_vg)

    # 4b. Soft knuckle-seam weight blend on Index1/2/3 & Middle1/2/3 so rigid Alliance finger boxes stay flush across 0..100 deg curls
    half_band = 0.045
    j1_z, j2_z, j3_z = 3.923, 3.595, 3.334
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

    # Smooth torso waist blend across Z=[5.40..6.70] so Point Pelvis / Spine / Spine1 flex without shear!
    hips_vg = target_vgs["Hips"]
    spine_vg = target_vgs["Spine"]
    spine1_vg = target_vgs["Spine1"]
    smoothed = 0
    for vi in torso_blend_verts:
        v = mesh.data.vertices[vi]
        z = v.co.z
        if 5.40 < z < 6.70:
            for g in list(v.groups):
                mesh.vertex_groups[g.group].remove([vi])
            if z <= 6.00:
                t = (z - 5.40) / 0.60
                if 1.0 - t > 1e-4: hips_vg.add([vi], 1.0 - t, 'REPLACE')
                if t > 1e-4: spine_vg.add([vi], t, 'REPLACE')
            else:
                t = (z - 6.00) / 0.70
                if 1.0 - t > 1e-4: spine_vg.add([vi], 1.0 - t, 'REPLACE')
                if t > 1e-4: spine1_vg.add([vi], t, 'REPLACE')
            smoothed += 1

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
    print(f"[✓] Remapped 59 bones (Track A 30-bone open-aligned fingers) + smoothed {smoothed} waist verts (zero-weight fixed: {zero_cnt})")

    # 5. Build Mirage 59-Bone Armature
    arm_data = bpy.data.armatures.new("cha_mirage_gs_deluxe2016_00_arm")
    arm_obj = bpy.data.objects.new("cha_mirage_gs_deluxe2016_00_arm", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')

    edit_bones = {}
    for bn in MIRAGE_59_BONES:
        b = arm_data.edit_bones.new(bn)
        wp = mirage_pos_map[bn]
        b.head = wp
        b.tail = wp + Vector((0.0, 0.0, 0.25))
        edit_bones[bn] = b

    for bn, pname in MIRAGE_PARENT_MAP.items():
        if bn in edit_bones and pname in edit_bones:
            edit_bones[bn].parent = edit_bones[pname]
            pb = edit_bones[pname]
            if (edit_bones[bn].head - pb.head).length > 0.05:
                pb.tail = edit_bones[bn].head

    bpy.ops.object.mode_set(mode='OBJECT')
    mesh.parent = arm_obj
    mod = mesh.modifiers.new("Armature", 'ARMATURE')
    mod.object = arm_obj

    blend_dir = DS_DIR / "01_aligned_mesh"
    blend_dir.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_dir / "dragstrip_robot_aligned.blend"))

    for out_fbx in (OUT_FBX_DIR / "dragstrip_robot_prepared.fbx", UNITY_DIR / "dragstrip_robot_prepared.fbx"):
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
