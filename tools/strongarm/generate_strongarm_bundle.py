#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_strongarm_bundle.py

Synthesizes assets_redeco/strongarm_gs.assetbundle from Prowl (prowl_gs_deluxe2016)
and the Unity-verified grafted meshes in strongarm_mesh.assetbundle:
1. Direct pass-through of authoritative Unity-space meshes (cha_strongarm_gs_00 &
   cha_strongarm_gs_01).
2. Injects Prowl's exact 50-bone m_BindPose + m_BoneNameHashes (Robot) and
   26-bone m_BindPose + m_BoneNameHashes (Vehicle).
3. Strict Dual-Prefab SMR isolation across Prefab 1 (Showcase: -8683282172418555027)
   and Prefab 2 (Combat _lw: -8048857395234776728), preserving local SMR m_AABB
   and keeping Prowl's weapons (baton, shotgun, chain) fully functional.
4. Binds single-submesh Robot & Vehicle SMRs to tuned Kabam Satin PBR Materials
   with full [0,1]x[0,1] UV scale=(1,1), offset=(0,0) on Diffuse, Normal, and RAOE.
5. Injects 2048x2048 textures, including dedicated Vehicle RAOE into ContactShadowB.
6. Rewires victory poses in AnimatorOverrideController to Ultra Magnus victory poses.
7. Enforces 100% opaque Diffuse alpha=255, updates m_Container & CAB strings,
   asserts upright AABB bounds, and packages with LZ4 compression.
