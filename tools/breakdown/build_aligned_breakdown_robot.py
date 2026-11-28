import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy, json, math
from mathutils import Vector, Matrix, Quaternion
from pathlib import Path

print("=== [Breakdown] Stage 2A Robot Alignment (Alliance FBX -> Sideswipe 80-Bone Rig, Track A Hands) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
BD_DIR = ROOT / "3rd-party-models" / "Breakdown"
FBX_SRC = BD_DIR / "source" / "source" / "Breakdown.fbx"
OUT_FBX_DIR = BD_DIR / "03_fbx_exports"
OUT_FBX_DIR.mkdir(parents=True, exist_ok=True)
UNITY_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Breakdown"
UNITY_DIR.mkdir(parents=True, exist_ok=True)

SIDESWIPE_TRUTH = json.loads((BD_DIR / "sideswipe_00_bones.json").read_text(encoding="utf-8"))
SIDESWIPE_80_BONES = [b["name"] for b in SIDESWIPE_TRUTH["bones"]]
ss_pos_map = {
    b["name"]: Vector((-float(b["unity_pos"][0]), -float(b["unity_pos"][2]), float(b["unity_pos"][1])))
    for b in SIDESWIPE_TRUTH["bones"]
}
ss_parent_map = {}
for b in SIDESWIPE_TRUTH["bones"]:
    parts = b["path"].split("/")
    pname = parts[-2] if len(parts) >= 2 else None
    ss_parent_map[b["name"]] = pname if pname in ss_pos_map else None

# Exact 58-VG -> Sideswipe 80-bone map (physically verified from rest-pose VG centroids!)
VGROUP_MAP = {
    "Bone Head": "Head",
    "Bone Neck": "Neck",
    "Bip001 Pelvis": "Hips",
    "Bone Spine": "Spine",
    "Bone Spine1": "Spine1",
    "Bone Chest": "Spine1",
    "Bone Back": "Spine1",
    "Bone Back001": "Spine1",

    # Left Leg
    "Bone L Thigh": "LeftUpLeg",
    "Bone L Calf": "LeftLeg",
    "Bone Calf_02_L": "LeftLeg",
    "Bone Calf_03_L": "LeftLeg",
    "Bone Calf_04_L": "LeftLeg",
    "Bone Calf_05_L": "LeftLeg",
    "Bone Tire_02_L": "LeftLeg",
    "Bone L Foot": "LeftFoot",
    "Bone L Toe0": "LeftToeBase",

    # Right Leg
    "Bone R Thigh": "RightUpLeg",
    "Bone R Calf": "RightLeg",
    "Bone Calf_02_R": "RightLeg",
    "Bone Calf_03_R": "RightLeg",
    "Bone Calf_04_R": "RightLeg",
    "Bone Calf_05_R": "RightLeg",
    "Bone Tire_02_R": "RightLeg",
    "Bone R Foot": "RightFoot",
    "Bone R Toe0": "RightToeBase",

    # Left Arm & Fingers (Track A: Open-pose aligned -> Thumb1, Index1/2/3, Middle1/2/3)
    "Bone L Clavicle": "LeftShoulder",
    "Bone L UpperArm": "LeftArm",
    "Bone Shoulder_02_L002": "LeftArm",
    "Bone Tire_01_L001": "LeftArm",
    "Bone L Forearm": "LeftForeArm",
    "Bone Arm_02_L": "LeftForeArm",
    "Bone L Hand": "LeftHand",
    "Bone L Finger0": "LeftHandThumb1",
    "Bone L Finger01": "LeftHandThumb1",
    "Bone L Finger02": "LeftHandThumb1",
    "Bone L Finger1": "LeftHandIndex1",
    "Bone L Finger11": "LeftHandIndex2",
    "Bone L Finger12": "LeftHandIndex3",
    "Bone L Finger2": "LeftHandMiddle1",
    "Bone L Finger21": "LeftHandMiddle2",
    "Bone L Finger22": "LeftHandMiddle3",

    # Right Arm & Fingers (Track A)
    "Bone R Clavicle": "RightShoulder",
    "Bone R UpperArm": "RightArm",
    "Bone Shoulder_02_R002": "RightArm",
    "Bone Tire_01_R001": "RightArm",
    "Bone R Forearm": "RightForeArm",
    "Bone Arm_02_R": "RightForeArm",
    "Bone R Hand": "RightHand",
    "Bone R Finger0": "RightHandThumb1",
    "Bone R Finger01": "RightHandThumb1",
    "Bone R Finger02": "RightHandThumb1",
    "Bone R Finger1": "RightHandIndex1",
    "Bone R Finger11": "RightHandIndex2",
    "Bone R Finger12": "RightHandIndex3",
    "Bone R Finger2": "RightHandMiddle1",
    "Bone R Finger21": "RightHandMiddle2",
    "Bone R Finger22": "RightHandMiddle3",
}


def wrap_polygon_uvs_clean(mesh_obj):
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
    print("[*] Importing Breakdown.fbx...")
    bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

    arm = bpy.data.objects.get("Breakdown")
    mesh = bpy.data.objects.get("Breakdown.001")
    sym_dc = bpy.data.objects.get("Symbol_DC01")
    assert arm and mesh and sym_dc, "Missing Breakdown, Breakdown.001 or Symbol_DC01!"

    # 0. Track A Open-Hand Pose Alignment via native Bip001
    arm.animation_data_clear()
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.pose.transforms_clear()

    mat_arm_to_mesh = mesh.matrix_world.inverted() @ arm.matrix_world
    rot_arm_to_mesh = mat_arm_to_mesh.to_3x3()

    for bname, deg in [
        ("Bip001 L Finger1", -4), ("Bip001 L Finger11", -14), ("Bip001 L Finger12", -18),
        ("Bip001 L Finger2", -4), ("Bip001 L Finger21", -14), ("Bip001 L Finger22", -18),
    ]:
        pose_bone_mesh_axis_curl(arm, rot_arm_to_mesh, bname, Vector((0.0, 1.0, 0.0)), deg)

    for bname, deg in [
        ("Bip001 R Finger1", -4), ("Bip001 R Finger11", -14), ("Bip001 R Finger12", -18),
        ("Bip001 R Finger2", -4), ("Bip001 R Finger21", -14), ("Bip001 R Finger22", -18),
    ]:
        pose_bone_mesh_axis_curl(arm, rot_arm_to_mesh, bname, Vector((0.0, -1.0, 0.0)), deg)

    ax_open_t = Vector((-0.861, 0.043, 0.507)).normalized()
    pose_bone_mesh_axis_curl(arm, rot_arm_to_mesh, "Bip001 L Finger0", ax_open_t, 66.8)
    pose_bone_mesh_axis_curl(arm, rot_arm_to_mesh, "Bip001 L Finger01", ax_open_t, -10.0)
    pose_bone_mesh_axis_curl(arm, rot_arm_to_mesh, "Bip001 L Finger02", ax_open_t, -10.0)

    for rname, ax_l, deg in [
        ("Bip001 R Finger0", ax_open_t, 66.8),
        ("Bip001 R Finger01", ax_open_t, -10.0),
        ("Bip001 R Finger02", ax_open_t, -10.0),
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

    # 1. Scale uniformly to Sideswipe 00 height (9.079m)
    raw_zs = [v.co.z for v in mesh.data.vertices]
    SCALE = 9.079 / (max(raw_zs) - min(raw_zs))
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

    # 2b. Subtle 2.3-deg outward arm flare around shoulder pivot (±1.40, 0, 7.79) so wrists align to Sideswipe X=±2.033m
    #     (Symbol_DC01 is on Bone Spine1 left chest, NOT left shoulder, so it does NOT rotate with the arm!)
    for side, pivot_x, angle_deg in (("L", 1.40, -2.3), ("R", -1.40, 2.3)):
        arm_vgs = {
            mesh.vertex_groups[n].index
            for n in (
                f"Bone {side} UpperArm", f"Bone Shoulder_02_{side}002", f"Bone Tire_01_{side}001",
                f"Bone {side} Forearm", f"Bone Arm_02_{side}", f"Bone {side} Hand",
                *(f"Bone {side} Finger{k}" for k in ("0", "01", "02", "1", "11", "12", "2", "21", "22")),
            )
            if n in mesh.vertex_groups
        }
        pivot = Vector((pivot_x, 0.0, 7.79))
        rot_y = Matrix.Rotation(math.radians(angle_deg), 4, 'Y')
        for v in mesh.data.vertices:
            if sum(g.weight for g in v.groups if g.group in arm_vgs) > 0.35:
                v.co = pivot + (rot_y @ (v.co - pivot))

    # 2c. C^0-continuous piecewise-linear Z alignment mapping EXACT Breakdown finger proximal bone heads -> Sideswipe m_BindPose!
    def map_finger_z(z: float) -> float:
        anchors = [
            (4.542, 4.542),  # Forearm cuff seam locked
            (4.070, 3.923),  # Bone L Finger1/2 head -> Sideswipe Index1/Middle1
            (3.886, 3.595),  # Bone L Finger11/21 head -> Sideswipe Index2/Middle2
            (3.730, 3.334),  # Bone L Finger12/22 head -> Sideswipe Index3/Middle3
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
                f"Bone {side} Hand",
                *(f"Bone {side} Finger{k}" for k in ("1", "11", "12", "2", "21", "22")),
            )
            if n in mesh.vertex_groups
        }
        thumb_vgs = {mesh.vertex_groups[f"Bone {side} Finger{k}"].index for k in ("0", "01", "02") if f"Bone {side} Finger{k}" in mesh.vertex_groups}
        for v in mesh.data.vertices:
            wh = sum(g.weight for g in v.groups if g.group in hand_vgs)
            wt = sum(g.weight for g in v.groups if g.group in thumb_vgs)
            w_eff = wh * max(0.0, 1.0 - wt)
            if w_eff > 0.05 and v.co.z < 4.542:
                v.co.z = v.co.z + (map_finger_z(v.co.z) - v.co.z) * min(1.0, w_eff)
    mesh.data.update()

    lh_vg = mesh.vertex_groups["Bone L Hand"]
    rh_vg = mesh.vertex_groups["Bone R Hand"]
    lh_pts = [v.co.x for v in mesh.data.vertices if any(g.group == lh_vg.index and g.weight > 0.3 for g in v.groups)]
    rh_pts = [v.co.x for v in mesh.data.vertices if any(g.group == rh_vg.index and g.weight > 0.3 for g in v.groups)]
    lh_x = sum(lh_pts) / len(lh_pts)
    rh_x = sum(rh_pts) / len(rh_pts)
    print(f"[*] Axis & Hand X check: LeftHand={lh_x:+.3f}, RightHand={rh_x:+.3f} (Sideswipe=±2.033m)")
    assert lh_x > 1.7 and rh_x < -1.7

    # 3. Clean U>1.0 wrapping + assign Symbol_DC01 to dedicated SubMesh 1 (purple left U=0.25, charcoal right U=0.75)
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
        t_uv = (0.25, 0.50) if p.material_index == 0 else (0.75, 0.50)
        for li in p.loop_indices:
            uvl[li].uv = t_uv

    mat_main = bpy.data.materials.new(name="cha_breakdown_main")
    mat_sym = bpy.data.materials.new(name="cha_breakdown_sym")
    mesh.data.materials.clear()
    mesh.data.materials.append(mat_main)
    sym_dc.data.materials.clear()
    sym_dc.data.materials.append(mat_sym)

    # Pin Symbol_DC01 onto Bone Spine1 (chest)
    sym_dc.vertex_groups.clear()
    sg = sym_dc.vertex_groups.new(name="Bone Spine1")
    sg.add(list(range(len(sym_dc.data.vertices))), 1.0, 'REPLACE')

    bpy.ops.object.select_all(action='DESELECT')
    sym_dc.select_set(True)
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.join()
    mesh.name = "cha_breakdown_robot"
    print(f"[✓] Joined Symbol_DC01 (SubMesh 1 on Spine1 chest). Total verts: {len(mesh.data.vertices)}, materials={len(mesh.data.materials)}")

    # 4. Identify pure core torso verts BEFORE remapping for smooth waist flex
    vg_dict = {vg.name: vg for vg in mesh.vertex_groups}
    torso_src_idxs = {vg_dict[n].index for n in ("Bip001 Pelvis", "Bone Spine", "Bone Spine1", "Bone Chest", "Bone Back", "Bone Back001") if n in vg_dict}
    torso_blend_verts = {
        v.index for v in mesh.data.vertices
        if sum(g.weight for g in v.groups if g.group in torso_src_idxs) > 0.75
    }

    target_vgs = {bn: mesh.vertex_groups.new(name=bn) for bn in SIDESWIPE_80_BONES}
    old_to_tgt = {vg_dict[old].index: target_vgs[tgt] for old, tgt in VGROUP_MAP.items() if old in vg_dict and tgt in target_vgs}

    for v in mesh.data.vertices:
        w_acc = {}
        for g in v.groups:
            if g.group in old_to_tgt:
                tvg = old_to_tgt[g.group]
                w_acc[tvg] = w_acc.get(tvg, 0.0) + g.weight
        for tvg, w in w_acc.items():
            tvg.add([v.index], w, 'REPLACE')

    for old_vg in [vg for vg in mesh.vertex_groups if vg.name not in SIDESWIPE_80_BONES]:
        mesh.vertex_groups.remove(old_vg)

    # 4b. Soft knuckle-seam weight blend on Index1/2/3 & Middle1/2/3 so rigid finger boxes stay flush across 0..100 deg curls
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

    # Smooth torso waist blend across Z=[5.40..6.70]
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
    print(f"[✓] Remapped 80 bones + {knuckle_blended} finger-seam verts + {smoothed} waist verts (zero-weight fixed: {zero_cnt})")

    # 5. Build Sideswipe 80-Bone Armature
    arm_data = bpy.data.armatures.new("cha_sideswipe_GS_Deluxe2008_00_arm")
    arm_obj = bpy.data.objects.new("cha_sideswipe_GS_Deluxe2008_00_arm", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')

    edit_bones = {}
    for bn in SIDESWIPE_80_BONES:
        b = arm_data.edit_bones.new(bn)
        wp = ss_pos_map[bn]
        b.head = wp
        b.tail = wp + Vector((0.0, 0.0, 0.25))
        edit_bones[bn] = b

    for bn, pname in ss_parent_map.items():
        if bn in edit_bones and pname and pname in edit_bones:
            edit_bones[bn].parent = edit_bones[pname]
            pb = edit_bones[pname]
            if (edit_bones[bn].head - pb.head).length > 0.05:
                pb.tail = edit_bones[bn].head

    bpy.ops.object.mode_set(mode='OBJECT')
    mesh.parent = arm_obj
    mod = mesh.modifiers.new("Armature", 'ARMATURE')
    mod.object = arm_obj

    blend_dir = BD_DIR / "01_aligned_mesh"
    blend_dir.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_dir / "breakdown_robot_aligned.blend"))

    for out_fbx in (OUT_FBX_DIR / "breakdown_robot_prepared.fbx", UNITY_DIR / "breakdown_robot_prepared.fbx"):
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
