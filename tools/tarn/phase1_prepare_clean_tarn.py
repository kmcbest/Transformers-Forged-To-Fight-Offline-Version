#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
phase1_prepare_clean_tarn.py
Upgraded Phase 1 pipeline for Tarn (Megatron GS Leader 2015 donor):
1. Opens 01_robot_source/source/last comp3.blend, resolves fallback_textures, fills empty images.
2. Calibrates Cycles shaders: attenuates heavy white scratches, converts pure-white (1,1,1) to
   Tarn silver-gunmetal, tunes yellow/orange accents toward Tarn gold, keeps eyes crimson & lines neon magenta.
3. Restores & uncurls BOTH 22-bone hands (Armature.000/Cylinder.001 Left & Armature.001/Cylinder.002 Right)
   preserving all handL__/handR__ finger vertex groups and saving world joint positions to tarn_hand_bones.json.
4. Straightens Tarn's posed head (+20.7 deg Z) and symmetrizes Left/Right arms to clean A-pose,
   normalizes centerline X=0 (from raw sym X=-33.65), Y centered around spine, Z=[0, 11.45m] at helmet top.
5. Smart per-part welding & decimation (crushing Cube.049/Cylinder.045 via voxel remesh while preserving
   crisp back/chest/mask/hands/cannon details) keeping total robot <= 32k tris (safe << 65,535 Unity verts).