"""

import copy
import sys
from pathlib import Path
import numpy as np
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

try:
    import UnityPy
except ImportError:
    print("Error: UnityPy is required.")
    sys.exit(1)

MAIN_MAT_PID = 7500203752916154549      # Robot main PBR material (558FC8F214D64839399816A6FC9AEED84D77CDE2)
VH_MAT_PID = 8471270994157717165       # Vehicle PBR material (94615E736488E63880999F20D3256250C0DC05BB)
VH_MAT_PID_ALT = -7118460493794104175  # Vehicle PBR material alt (87791CF98FF8EC7989E934D022223541EC4F3AB9)

TEX_MAIN_A_PID = 8699654113595830490    # cha_prowl_gs_deluxe2016_main_a
TEX_MAIN_NM_PID = -5650952820722940311  # main_NM
TEX_MAIN_RAOE_PID = -1377069345250401912 # main_tform_misc_RAOE

TEX_VH_A_PID = -3877080133234792206     # tform_misc_A
TEX_VH_NM_PID = 7289807295065357004     # tform_misc_NM
TEX_VH_RAOE_PID = TEX_MAIN_RAOE_PID     # Unified main_tform_misc_RAOE bottom-right tile [0.75..1.0, 0.0..0.25]

ULTRA_MAGNUS_VICTORY_PID = 9212422502065540883
ULTRA_MAGNUS_VICTORY_IDLE_PID = 9212422502065540881


def replace_str_in_tree(tree_obj, old_s, new_s):
    if isinstance(tree_obj, dict):
        for k, v in tree_obj.items():
            if isinstance(v, str) and old_s in v:
                tree_obj[k] = v.replace(old_s, new_s)
            else:
                replace_str_in_tree(v, old_s, new_s)
    elif isinstance(tree_obj, list):
        for i, item in enumerate(tree_obj):
            if isinstance(item, str) and old_s in item:
                tree_obj[i] = item.replace(old_s, new_s)
            else:
                replace_str_in_tree(item, old_s, new_s)


def prepare_authoritative_mesh(mesh_tree, target_name, bindposes, bone_hashes):
    mesh_copy = copy.deepcopy(mesh_tree)
    mesh_copy["m_Name"] = target_name
    mesh_copy["m_BindPose"] = copy.deepcopy(bindposes)
    if bone_hashes:
        mesh_copy["m_BoneNameHashes"] = copy.deepcopy(bone_hashes)
    aabb = mesh_copy.get("m_LocalAABB", {})
    c = aabb.get("m_Center", {})
    e = aabb.get("m_Extent", {})
    bounds_info = {
        "center_x": float(c.get("x", 0.0)),
        "center_y": float(c.get("y", 0.0)),
        "center_z": float(c.get("z", 0.0)),
        "extent_x": float(e.get("x", 0.0)),
        "extent_y": float(e.get("y", 0.0)),
        "extent_z": float(e.get("z", 0.0)),
    }
    return mesh_copy, bounds_info


def load_opaque_rgba(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGBA")
    arr = np.array(img, dtype=np.uint8)
    arr[:, :, 3] = 255  # Guarantee zero accidental alpha cutout/sorting holes
    return Image.fromarray(arr, mode="RGBA")


def tune_kabam_pbr_material(
    mat_tree, base_pid, norm_pid, raoe_pid,
    metallic_range=0.22, roughness_range=0.90,
    raoe_scale=(1.0, 1.0), raoe_offset=(0.0, 0.0),
    albedo_tint=1.0, overbright=16.0,
):
    saved_props = mat_tree.get("m_SavedProperties", {})
    new_floats = []
    for k, v in saved_props.get("m_Floats", []):
        if k == "_Mode":
            new_floats.append((k, 3.0))  # Official Kabam _MODE_CLEARCOAT (enables RAOE emissive + satin PBR)
        elif k == "_metallic_range":
            new_floats.append((k, metallic_range))
        elif k == "_roughness_range":
            new_floats.append((k, roughness_range))
        elif k == "_clearcoat_reflectance_range":
            new_floats.append((k, 0.035))
        elif k == "_reflectance":
            new_floats.append((k, 0.035))
        elif k == "_emissive_range":
            new_floats.append((k, 1.0))
        elif k == "_emissive_overbright_range":
            new_floats.append((k, overbright))
        elif k == "_emissive_none":
            new_floats.append((k, 0.0))
        elif k == "_ZWrite":
            new_floats.append((k, 1.0))
        else:
            new_floats.append((k, v))
    saved_props["m_Floats"] = new_floats

    new_colors = []
    for k, v in saved_props.get("m_Colors", []):
        if k in ("_base_col", "_Color", "_base2_col"):
            new_colors.append((k, {"r": albedo_tint, "g": albedo_tint, "b": albedo_tint, "a": 1.0}))
        elif k == "_emissive_intensity_col":
            new_colors.append((k, {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}))
        else:
            new_colors.append((k, v))
    saved_props["m_Colors"] = new_colors

    new_texs = []
    for k, v in saved_props.get("m_TexEnvs", []):
        if k == "_base_tex":
            v["m_Texture"] = {"m_FileID": 0, "m_PathID": base_pid}
            v["m_Scale"] = {"x": 1.0, "y": 1.0}
            v["m_Offset"] = {"x": 0.0, "y": 0.0}
        elif k == "_normal_tex":
            v["m_Texture"] = {"m_FileID": 0, "m_PathID": norm_pid}
            v["m_Scale"] = {"x": 1.0, "y": 1.0}
            v["m_Offset"] = {"x": 0.0, "y": 0.0}
        elif k == "_pbr_composite_tex":
            v["m_Texture"] = {"m_FileID": 0, "m_PathID": raoe_pid}
            v["m_Scale"] = {"x": raoe_scale[0], "y": raoe_scale[1]}
            v["m_Offset"] = {"x": raoe_offset[0], "y": raoe_offset[1]}
        new_texs.append((k, v))
    saved_props["m_TexEnvs"] = new_texs


def generate_bundle():
    root = Path(r"E:\Agent\TFTF-blender")
    compiled_bundle_path = root / "toolchain" / "unity_build_project" / "AssetBundles" / "strongarm_mesh.assetbundle"
    prowl_bundle_path = root / "extracted_apk" / "assets" / "assetpack" / "prowl_gs_deluxe2016_odr" / "prowl_gs_deluxe2016.assetbundle"
    if not prowl_bundle_path.is_file():
        prowl_bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")
    output_bundle_path = root / "assets_redeco" / "strongarm_gs.assetbundle"
    output_bundle_path.parent.mkdir(parents=True, exist_ok=True)

    if not compiled_bundle_path.is_file():
        raise FileNotFoundError(f"Missing {compiled_bundle_path}. Build it via PackStrongarmMeshBundle first.")

    print(f"[*] Loading compiled Strongarm mesh bundle: {compiled_bundle_path.name}...")
    c_env = UnityPy.load(str(compiled_bundle_path))

    print(f"[*] Loading clean official Prowl bundle: {prowl_bundle_path}...")
    g_env = UnityPy.load(str(prowl_bundle_path))

    # 1. Extract authoritative Unity-space Robot & Vehicle Meshes
    robot_mesh_tree = None
    vh_mesh_tree = None
    for obj in c_env.objects:
        if obj.type.name == "Mesh":
            tree = obj.read_typetree()
            m_name = tree.get("m_Name", "")
            if m_name == "cha_strongarm_gs_00":
                robot_mesh_tree = tree
                print(f"[+] Found Robot Mesh: {m_name}, verts={tree.get('m_VertexData', {}).get('m_VertexCount')}, submeshes={len(tree.get('m_SubMeshes', []))}")
            elif m_name == "cha_strongarm_gs_01":
                vh_mesh_tree = tree
                print(f"[+] Found Vehicle Mesh: {m_name}, verts={tree.get('m_VertexData', {}).get('m_VertexCount')}, submeshes={len(tree.get('m_SubMeshes', []))}")

    if robot_mesh_tree is None or vh_mesh_tree is None:
        raise ValueError("Missing cha_strongarm_gs_00 or cha_strongarm_gs_01 in strongarm_mesh.assetbundle!")

    # 2. Extract Transform hierarchies for Prefab 1 (Showcase: -8683282172418555027) and Prefab 2 (Combat _lw: -8048857395234776728)
    P1_ROOT_ID = -8683282172418555027
    P2_ROOT_ID = -8048857395234776728

    tr_to_go = {}
    go_to_tr = {}
    go_dict = {}
    tr_dict = {}
    for obj in g_env.objects:
        if obj.type.name == "GameObject":
            go_dict[obj.path_id] = obj.read_typetree()
        elif obj.type.name == "Transform":
            tree = obj.read_typetree()
            tr_dict[obj.path_id] = tree
            go_id = tree.get("m_GameObject", {}).get("m_PathID")
            tr_to_go[obj.path_id] = go_id
            go_to_tr[go_id] = obj.path_id

    def get_prefab_transforms(root_go_id):
        result = {}
        def recurse(go_id):
            go = go_dict.get(go_id)
            if not go:
                return
            name = go.get("m_Name")
            tr_id = go_to_tr.get(go_id)
            if name not in result:
                result[name] = tr_id
            tr = tr_dict.get(tr_id)
            if tr:
                for child in tr.get("m_Children", []):
                    recurse(tr_to_go.get(child.get("m_PathID")))
        recurse(root_go_id)
        return result

    p1_transforms = get_prefab_transforms(P1_ROOT_ID)
    p2_transforms = get_prefab_transforms(P2_ROOT_ID)
    p1_tr_set = set(p1_transforms.values())
    print(f"[+] Prefab 1 (Showcase) transforms: {len(p1_transforms)} | Prefab 2 (Combat _lw) transforms: {len(p2_transforms)}")

    # 3. Extract ground-truth bindposes, m_BoneNameHashes, SMR bone orders, and local SMR m_AABBs from Prowl
    prowl_bindposes = None
    prowl_bone_hashes = None
    prowl_smr_bones = []
    prowl_robot_smr_aabb = None

    prowl_vh_bindposes = None
    prowl_vh_bone_hashes = None
    prowl_vh_bones = []
    prowl_vh_smr_aabb = None

    for obj in g_env.objects:
        if obj.type.name == "Mesh":
            tree = obj.read_typetree()
            if tree.get("m_Name") == "cha_prowl_gs_deluxe2016_00":
                prowl_bindposes = tree.get("m_BindPose", [])
                prowl_bone_hashes = tree.get("m_BoneNameHashes", [])
            elif tree.get("m_Name") == "cha_prowl_gs_deluxe2016_01":
                prowl_vh_bindposes = tree.get("m_BindPose", [])
                prowl_vh_bone_hashes = tree.get("m_BoneNameHashes", [])
        elif obj.type.name == "SkinnedMeshRenderer":
            tree = obj.read_typetree()
            bones = tree.get("m_Bones", [])
            if len(bones) == 50 and not prowl_smr_bones:
                prowl_robot_smr_aabb = copy.deepcopy(tree.get("m_AABB"))
                for b in bones:
                    go_id = tr_to_go.get(b.get("m_PathID"))
                    prowl_smr_bones.append(go_dict.get(go_id, {}).get("m_Name"))
            elif len(bones) == 26 and not prowl_vh_bones:
                prowl_vh_smr_aabb = copy.deepcopy(tree.get("m_AABB"))
                for b in bones:
                    go_id = tr_to_go.get(b.get("m_PathID"))
                    prowl_vh_bones.append(go_dict.get(go_id, {}).get("m_Name"))

    assert len(prowl_bindposes) == 50 and len(prowl_bone_hashes) == 50, f"Expected 50 Prowl robot bindposes & hashes, got {len(prowl_bindposes)}!"
    assert len(prowl_vh_bindposes) == 26 and len(prowl_vh_bone_hashes) == 26, f"Expected 26 Prowl vehicle bindposes & hashes, got {len(prowl_vh_bindposes)}!"

    # 4. Prepare meshes & enforce upright AABB assertions
    robot_mesh_copy, r_bounds = prepare_authoritative_mesh(
        robot_mesh_tree, "cha_prowl_gs_deluxe2016_00", prowl_bindposes, prowl_bone_hashes
    )
    vh_mesh_copy, vh_bounds = prepare_authoritative_mesh(
        vh_mesh_tree, "cha_prowl_gs_deluxe2016_01", prowl_vh_bindposes, prowl_vh_bone_hashes
    )
    print(f"[+] Robot LocalAABB:   center=({r_bounds['center_x']:.2f}, {r_bounds['center_y']:.2f}, {r_bounds['center_z']:.2f}), extent=({r_bounds['extent_x']:.2f}, {r_bounds['extent_y']:.2f}, {r_bounds['extent_z']:.2f})")
    print(f"[+] Vehicle LocalAABB: center=({vh_bounds['center_x']:.2f}, {vh_bounds['center_y']:.2f}, {vh_bounds['center_z']:.2f}), extent=({vh_bounds['extent_x']:.2f}, {vh_bounds['extent_y']:.2f}, {vh_bounds['extent_z']:.2f})")

    assert r_bounds["center_y"] > 3.0 and r_bounds["extent_y"] > 3.0, (
        f"FATAL: Robot mesh is NOT upright in Unity Y-up space! Got {r_bounds}"
    )
    assert vh_bounds["extent_z"] > 3.0, (
        f"FATAL: Vehicle mesh is NOT horizontal along Z! Got {vh_bounds}"
    )

    # 5. CAB remap setup
    old_cab = "CAB-prowlgskabam000112233445566"
    for obj in g_env.objects:
        if hasattr(obj, "assets_file") and getattr(obj.assets_file, "name", "").startswith("CAB-"):
            old_cab = obj.assets_file.name
            break
    new_cab = "CAB-strongarmgskabam00011223344"
    print(f"[*] Remapping CAB: {old_cab} -> {new_cab}")

    # 6. Processed 2048x2048 Atlases
    tex_dir = root / "toolchain" / "unity_build_project" / "Assets" / "Strongarm"
    tex_diffuse = tex_dir / "cha_strongarm_main_a.png"
    tex_normal = tex_dir / "cha_strongarm_main_NM.png"
    tex_raoe = tex_dir / "cha_strongarm_main_tform_misc_RAOE.png"
    vh_diffuse = tex_dir / "cha_strongarm_vh_a.png"
    vh_normal = tex_dir / "cha_strongarm_vh_NM.png"

    for req_tex in (tex_diffuse, tex_normal, tex_raoe, vh_diffuse, vh_normal):
        if not req_tex.is_file():
            raise FileNotFoundError(f"Missing processed texture: {req_tex}")

    # 7. Apply object replacements across the AssetBundle
    replaced_robot = False
    replaced_vh = False
    routed_robot_smrs = 0
    routed_vh_smrs = 0
    rewired_victory_clips = 0

    for obj in g_env.objects:
        if obj.type.name == "Mesh":
            m_tree = obj.read_typetree()
            m_name = m_tree.get("m_Name")
            if m_name == "cha_prowl_gs_deluxe2016_00":
                replace_str_in_tree(robot_mesh_copy, old_cab, new_cab)
                obj.save_typetree(robot_mesh_copy)
                replaced_robot = True
                print("[✓] Replaced cha_prowl_gs_deluxe2016_00 with Strongarm Robot Mesh!")
            elif m_name == "cha_prowl_gs_deluxe2016_01":
                replace_str_in_tree(vh_mesh_copy, old_cab, new_cab)
                obj.save_typetree(vh_mesh_copy)
                replaced_vh = True
                print("[✓] Replaced cha_prowl_gs_deluxe2016_01 with Strongarm Vehicle Mesh!")
            else:
                replace_str_in_tree(m_tree, old_cab, new_cab)
                obj.save_typetree(m_tree)

        elif obj.type.name == "SkinnedMeshRenderer":
            smr = obj.read_typetree()
            go_id = smr.get("m_GameObject", {}).get("m_PathID")
            go_name = go_dict.get(go_id, {}).get("m_Name", "")
            tr_id_self = go_to_tr.get(go_id)
            is_p1 = tr_id_self in p1_tr_set
            pref_tr = p1_transforms if is_p1 else p2_transforms
            pref_label = "Prefab 1 (Showcase)" if is_p1 else "Prefab 2 (Combat _lw)"

            if len(smr.get("m_Bones", [])) == 50:
                smr["m_Bones"] = [
                    {"m_FileID": 0, "m_PathID": pref_tr.get(bname, pref_tr["Hips"])}
                    for bname in prowl_smr_bones
                ]
                smr["m_RootBone"] = {"m_FileID": 0, "m_PathID": pref_tr["Hips"]}
                if prowl_robot_smr_aabb:
                    smr["m_AABB"] = copy.deepcopy(prowl_robot_smr_aabb)
                smr["m_Materials"] = [{"m_FileID": 0, "m_PathID": MAIN_MAT_PID}]
                replace_str_in_tree(smr, old_cab, new_cab)
                obj.save_typetree(smr)
                routed_robot_smrs += 1
                print(f"[✓] Re-routed 50-bone Robot SMR in {pref_label} -> Material {MAIN_MAT_PID}")
            elif len(smr.get("m_Bones", [])) == 26:
                smr["m_Bones"] = [
                    {"m_FileID": 0, "m_PathID": pref_tr.get(bname, pref_tr.get("transformed", pref_tr["Hips"]))}
                    for bname in prowl_vh_bones
                ]
                if prowl_vh_smr_aabb:
                    smr["m_AABB"] = copy.deepcopy(prowl_vh_smr_aabb)
                smr["m_Materials"] = [{"m_FileID": 0, "m_PathID": VH_MAT_PID}]
                replace_str_in_tree(smr, old_cab, new_cab)
                obj.save_typetree(smr)
                routed_vh_smrs += 1
                print(f"[✓] Re-routed 26-bone Vehicle SMR in {pref_label} -> Material {VH_MAT_PID}")
            else:
                # Keep weapons enabled & untouched
                replace_str_in_tree(smr, old_cab, new_cab)
                obj.save_typetree(smr)
                print(f"[✓] Preserved Weapon/Accessory SMR ({go_name}) in {pref_label}")

        elif obj.type.name == "Material":
            mat = obj.read_typetree()
            if obj.path_id == MAIN_MAT_PID:
                tune_kabam_pbr_material(
                    mat, TEX_MAIN_A_PID, TEX_MAIN_NM_PID, TEX_MAIN_RAOE_PID,
                    metallic_range=0.22, roughness_range=0.90,
                    raoe_scale=(1.0, 1.0), raoe_offset=(0.0, 0.0),
                    albedo_tint=1.0, overbright=16.0
                )
                replace_str_in_tree(mat, old_cab, new_cab)
                obj.save_typetree(mat)
                print("[✓] Tuned Robot Main Material (full 1:1 UV scale, Vibrant Car-Paint PBR + Optics)")
            elif obj.path_id in (VH_MAT_PID, VH_MAT_PID_ALT):
                tune_kabam_pbr_material(
                    mat, TEX_VH_A_PID, TEX_VH_NM_PID, TEX_VH_RAOE_PID,
                    metallic_range=0.14, roughness_range=0.85,
                    raoe_scale=(0.25, 0.25), raoe_offset=(0.75, 0.0),
                    albedo_tint=1.0, overbright=16.0
                )
                replace_str_in_tree(mat, old_cab, new_cab)
                obj.save_typetree(mat)
                print(f"[✓] Tuned Vehicle Material PID {obj.path_id} (RAOE tiled at bottom-right [0.75..1.0, 0.0..0.25])")
            else:
                replace_str_in_tree(mat, old_cab, new_cab)
                obj.save_typetree(mat)

        elif obj.type.name == "Texture2D":
            t_tree = obj.read_typetree()
            t_name = t_tree.get("m_Name", "")
            if t_name == "cha_prowl_gs_deluxe2016_main_a":
                tex = obj.read()
                tex.image = load_opaque_rgba(tex_diffuse)
                tex.save()
                print(f"[✓] Injected 2048x2048 opaque Robot Diffuse -> {t_name}")
            elif t_name == "main_NM":
                tex = obj.read()
                tex.image = Image.open(tex_normal).convert("RGB")
                tex.save()
                print(f"[✓] Injected 2048x2048 Kabam Robot Normal (NM.B=Metallic) -> {t_name}")
            elif t_name == "main_tform_misc_RAOE":
                tex = obj.read()
                tex.image = Image.open(tex_raoe).convert("RGB")
                tex.save()
                print(f"[✓] Injected 2048x2048 Unified RGB RAOE (Robot+Vehicle) -> {t_name}")
            elif t_name == "tform_misc_A":
                tex = obj.read()
                tex.image = load_opaque_rgba(vh_diffuse)
                tex.save()
                print(f"[✓] Injected 2048x2048 opaque Vehicle Diffuse -> {t_name}")
            elif t_name == "tform_misc_NM":
                tex = obj.read()
                tex.image = Image.open(vh_normal).convert("RGB")
                tex.save()
                print(f"[✓] Injected 2048x2048 Kabam Vehicle Normal (NM.B=Metallic) -> {t_name}")
            else:
                replace_str_in_tree(t_tree, old_cab, new_cab)
                obj.save_typetree(t_tree)

        elif obj.type.name == "AnimatorOverrideController":
            aoc = obj.read_typetree()
            aoc_name = aoc.get("m_Name", "")
            if "fight" in aoc_name.lower():
                for pair in aoc.get("m_Clips", []):
                    orig_pid = pair.get("m_OriginalClip", {}).get("m_PathID", 0)
                    if orig_pid == 3642901185112467297:  # char_victory
                        pair["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": 5357267963671096457}
                        rewired_victory_clips += 1
                        print("[✓] Rewired char_victory -> Ultramagnus_Normal_victory (PID 5357267963671096457)")
                    elif orig_pid == -4048722777385356729:  # char_victory_idle
                        pair["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": 1518602965279940590}
                        rewired_victory_clips += 1
                        print("[✓] Rewired char_victory_idle -> Ultramagnus_Normal_victory_idle (PID 1518602965279940590)")
                replace_str_in_tree(aoc, old_cab, new_cab)
                obj.save_typetree(aoc)
            else:
                replace_str_in_tree(aoc, old_cab, new_cab)
                obj.save_typetree(aoc)

        elif obj.type.name == "AssetBundle":
            ab = obj.read_typetree()
            new_container = []
            for item in ab.get("m_Container", []):
                first = item[0]
                if isinstance(first, str) and "prowl_gs_deluxe2016" in first:
                    first = first.replace("prowl_gs_deluxe2016", "strongarm_gs")
                if isinstance(item, tuple):
                    new_container.append((first, item[1]))
                elif isinstance(item, list):
                    item[0] = first
                    new_container.append(item)
                else:
                    new_container.append(item)
            ab["m_Container"] = new_container

            # Keep m_PreloadTable synchronized with Ultra Magnus victory clips & VictoryStagePrefab
            for p_entry in ab.get("m_PreloadTable", []):
                fid = p_entry.get("m_FileID")
                pid = p_entry.get("m_PathID")
                if fid == 2 and pid == -2951149380490677767:
                    p_entry["m_PathID"] = 5357267963671096457
                elif fid == 2 and pid == -9154018769279338152:
                    p_entry["m_PathID"] = 1518602965279940590
                elif fid == 7 and pid == 3984080292617428280:
                    p_entry["m_PathID"] = -902189099669460623

            replace_str_in_tree(ab, old_cab, new_cab)
            obj.save_typetree(ab)
            print(f"[✓] Updated AssetBundle m_Container prefabs & PreloadTable for strongarm_gs")

        elif obj.type.name == "MonoBehaviour":
            mb = obj.read_typetree()
            if "VictoryStagePrefab" in mb:
                vs = mb["VictoryStagePrefab"]
                if vs.get("m_FileID") == 7 and vs.get("m_PathID") == 3984080292617428280:
                    vs["m_PathID"] = -902189099669460623  # TFormStage_Brute_Victory (Ultra Magnus stage!)
                    print(f"[✓] Redirected PlayerReferences.VictoryStagePrefab (PID {obj.path_id}) -> TFormStage_Brute_Victory")
            replace_str_in_tree(mb, old_cab, new_cab)
            obj.save_typetree(mb)

        elif obj.type.name == "GameObject":
            # Keep original Root GO names (Prowl_GS_Deluxe2016 / _lw) so MatineeData hierarchy paths remain 100% valid!
            tree = obj.read_typetree()
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)

        else:
            try:
                tree = obj.read_typetree()
                replace_str_in_tree(tree, old_cab, new_cab)
                obj.save_typetree(tree)
            except Exception:
                pass

    assert replaced_robot and replaced_vh, "Failed to replace both Robot and Vehicle meshes!"
    assert routed_robot_smrs == 2 and routed_vh_smrs == 2, f"Expected 2 Robot SMRs & 2 Vehicle SMRs, got {routed_robot_smrs} & {routed_vh_smrs}!"
    assert rewired_victory_clips >= 2, f"Expected 2 rewired victory clips, got {rewired_victory_clips}!"

    bf = list(g_env.files.values())[0]
    new_files = {}
    for subfname, subf in bf.files.items():
        new_subfname = subfname.replace(old_cab, new_cab)
        if hasattr(subf, "name"):
            subf.name = new_subfname
        new_files[new_subfname] = subf
    bf.files = new_files

    print(f"[*] Saving LZ4-compressed AssetBundle to {output_bundle_path}...")
    with open(output_bundle_path, "wb") as f:
        f.write(bf.save(packer="lz4"))

    size_mb = output_bundle_path.stat().st_size / (1024 * 1024)
    print(f"[SUCCESS] Strongarm AssetBundle synthesized: {output_bundle_path} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    generate_bundle()