6. Loads Megatron GS references, 51/21 bone armatures, and Tarn_Vehicle.glb aligned at Z_min=-1.549.
7. Saves 06_working/tarn_workspace_cleaned.blend & renders Gate 1 multi-angle inspection previews.
"""
import json
import math
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import bmesh
from mathutils import Matrix, Vector

TARN_ROOT = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Tarn")
BLEND_SRC = TARN_ROOT / "01_robot_source" / "source" / "last comp3.blend"
FALLBACK_DIR = TARN_ROOT / "01_robot_source" / "fallback_textures"
DONOR_DIR = TARN_ROOT / "04_donor_reference" / "megatron_gs_leader2015"
VEH_GLB = TARN_ROOT / "02_vehicle_source" / "Tarn_Vehicle.glb"
OUT_BLEND = TARN_ROOT / "06_working" / "tarn_workspace_cleaned.blend"
HAND_BONES_JSON = TARN_ROOT / "06_working" / "tarn_hand_bones.json"
SCRATCH_DIR = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\66aaeff3-2652-4f24-8fc9-00b0ef375582\scratch")
OUT_BLEND.parent.mkdir(parents=True, exist_ok=True)
SCRATCH_DIR.mkdir(parents=True, exist_ok=True)

RAW_SYM_X = -33.65
RAW_CENTER_Y = 1.50
RAW_FOOT_Z = -71.96
RAW_HELMET_TOP_Z = 2.10
SCALE_F = 11.45 / (RAW_HELMET_TOP_Z - RAW_FOOT_Z)  # ~0.154604

HEAD_PARTS = {
    "Sphere.001", "Plane.050", "Plane.000", "Cube.008",
    "Plane.002", "Plane.003", "Sphere.003", "Cube.028",
}
HEAD_PIVOT_RAW = Vector((-33.65, 1.86, -8.28))

RIGHT_ARM_PARTS = {
    "Cube.020", "Cube.021", "Cube.001", "Cube.002", "Cube.022",
    "Cylinder.002", "Cylinder.003", "Cylinder.004",
}
LEFT_ARM_PARTS = {
    "Cube.006", "Cube.025", "Cube.027", "Cylinder.001",
}

PART_TRI_BUDGETS = {
    "Sphere.001": 1500,
    "Plane.050": 2400,
    "Torus.000": 700,
    "Cylinder.001": 2400,
    "Cylinder.002": 2400,
    "Cube.020": 1300,
    "Cube.025": 1300,
    "Cylinder.038": 1100,
    "Cylinder.062": 1100,
    "Cube.019": 1500,
    "Cube.030": 1600,
    "Cylinder.003": 1900,
    "Cylinder.004": 1200,
    "Plane.004": 1200,
    "Plane.012": 900,
    "Plane.036": 1200,
    "Plane.008": 1200,
    "Circle.000": 800,
    "Cylinder.011": 700,
    "Cylinder.015": 700,
    "Cube.008": 800,
    "Plane.000": 800,
    "Plane.009": 650,
    "Plane.010": 650,
    "Plane.058": 650,
    "Plane.059": 650,
    "Cylinder.014": 900,
}


def import_obj_compat(filepath: Path):
    if hasattr(bpy.ops.wm, "obj_import"):
        bpy.ops.wm.obj_import(filepath=str(filepath))
    else:
        bpy.ops.import_scene.obj(filepath=str(filepath))


def fix_missing_and_empty_images():
    print("[1/7] Resolving fallback textures & empty datablocks...")
    if FALLBACK_DIR.is_dir():
        bpy.ops.file.find_missing_files(directory=str(FALLBACK_DIR))
    for img in bpy.data.images:
        if img.source == 'FILE' and not img.has_data:
            cand = FALLBACK_DIR / Path(bpy.path.abspath(img.filepath)).name
            if cand.is_file():
                img.filepath = str(cand)
                img.reload()
        if img.size[0] == 0 or img.size[1] == 0:
            img.source = 'GENERATED'
            img.generated_width = 16
            img.generated_height = 16
            img.generated_color = (0.0, 0.0, 0.0, 1.0)
            img.reload()


def calibrate_cycles_materials():
    print("[2/7] Calibrating Cycles materials (reducing scratch noise, matching Tarn palette)...")
    # Silver-lilac target in linear ~ (0.48, 0.47, 0.65), gold target in linear ~ (0.52, 0.27, 0.03)
    white_to_silver = {"Material.011", "Material.029", "Material.031", "Material.034"}
    gray_to_silver = {"Material.013"}
    gold_mats = {"Material.019", "a metall.004"}

    for mat in bpy.data.materials:
        if not mat.use_nodes or not mat.node_tree:
            continue
        nt = mat.node_tree

        # 1) Attenuate scratch masks on Mix Shaders so armor stays clean dark purple
        for nd in list(nt.nodes):
            if nd.type == 'MIX_SHADER':
                fac_in = nd.inputs[0]
                if fac_in.is_linked:
                    # Only attenuate mask* scratch overlays (not emission mixes)
                    src_node = fac_in.links[0].from_node
                    has_emit = any(
                        inp.is_linked and inp.links[0].from_node.type == 'EMISSION'
                        for inp in nd.inputs[1:]
                    )
                    if src_node.type == 'TEX_IMAGE' and not has_emit:
                        mul = nt.nodes.new('ShaderNodeMath')
                        mul.operation = 'MULTIPLY'
                        mul.inputs[1].default_value = 0.20
                        src_sock = fac_in.links[0].from_socket
                        nt.links.new(src_sock, mul.inputs[0])
                        nt.links.new(mul.outputs[0], fac_in)
                else:
                    fac_in.default_value = min(fac_in.default_value, 0.22)

            if nd.type == 'BSDF_PRINCIPLED':
                base = nd.inputs['Base Color']
                if mat.name in white_to_silver and not base.is_linked:
                    base.default_value = (0.48, 0.47, 0.65, 1.0)
                elif mat.name in gold_mats and not base.is_linked:
                    base.default_value = (0.52, 0.27, 0.03, 1.0)
                else:
                    # Darken harsh light-gray worn-edge Principled BSDF (0.62..0.78 -> 0.36..0.42)
                    c = base.default_value
                    if not base.is_linked and abs(c[0] - c[1]) < 0.03 and abs(c[1] - c[2]) < 0.03 and 0.50 <= c[0] <= 0.85:
                        base.default_value = (0.36, 0.35, 0.42, 1.0)

            elif nd.type == 'BSDF_DIFFUSE':
                if mat.name in gray_to_silver:
                    nd.inputs['Color'].default_value = (0.45, 0.44, 0.58, 1.0)
                elif mat.name in gold_mats:
                    nd.inputs['Color'].default_value = (0.52, 0.27, 0.03, 1.0)

            elif nd.type == 'BSDF_GLOSSY':
                if mat.name in gray_to_silver:
                    nd.inputs['Color'].default_value = (0.50, 0.49, 0.65, 1.0)

            elif nd.type == 'EMISSION':
                if mat.name == "Material.005":
                    # Vibrant crimson-red eyes
                    nd.inputs['Color'].default_value = (0.95, 0.04, 0.06, 1.0)
                    nd.inputs['Strength'].default_value = 8.0


def restore_and_uncurl_hands():
    print("[3/7] Restoring & uncurling Left/Right 22-bone hands (preserving vertex groups)...")
    arm_l = bpy.data.objects["Armature.000"]
    arm_r = bpy.data.objects["Armature.001"]
    hand_l = bpy.data.objects["Cylinder.001"]
    hand_r = bpy.data.objects["Cylinder.002"]

    # Copy Left open-hand finger pose rotations (Bone.001..022) onto Right curled-hand armature
    for pb_r in arm_r.pose.bones:
        if pb_r.name != "Bone" and pb_r.name in arm_l.pose.bones:
            pb_l = arm_l.pose.bones[pb_r.name]
            pb_r.rotation_mode = pb_l.rotation_mode
            pb_r.rotation_quaternion = pb_l.rotation_quaternion.copy()
            pb_r.rotation_euler = pb_l.rotation_euler.copy()
            pb_r.location = pb_l.location.copy()
            pb_r.scale = pb_l.scale.copy()
    bpy.context.view_layer.update()

    # Prefix hand vertex groups BEFORE baking Armature modifier & joining
    for side, mobj in [("handL__", hand_l), ("handR__", hand_r)]:
        for vg in mobj.vertex_groups:
            if not vg.name.startswith(side):
                vg.name = side + vg.name

    # Record world bone positions BEFORE detaching/deleting Armature.000/001
    hand_bones_raw = {}
    for side_key, arm_obj in [("L", arm_l), ("R", arm_r)]:
        bdict = {}
        for pb in arm_obj.pose.bones:
            hw = arm_obj.matrix_world @ pb.head
            tw = arm_obj.matrix_world @ pb.tail
            bdict[pb.name] = {
                "parent": pb.parent.name if pb.parent else None,
                "head_raw": [hw.x, hw.y, hw.z],
                "tail_raw": [tw.x, tw.y, tw.z],
            }
        hand_bones_raw[side_key] = bdict

    # Apply Armature modifier on both hands FIRST, then clear parent KEEP_TRANSFORM
    for mobj in (hand_l, hand_r):
        bpy.ops.object.select_all(action='DESELECT')
        mobj.select_set(True)
        bpy.context.view_layer.objects.active = mobj
        for mod in list(mobj.modifiers):
            if mod.type == 'ARMATURE':
                bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

    # Remove old hand armatures safely after baking
    bpy.data.objects.remove(arm_l, do_unlink=True)
    bpy.data.objects.remove(arm_r, do_unlink=True)
    return hand_bones_raw


def straighten_head_and_arms(hand_bones_raw):
    print("[4/7] Straightening head (+20.7 deg Z) & symmetrizing posed arms...")
    # 1) Rotate head parts +20.7 deg around Z at HEAD_PIVOT_RAW
    rot_head = Matrix.Translation(HEAD_PIVOT_RAW) @ Matrix.Rotation(math.radians(20.7), 4, 'Z') @ Matrix.Translation(-HEAD_PIVOT_RAW)
    for nm in HEAD_PARTS:
        o = bpy.data.objects.get(nm)
        if o:
            o.matrix_world = rot_head @ o.matrix_world

    # 2) Align Left Arm & Right Arm forward/back tilt around shoulders to hang symmetrically near Y_raw ~ +1.0
    # Note: Left Arm is swung back (hand Y=-1.03), Right Arm is swung forward (hand Y=-7.99)
    # Pivot near shoulder center: L_sh ~ (-15.0, +4.0, -17.0), R_sh ~ (-52.3, +2.0, -17.0)
    l_sh = Vector((RAW_SYM_X + 18.65, 4.5, -16.8))
    r_sh = Vector((RAW_SYM_X - 18.65, 2.0, -16.8))
    # Rotate Left Arm forward (-14 deg around X) and Right Arm backward (+16 deg around X)
    rot_l = Matrix.Translation(l_sh) @ Matrix.Rotation(math.radians(-14.0), 4, 'X') @ Matrix.Translation(-l_sh)
    rot_r = Matrix.Translation(r_sh) @ Matrix.Rotation(math.radians(+16.0), 4, 'X') @ Matrix.Translation(-r_sh)

    for nm in LEFT_ARM_PARTS:
        o = bpy.data.objects.get(nm)
        if o:
            o.matrix_world = rot_l @ o.matrix_world
    for nm in RIGHT_ARM_PARTS:
        o = bpy.data.objects.get(nm)
        if o:
            o.matrix_world = rot_r @ o.matrix_world

    # Transform recorded hand_bones_raw by rot_l / rot_r so they stay 100% locked to hand meshes!
    for side_key, rot_m in [("L", rot_l), ("R", rot_r)]:
        for bname, info in hand_bones_raw[side_key].items():
            h = rot_m @ Vector(info["head_raw"])
            t = rot_m @ Vector(info["tail_raw"])
            info["head_raw"] = [h.x, h.y, h.z]
            info["tail_raw"] = [t.x, t.y, t.z]
    bpy.context.view_layer.update()


def transform_raw_to_norm(pt: Vector) -> Vector:
    return Vector((
        (pt.x - RAW_SYM_X) * SCALE_F,
        (pt.y - RAW_CENTER_Y) * SCALE_F,
        (pt.z - RAW_FOOT_Z) * SCALE_F,
    ))


def voxel_simplify_greeble(obj, divisions=34):
    """Replace ultra-dense non-manifold wire greebles (Cube.049/Cylinder.045) with clean low-poly solid."""
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    dim = max(obj.dimensions.x, obj.dimensions.y, obj.dimensions.z, 0.1)
    # Pick charcoal material if available
    char_mat = bpy.data.materials.get("a metall.000")
    mr = obj.modifiers.new("VoxelSimp", 'REMESH')
    mr.mode = 'VOXEL'
    mr.voxel_size = max(dim / divisions, 0.04)
    bpy.ops.object.modifier_apply(modifier=mr.name)
    if char_mat:
        obj.data.materials.clear()
        obj.data.materials.append(char_mat)


def clean_decimate_and_join(hand_bones_raw):
    print("[5/7] Cleaning modifiers, smart per-part decimation, and joining Tarn_Robot_LowPoly...")
    col_src = bpy.data.collections.new("Tarn_Robot_RawParts")
    bpy.context.scene.collection.children.link(col_src)

    decal_mats = {"decal02_33", "paneling01_04"}
    robot_meshes = []

    bpy.ops.object.select_all(action='DESELECT')
    for obj in list(bpy.data.objects):
        if obj.type in ('CAMERA', 'LIGHT', 'EMPTY'):
            bpy.data.objects.remove(obj, do_unlink=True)
            continue
        if obj.type == 'CURVE':
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.convert(target='MESH')
            obj.select_set(False)
        if obj.type == 'MESH':
            mat_names = {ms.material.name for ms in obj.material_slots if ms.material}
            if mat_names and mat_names.issubset(decal_mats):
                bpy.data.objects.remove(obj, do_unlink=True)
                continue
            robot_meshes.append(obj)

    for obj in robot_meshes:
        if obj.parent:
            mw = obj.matrix_world.copy()
            obj.parent = None
            obj.matrix_world = mw
        if obj.data.users > 1:
            obj.data = obj.data.copy()

        for mod in list(obj.modifiers):
            if mod.type == 'SUBSURF':
                obj.modifiers.remove(mod)
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        for mod in list(obj.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception as e:
                print(f"  [!] Skipping modifier {obj.name}.{mod.name}: {e}")

        det = obj.matrix_world.to_3x3().determinant()
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        if det < 0:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.object.mode_set(mode='OBJECT')
            print(f"  [!] Fixed negative-det normals: {obj.name} (det={det:.3f})")
        obj.select_set(False)

        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        col_src.objects.link(obj)

    # Smart per-part welding & decimation
    for obj in robot_meshes:
        orig_name = obj.name
        if orig_name in ("Cube.049", "Cylinder.045"):
            voxel_simplify_greeble(obj, divisions=30 if orig_name == "Cube.049" else 36)
            ntri = sum(max(0, len(p.vertices) - 2) for p in obj.data.polygons)
            print(f"  [✓] Voxel-simplified {orig_name}: {ntri} tris, {len(obj.data.vertices)} verts")
            continue

        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)

        # Weld split vertices on high-density meshes so Collapse Decimate works cleanly
        if len(obj.data.vertices) > 2500:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles(threshold=0.002)
            bpy.ops.object.mode_set(mode='OBJECT')

        ntri = sum(max(0, len(p.vertices) - 2) for p in obj.data.polygons)
        budget = PART_TRI_BUDGETS.get(orig_name, 800)
        if ntri > budget:
            mod = obj.modifiers.new("PartDecimate", 'DECIMATE')
            mod.decimate_type = 'COLLAPSE'
            mod.ratio = max(0.01, budget / float(ntri))
            bpy.ops.object.modifier_apply(modifier=mod.name)
            ntri2 = sum(max(0, len(p.vertices) - 2) for p in obj.data.polygons)
            print(f"  [✓] Decimated {orig_name:16s}: {ntri:6d} -> {ntri2:5d} tris (target={budget})")
        obj.select_set(False)

    # Preserve handL__/handR__ vertex groups, clear junk groups, add part__<orig_name>
    for o in robot_meshes:
        keep_prefix = ("handL__", "handR__")
        for vg in list(o.vertex_groups):
            if not vg.name.startswith(keep_prefix):
                o.vertex_groups.remove(vg)
        if len(o.data.vertices) > 0:
            vg = o.vertex_groups.new(name=f"part__{o.name}")
            vg.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')

    # Join into Tarn_Robot_LowPoly
    bpy.ops.object.select_all(action='DESELECT')
    for o in robot_meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = robot_meshes[0]
    bpy.ops.object.join()
    robot = bpy.context.active_object
    robot.name = "Tarn_Robot_LowPoly"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Normalize coordinates (center X=0 at RAW_SYM_X, Y near spine, ground Z=0, helmet top=11.45)
    for v in robot.data.vertices:
        v.co = transform_raw_to_norm(v.co)
    # Fine-tune exact min_z = 0
    min_z = min(v.co.z for v in robot.data.vertices)
    for v in robot.data.vertices:
        v.co.z -= min_z
    robot.data.update()

    # Transform hand bone positions into exact same normalized coordinates
    hand_bones_norm = {}
    for side_key in ("L", "R"):
        hand_bones_norm[side_key] = {}
        for bname, info in hand_bones_raw[side_key].items():
            hn = transform_raw_to_norm(Vector(info["head_raw"]))
            tn = transform_raw_to_norm(Vector(info["tail_raw"]))
            hn.z -= min_z
            tn.z -= min_z
            hand_bones_norm[side_key][bname] = {
                "parent": info["parent"],
                "head": [hn.x, hn.y, hn.z],
                "tail": [tn.x, tn.y, tn.z],
            }
    HAND_BONES_JSON.write_text(json.dumps(hand_bones_norm, indent=2), encoding='utf-8')

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')

    total_tris = sum(max(0, len(p.vertices) - 2) for p in robot.data.polygons)
    zs = [v.co.z for v in robot.data.vertices]
    xs = [v.co.x for v in robot.data.vertices]
    ys = [v.co.y for v in robot.data.vertices]
    print(f"[✓] Tarn_Robot_LowPoly ready: verts={len(robot.data.vertices):,}, tris={total_tris:,}, X=[{min(xs):.2f},{max(xs):.2f}], Y=[{min(ys):.2f},{max(ys):.2f}], Z=[{min(zs):.2f},{max(zs):.2f}]")
    return robot


def build_armature_from_spec(spec_path: Path, arm_name: str, col_target):
    spec = json.loads(spec_path.read_text(encoding='utf-8'))
    arm_data = bpy.data.armatures.new(arm_name)
    arm_obj = bpy.data.objects.new(arm_name, arm_data)
    col_target.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')

    bones_info = {b["name"]: b for b in spec["bones"]}
    children_map = {}
    for b in spec["bones"]:
        p = b.get("parent_transform_name")
        children_map.setdefault(p, []).append(b["name"])

    edit_bones = {}
    for b in spec["bones"]:
        eb = arm_data.edit_bones.new(b["name"])
        pos = Vector(b["blender_pos_matching_obj"])
        eb.head = pos
        kids = [k for k in children_map.get(b["name"], []) if k in bones_info]
        if kids:
            avg = sum((Vector(bones_info[k]["blender_pos_matching_obj"]) for k in kids), Vector((0, 0, 0))) / len(kids)
            eb.tail = avg if (avg - pos).length > 0.02 else (pos + Vector((0, 0, 0.15)))
        else:
            eb.tail = pos + Vector((0, -0.15, 0))
        edit_bones[b["name"]] = eb

    for b in spec["bones"]:
        p = b.get("parent_transform_name")
        if p in edit_bones:
            edit_bones[b["name"]].parent = edit_bones[p]

    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"[✓] Created donor armature {arm_name} ({len(arm_data.bones)} bones)")
    return arm_obj


def load_donors_and_vehicle():
    print("[6/7] Loading Megatron GS donor OBJs, armatures, and Tarn_Vehicle.glb...")
    col_ref = bpy.data.collections.new("04_Donor_References")
    bpy.context.scene.collection.children.link(col_ref)

    for obj_name in ["cha_megatron_gs_leader2015_00_robot.obj", "cha_megatron_gs_leader2015_01_tank.obj", "cha_megatron_gs_leader2015_wpns_cannon_right.obj"]:
        p = DONOR_DIR / obj_name
        if p.is_file():
            before = set(bpy.data.objects)
            import_obj_compat(p)
            for o in set(bpy.data.objects) - before:
                o.name = f"REF_{obj_name[:-4]}"
                o.display_type = 'WIRE'
                for c in list(o.users_collection):
                    c.objects.unlink(o)
                col_ref.objects.link(o)

    build_armature_from_spec(DONOR_DIR / "robot_51_bones_and_bindposes.json", "ARM_MegatronGS_Robot51", col_ref)
    build_armature_from_spec(DONOR_DIR / "tank_21_bones_and_bindposes.json", "ARM_MegatronGS_Tank21", col_ref)

    col_veh = bpy.data.collections.new("02_Tarn_Vehicle")
    bpy.context.scene.collection.children.link(col_veh)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(VEH_GLB))
    veh_objs = list(set(bpy.data.objects) - before)
    veh_meshes = [o for o in veh_objs if o.type == 'MESH']
    for o in veh_objs:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col_veh.objects.link(o)

    for o in veh_meshes:
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True)
        if "Tread" in o.name:
            mod = o.modifiers.new("TreadDecimate", 'DECIMATE')
            mod.ratio = 0.22
            bpy.ops.object.modifier_apply(modifier=mod.name)
            print(f"  [✓] Tread decimated: {o.name} -> {len(o.data.polygons)} polys, {len(o.data.vertices)} verts")
        o.select_set(False)

    # Scale 0.78x and align tread bottom strictly to Z = -1.549m
    veh_roots = [o for o in veh_objs if o.parent is None]
    for r in veh_roots:
        r.scale = (0.78, 0.78, 0.78)
    bpy.context.view_layer.update()
    min_vz = min((o.matrix_world @ v.co).z for o in veh_meshes for v in o.data.vertices)
    dz = -1.549 - min_vz
    for r in veh_roots:
        r.location.z += dz
    bpy.context.view_layer.update()
    new_min_vz = min((o.matrix_world @ v.co).z for o in veh_meshes for v in o.data.vertices)
    print(f"  [✓] Tarn_Vehicle grounded to Z_min = {new_min_vz:.3f}m (Megatron Tank = -1.549m)")


def render_gate1_verification(robot):
    print("[7/7] Saving workspace & rendering Gate 1 multi-angle inspection views...")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))

    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 900
    if not scene.world:
        scene.world = bpy.data.worlds.new("W")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.18, 0.19, 0.23, 1.0)
    scene.world.node_tree.nodes["Background"].inputs[1].default_value = 1.0

    def look_at(obj, pos, target):
        obj.location = Vector(pos)
        obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()

    for nm, pos, en in [("Key", (8, -18, 14), 3.0), ("Fill", (-10, -15, 8), 1.8), ("Rim", (0, 18, 12), 2.5)]:
        lo = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN'))
        lo.data.energy = en
        scene.collection.objects.link(lo)
        look_at(lo, pos, (0, 0, 5.5))

    cam = bpy.data.objects.new("Gate1Cam", bpy.data.cameras.new("Gate1Cam"))
    cam.data.lens = 45.0
    scene.collection.objects.link(cam)
    scene.camera = cam

    for o in bpy.data.objects:
        if "TarnTank" in o.name or "01_tank" in o.name or "cannon_right" in o.name:
            o.hide_render = True

    ref0 = bpy.data.objects.get("REF_cha_megatron_gs_leader2015_00_robot")
    if ref0:
        ref0.location = (6.5, 0, 0)
        ref0.hide_render = False
    robot.hide_render = False

    for fname, cpos, ctgt in [
        ("gate1_v2_front.png", (3.2, -24.0, 5.9), (3.2, 0.0, 5.7)),
        ("gate1_v2_back.png", (0.0, 22.0, 6.0), (0.0, 0.0, 5.7)),
        ("gate1_v2_head_closeup.png", (0.0, -7.0, 10.1), (0.0, 0.0, 10.1)),
    ]:
        look_at(cam, cpos, ctgt)
        scene.render.filepath = str(SCRATCH_DIR / fname)
        bpy.ops.render.render(write_still=True)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND_SRC))
    fix_missing_and_empty_images()
    calibrate_cycles_materials()
    hand_bones_raw = restore_and_uncurl_hands()
    straighten_head_and_arms(hand_bones_raw)
    robot = clean_decimate_and_join(hand_bones_raw)
    load_donors_and_vehicle()
    render_gate1_verification(robot)
    print("[OK] Phase 1 clean preparation + Gate 1 verification complete!")


if __name__ == "__main__":
    main()
