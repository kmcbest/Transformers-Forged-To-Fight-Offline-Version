#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_breakdown_assets.py

Stage 4 Production AssetBundle Grafting for Decepticon Breakdown (打击):
Faction: Decepticon (霸天虎 / 飞虎队)
Class: Scout (scou)

1. 3D Model & PBR Textures (Transformers: Alliance grafted onto Sideswipe 80-bone rig):
   - Robot 00 (80 bones, Track A articulated open-and-closed hands + soft knuckle blend, Symbol_DC01 on Spine1 chest)
   - Vehicle 01 (34 bones, Lamborghini Countach chassis + Symbol_DC02 on hood, rigidly bound to chop2_hip_center)
   - Left-Hand Pistol (cha_sideswipe_gs_deluxe2008_00_wpns_pistol_left aligned to Breakdown_Weapon)
   - Sideswipe shoulder rocket/base renderers silenced cleanly (SMR disabled + Transform scale 0.0001 + PropsController cleared)
   - 2048x2048 Main PBR + 512x512 Emblem SubMesh 1 + 1024x1024 Weapon PBR
2. Combat Animation & Moveset Grafting (Preserved):
   - Normal attacks (Light 1..4, Medium 1..2, Heavy, Ranged Left Gun): Sideswipe (Preserved)
   - S1: Movie Bumblebee (bumble_bee_attackSpecial_01 / move_bumblebee_special_01)
   - S2: Starscream (starscream_gs_attackSpecial_02_stomp / move_starscream_special_02)
   - S3: Sideswipe (sideswipe_attackSpecial_03 / move_sideswipe_special_03 Preserved)
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import argparse
import copy
import io
import zipfile
from collections import deque
from pathlib import Path
from PIL import Image

try:
    import UnityPy
    from UnityPy.enums import TextureFormat
except ImportError:
    print("Error: UnityPy is required. Install it using: pip install UnityPy lz4 pillow numpy")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
BD_DIR = ROOT / "3rd-party-models" / "Breakdown"
MESH_BUNDLE = BD_DIR / "04_unity_bundles" / "breakdown_mesh.assetbundle"
TEX_DIR = BD_DIR / "02_textures"

BOT_ID = "breakdown_gs"
NEW_CAB = "CAB-breakdown2016gs00001122334455"

# Sideswipe donor Mesh / Texture / Material / SMR PIDs
MESH_ROBOT_PID = -296815002598429789      # cha_sideswipe_GS_Deluxe2008_00 (80 bones)
MESH_VEH_PID = 5915794594068324911        # cha_sideswipe_GS_Deluxe2008_01 (34 bones)
MESH_GUN_L_PID = 4042796522768831175      # cha_sideswipe_gs_deluxe2008_00_wpns_pistol_left (1 bone)

TEX_MAIN_DIFF_PID = -340194034951253890   # cha_sideswipe_gs_deluxe2008_main_a
TEX_MAIN_NM_PID = -518961258100061740     # main_NM (NM.B = Kabam metallic)
TEX_MAIN_RAOE_PID = -6916311576766345055  # main_tform_misc_RAOE (RGB24)

TEX_SYM_DIFF_PID = 3986449260907600820    # tform_misc_A -> dedicated SubMesh 1 Decepticon badge
TEX_SYM_NM_PID = 8338546132169352038      # tform_misc_NM

TEX_WPNS_DIFF_PID = -2408903945301852422  # cha_sideswipe_gs_deluxe2008_wpns_a
TEX_WPNS_NM_PID = 3059252300645484932     # wpns_NM
TEX_WPNS_RAOE_PID = -5887805459847094493  # wpns_RAOE (RGB24)

MAT_MAIN_PID = 8880514616582961428        # Main PBR material (SubMesh 0)
MAT_SYM_PID = -1848679255853977883        # SubMesh 1 Decepticon emblem material
MAT_UNUSED_MISC_PID = -230865434415886343 # Unused Sideswipe misc material
MAT_WPNS_PID = 3322655671676547520        # Weapons material

SMR_ROBOT_PIDS = (-3871762863306436332, -2890038130123251469)
SMR_VEH_PIDS = (8417436380511668201, 9069484767575937559)
SMR_GUN_PIDS = (-7259636231801627531, -678426303063061739)
SMR_ROCKET_PIDS = (
    -9113075504956289866, 3432725126339371749,
    -4307220915480615793, -4146541590697296145, -741273414703157834,
    2985735050426107028, 4555079036733808051, 6496817595514861342,
    6973592436609535003, 8631914145074938292,
)


def iter_pptrs_in_tree(node):
    if isinstance(node, dict):
        if "m_FileID" in node and "m_PathID" in node:
            yield node
        else:
            for v in node.values():
                yield from iter_pptrs_in_tree(v)
    elif isinstance(node, (list, tuple)):
        for x in node:
            yield from iter_pptrs_in_tree(x)


def collect_closure(sf, root_pids):
    visited = set()
    all_pptrs = set()
    queue = deque()
    for r in root_pids:
        all_pptrs.add((0, r))
        visited.add(r)
        queue.append(r)
    while queue:
        cur = queue.popleft()
        obj = sf.objects.get(cur)
        if obj is None:
            continue
        try:
            tree = obj.read_typetree()
        except Exception:
            continue
        for pptr in iter_pptrs_in_tree(tree):
            fid, tpid = int(pptr.get("m_FileID", 0)), int(pptr.get("m_PathID", 0))
            if tpid == 0:
                continue
            all_pptrs.add((fid, tpid))
            if fid == 0 and tpid not in visited:
                visited.add(tpid)
                queue.append(tpid)
    return visited, all_pptrs


def replace_str_in_tree(tree_obj, old_s, new_s):
    if isinstance(tree_obj, dict):
        for k, v in tree_obj.items():
            if isinstance(v, str) and (old_s in v or old_s.lower() in v.lower()):
                tree_obj[k] = v.replace(old_s, new_s).replace(old_s.lower(), new_s.lower())
            else:
                replace_str_in_tree(v, old_s, new_s)
    elif isinstance(tree_obj, list):
        for idx, item in enumerate(tree_obj):
            if isinstance(item, str) and (old_s in item or old_s.lower() in item.lower()):
                tree_obj[idx] = item.replace(old_s, new_s).replace(old_s.lower(), new_s.lower())
            else:
                replace_str_in_tree(item, old_s, new_s)


def patch_kabam_character_mat(mat_tt: dict, tex_overrides: dict, custom_floats: dict = None, custom_colors: dict = None):
    old_envs = mat_tt.get("m_SavedProperties", {}).get("m_TexEnvs", [])
    new_envs = []
    for item in old_envs:
        if isinstance(item, (tuple, list)) and len(item) == 2:
            prop_name, prop_data = item
            if prop_name in tex_overrides:
                override_pid = tex_overrides[prop_name]
                if override_pid is not None:
                    prop_data["m_Texture"] = {"m_FileID": 0, "m_PathID": override_pid}
                prop_data["m_Scale"] = {"x": 1.0, "y": 1.0}
                prop_data["m_Offset"] = {"x": 0.0, "y": 0.0}
            new_envs.append((prop_name, prop_data))
    mat_tt["m_SavedProperties"]["m_TexEnvs"] = new_envs

    float_overrides = {
        "_Mode": 3.0,
        "_ZWrite": 1.0,
        "_metallic_range": 0.0,
        "_metallic_toggle": 0.0,
        "_roughness_range": 0.85,
        "_clearcoat_reflectance_range": 0.08,
        "_emissive_range": 0.0,
        "_emissive_none": 0.0,
        "_emissive_overbright_range": 16.0,
    }
    if custom_floats:
        float_overrides.update(custom_floats)

    floats = mat_tt["m_SavedProperties"]["m_Floats"]
    existing_keys = {k for k, _ in floats}
    new_floats = [(k, float_overrides[k] if k in float_overrides else v) for k, v in floats]
    for k, v in float_overrides.items():
        if k not in existing_keys:
            new_floats.append((k, v))
    mat_tt["m_SavedProperties"]["m_Floats"] = new_floats

    color_overrides = {
        "_Color": {"r": 0.92, "g": 0.92, "b": 0.92, "a": 1.0},
        "_base_col": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
        "_emissive_intensity_col": {"r": 1.0, "g": 0.06, "b": 0.06, "a": 0.0},
    }
    if custom_colors:
        color_overrides.update(custom_colors)

    colors = mat_tt["m_SavedProperties"]["m_Colors"]
    mat_tt["m_SavedProperties"]["m_Colors"] = [
        (k, dict(color_overrides[k]) if k in color_overrides else v) for k, v in colors
    ]


def generate_breakdown_assets(apk_path: str | None = None, output_dir: str = "assets_redeco") -> None:
    out_dir = Path(output_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    assert MESH_BUNDLE.is_file(), f"Missing Stage 3 mesh bundle: {MESH_BUNDLE}"
    for tf in (
        "cha_breakdown_main_Diffuse.png", "cha_breakdown_main_Normal.png", "cha_breakdown_main_RAOE.png",
        "cha_breakdown_sym_Diffuse.png", "cha_breakdown_sym_Normal.png",
        "cha_breakdown_wpns_Diffuse.png", "cha_breakdown_wpns_Normal.png", "cha_breakdown_wpns_RAOE.png",
    ):
        assert (TEX_DIR / tf).is_file(), f"Missing texture: {TEX_DIR / tf}"

    extracted_candidates = [
        ROOT / "extracted_apk" / "assets" / "assetpack",
        Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack"),
    ]

    def load_bundle(rel_path: str) -> bytes:
        for base in extracted_candidates:
            if (base / rel_path).is_file():
                return (base / rel_path).read_bytes()
        if apk_path and Path(apk_path).is_file():
            with zipfile.ZipFile(apk_path, "r") as z:
                return z.read(f"assets/assetpack/{rel_path}")
        raise FileNotFoundError(f"Cannot find {rel_path} in {extracted_candidates} or {apk_path}")

    print("[*] Loading component assetbundles & Stage 3 Breakdown mesh bundle...")
    sideswipe_bytes = load_bundle("sideswipe_gs_odr/sideswipe_gs.assetbundle")
    procedural_bytes = load_bundle("characters_procedural_odr/character_anim_procedural.assetbundle")
    thundercracker_bytes = load_bundle("thundercracker_gs_leader2015_odr/thundercracker_gs_leader2015.assetbundle")

    print("[*] Parsing source bundles...")
    s_env = UnityPy.load(sideswipe_bytes)
    proc_env = UnityPy.load(procedural_bytes)
    tc_env = UnityPy.load(thundercracker_bytes)
    mesh_env = UnityPy.load(str(MESH_BUNDLE))

    bd_meshes = {}
    for obj in mesh_env.objects:
        if obj.type.name == "Mesh":
            tt = obj.read_typetree()
            bd_meshes[tt["m_Name"]] = tt
    for req in (
        "cha_sideswipe_GS_Deluxe2008_00",
        "cha_sideswipe_GS_Deluxe2008_01",
        "cha_sideswipe_gs_deluxe2008_00_wpns_pistol_left",
    ):
        assert req in bd_meshes, f"Missing '{req}' in {MESH_BUNDLE}: {list(bd_meshes.keys())}"

    # 1. Extract required external AnimationClips (Movie Bumblebee S1 + Starscream S2 Stomp)
    print("[*] Extracting external combat animation clips...")
    clip_s1 = next(
        (obj.read_typetree() for obj in proc_env.objects if obj.path_id == -5764875969571546881 and obj.type.name == "AnimationClip"),
        None,
    )
    assert clip_s1 is not None, "Missing Movie Bumblebee S1 clip!"
    clip_s1["m_Name"] = "breakdown_GS_attackSpecial_01"

    clip_s2 = next(
        (obj.read_typetree() for obj in tc_env.objects if obj.path_id == 6867043127549743747 and obj.type.name == "AnimationClip"),
        None,
    )
    assert clip_s2 is not None, "Missing Starscream S2 clip!"
    clip_s2["m_Name"] = "breakdown_GS_attackSpecial_02"

    # 2. Re-wire Sideswipe donor CAB & inject AnimationClips
    s_asset = list(s_env.assets)[0]
    obj_map = {o.path_id: o for o in s_env.objects}

    cab_files = [k for k in s_env.file.files.keys() if k.lower().startswith("cab-") and "." not in k]
    assert cab_files, "Could not find CAB file in Sideswipe donor bundle!"
    old_cab = cab_files[0]
    old_cab_low = old_cab.lower()
    new_cab_low = NEW_CAB.lower()
    print(f"[*] Remapping CAB: {old_cab} -> {NEW_CAB}")

    PID_S1 = 991001
    PID_S2 = 991002
    new_clips = [(PID_S1, clip_s1), (PID_S2, clip_s2)]

    template_clip = next(o for o in s_asset.objects.values() if o.type.name == "AnimationClip")
    for pid, ctree in new_clips:
        new_obj = copy.copy(template_clip)
        new_obj.path_id = pid
        replace_str_in_tree(ctree, old_cab, new_cab_low)
        new_obj.save_typetree(ctree)
        s_asset.objects[pid] = new_obj
    print(f"[+] Injected {len(new_clips)} custom combat AnimationClips into Breakdown bundle")

    # 3. Graft 3D Alliance Meshes (Robot 00, Countach 01, Left-Hand Rifle) cleanly
    mesh_specs = (
        (MESH_ROBOT_PID, "cha_sideswipe_GS_Deluxe2008_00", "cha_breakdown_gs_00", 3.0),
        (MESH_VEH_PID, "cha_sideswipe_GS_Deluxe2008_01", "cha_breakdown_gs_01", 0.5),
        (MESH_GUN_L_PID, "cha_sideswipe_gs_deluxe2008_00_wpns_pistol_left", "cha_breakdown_gs_wpns_pistol_left", -10.0),
    )
    for dst_pid, src_name, dst_name, y_floor in mesh_specs:
        src_tt = copy.deepcopy(bd_meshes[src_name])
        dst_obj = obj_map[dst_pid]
        dst_tt = dst_obj.read_typetree()

        keep_hashes = list(dst_tt["m_BoneNameHashes"])
        keep_root_hash = int(dst_tt["m_RootBoneNameHash"])
        assert len(src_tt["m_BindPose"]) == len(keep_hashes), (
            f"{src_name} bindpose len {len(src_tt['m_BindPose'])} != donor hashes len {len(keep_hashes)}"
        )
        c_y = src_tt["m_LocalAABB"]["m_Center"]["y"]
        assert c_y > y_floor, f"{src_name} center.y={c_y:.3f} failed height guard (>{y_floor})"

        dst_tt["m_Name"] = dst_name
        for field in (
            "m_SubMeshes", "m_Shapes", "m_BindPose", "m_BonesAABB",
            "m_VariableBoneCountWeights", "m_MeshCompression", "m_IndexFormat",
            "m_IndexBuffer", "m_VertexData", "m_CompressedMesh",
            "m_LocalAABB", "m_StreamData",
        ):
            dst_tt[field] = src_tt[field]
        dst_tt["m_BoneNameHashes"] = keep_hashes
        dst_tt["m_RootBoneNameHash"] = keep_root_hash
        dst_tt["m_IsReadable"] = True
        dst_tt["m_KeepVertices"] = True
        dst_tt["m_KeepIndices"] = True
        dst_tt["m_MeshUsageFlags"] = 1
        dst_obj.save_typetree(dst_tt)
        print(f"[✓] Grafted Mesh '{dst_name}': PID={dst_pid}, verts={src_tt['m_VertexData']['m_VertexCount']}, bones={len(keep_hashes)}, submeshes={len(dst_tt['m_SubMeshes'])}")

    # 4. Inject 2048 Main + 512 Sym + 1024 Weapon PBR textures
    def set_texture(obj, img_path: Path, name: str, is_raoe: bool = False):
        t = obj.read()
        img = Image.open(img_path)
        if is_raoe:
            img = img.convert("RGB")
            target_fmt = TextureFormat.RGB24
        else:
            img = img.convert("RGBA")
            r, g, b, _ = img.split()
            img = Image.merge("RGBA", (r, g, b, Image.new("L", img.size, 255)))
            target_fmt = TextureFormat.RGBA32

        t.m_Name = name
        t.m_StreamData.offset = 0
        t.m_StreamData.size = 0
        t.m_StreamData.path = ""
        t.set_image(img, target_format=target_fmt, mipmap_count=1)
        t.save()
        print(f"  [Tex] {obj.path_id}: '{name}' {img.size[0]}x{img.size[1]} fmt={int(target_fmt)}")

    print("[*] Injecting Breakdown Main 2048 + Sym 512 + Weapon 1024 PBR textures...")
    set_texture(obj_map[TEX_MAIN_DIFF_PID], TEX_DIR / "cha_breakdown_main_Diffuse.png", "cha_breakdown_main_Diffuse", is_raoe=False)
    set_texture(obj_map[TEX_MAIN_NM_PID], TEX_DIR / "cha_breakdown_main_Normal.png", "cha_breakdown_main_Normal", is_raoe=False)
    set_texture(obj_map[TEX_MAIN_RAOE_PID], TEX_DIR / "cha_breakdown_main_RAOE.png", "cha_breakdown_main_RAOE", is_raoe=True)

    set_texture(obj_map[TEX_SYM_DIFF_PID], TEX_DIR / "cha_breakdown_sym_Diffuse.png", "cha_breakdown_sym_Diffuse", is_raoe=False)
    set_texture(obj_map[TEX_SYM_NM_PID], TEX_DIR / "cha_breakdown_sym_Normal.png", "cha_breakdown_sym_Normal", is_raoe=False)

    set_texture(obj_map[TEX_WPNS_DIFF_PID], TEX_DIR / "cha_breakdown_wpns_Diffuse.png", "cha_breakdown_wpns_Diffuse", is_raoe=False)
    set_texture(obj_map[TEX_WPNS_NM_PID], TEX_DIR / "cha_breakdown_wpns_Normal.png", "cha_breakdown_wpns_Normal", is_raoe=False)
    set_texture(obj_map[TEX_WPNS_RAOE_PID], TEX_DIR / "cha_breakdown_wpns_RAOE.png", "cha_breakdown_wpns_RAOE", is_raoe=True)

    # 5. Patch Main, SubMesh 1 Sym, & Weapon Materials
    main_tex_overrides = {
        "_base_tex": TEX_MAIN_DIFF_PID,
        "_normal_tex": TEX_MAIN_NM_PID,
        "_pbr_composite_tex": TEX_MAIN_RAOE_PID,
    }
    m_obj = obj_map[MAT_MAIN_PID]
    m_tt = m_obj.read_typetree()
    patch_kabam_character_mat(m_tt, main_tex_overrides)
    m_obj.save_typetree(m_tt)

    sym_tex_overrides = {
        "_base_tex": TEX_SYM_DIFF_PID,
        "_normal_tex": TEX_SYM_NM_PID,
        "_pbr_composite_tex": TEX_MAIN_RAOE_PID,
    }
    for mpid in (MAT_SYM_PID, MAT_UNUSED_MISC_PID):
        s_obj = obj_map[mpid]
        s_tt = s_obj.read_typetree()
        patch_kabam_character_mat(
            s_tt,
            sym_tex_overrides,
            custom_floats={"_emissive_overbright_range": 0.0},
            custom_colors={"_emissive_intensity_col": {"r": 0.0, "g": 0.0, "b": 0.0, "a": 0.0}},
        )
        s_obj.save_typetree(s_tt)

    wpn_tex_overrides = {
        "_base_tex": TEX_WPNS_DIFF_PID,
        "_normal_tex": TEX_WPNS_NM_PID,
        "_pbr_composite_tex": TEX_WPNS_RAOE_PID,
    }
    w_obj = obj_map[MAT_WPNS_PID]
    w_tt = w_obj.read_typetree()
    patch_kabam_character_mat(
        w_tt,
        wpn_tex_overrides,
        custom_floats={"_emissive_overbright_range": 0.0},
        custom_colors={"_emissive_intensity_col": {"r": 0.0, "g": 0.0, "b": 0.0, "a": 0.0}},
    )
    w_obj.save_typetree(w_tt)
    print("[✓] Patched Breakdown Main / SubMesh-1 Sym / Weapon Materials")

    # 6. Configure SMRs (2 SubMeshes on Robot/Veh: [Main, Sym], 1 SubMesh on Gun) & silence Sideswipe shoulder rockets
    generous_aabb = {"m_Center": {"x": 0.0, "y": 0.0, "z": 0.0}, "m_Extent": {"x": 10.0, "y": 10.0, "z": 10.0}}
    for pid in SMR_ROBOT_PIDS + SMR_VEH_PIDS:
        smr_obj = obj_map[pid]
        smr_tt = smr_obj.read_typetree()
        smr_tt["m_Materials"] = [
            {"m_FileID": 0, "m_PathID": MAT_MAIN_PID},
            {"m_FileID": 0, "m_PathID": MAT_SYM_PID},
        ]
        smr_tt["m_AABB"] = generous_aabb
        smr_tt["m_UpdateWhenOffscreen"] = True
        smr_obj.save_typetree(smr_tt)

    for pid in SMR_GUN_PIDS:
        smr_obj = obj_map[pid]
        smr_tt = smr_obj.read_typetree()
        smr_tt["m_Materials"] = [{"m_FileID": 0, "m_PathID": MAT_WPNS_PID}]
        smr_tt["m_AABB"] = generous_aabb
        smr_tt["m_UpdateWhenOffscreen"] = True
        smr_obj.save_typetree(smr_tt)

    hidden_transform_pids = set()
    for pid in SMR_ROCKET_PIDS:
        smr_obj = obj_map.get(pid)
        if smr_obj is None:
            continue
        smr_tt = smr_obj.read_typetree()
        smr_tt["m_Enabled"] = False
        smr_tt["m_Materials"] = []
        go_pid = smr_tt["m_GameObject"]["m_PathID"]
        smr_obj.save_typetree(smr_tt)
        go_obj = obj_map.get(go_pid)
        if go_obj:
            go_tt = go_obj.read_typetree()
            for comp in go_tt.get("m_Component", []):
                comp_pid = comp.get("component", {}).get("m_PathID")
                if comp_pid in obj_map and obj_map[comp_pid].type.name == "Transform":
                    hidden_transform_pids.add(comp_pid)
    for tpid in hidden_transform_pids:
        t_obj = obj_map[tpid]
        t_tt = t_obj.read_typetree()
        t_tt["m_LocalScale"] = {"x": 0.0001, "y": 0.0001, "z": 0.0001}
        t_obj.save_typetree(t_tt)
    print(f"[✓] Updated Robot/Veh/Gun SMRs & silenced {len(SMR_ROCKET_PIDS)} donor shoulder rocket renderers")

    # 7. Configure Fight AOC, MoveSet, PropsController, Container, & CAB string remapping
    replaced_pids = {
        MESH_ROBOT_PID, MESH_VEH_PID, MESH_GUN_L_PID,
        TEX_MAIN_DIFF_PID, TEX_MAIN_NM_PID, TEX_MAIN_RAOE_PID,
        TEX_SYM_DIFF_PID, TEX_SYM_NM_PID,
        TEX_WPNS_DIFF_PID, TEX_WPNS_NM_PID, TEX_WPNS_RAOE_PID,
    }
    injected_set = {PID_S1, PID_S2}
    for obj in list(s_env.objects):
        if obj.path_id == 6324095378042686150 and obj.type.name == "AnimatorOverrideController":
            tree = obj.read_typetree()
            clips = tree.get("m_Clips", [])
            clips[4]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_S1}
            clips[5]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_S2}
            tree["m_Clips"] = clips
            replace_str_in_tree(tree, old_cab, new_cab_low)
            obj.save_typetree(tree)
            print("[+] Configured Breakdown Fight AOC (S1=Movie Bumblebee, S2=Starscream Stomp, S3/Normals=Sideswipe)")

        elif obj.path_id == -7374307588374362381 and obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            moves = tree.get("_moves", [])
            moves[6]["_name"] = "move_bumblebee_special_01"
            moves[6]["_asset"] = {"m_FileID": 3, "m_PathID": -2438169768979208740}
            moves[7]["_name"] = "move_starscream_special_02"
            moves[7]["_asset"] = {"m_FileID": 3, "m_PathID": -4550375753452909921}
            tree["_moves"] = moves
            replace_str_in_tree(tree, old_cab, new_cab_low)
            obj.save_typetree(tree)
            print("[+] Configured Breakdown MoveSet (moves[6]=Bumblebee S1, moves[7]=Starscream S2)")

        elif obj.path_id in (-8328346350009699883, 5273775749855714258) and obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            props = tree.get("_props", {})
            keys = props.get("_serializedKeys", [])
            values = props.get("_serializedValues", [])
            for k, v in zip(keys, values):
                if k in ("rocketBase", "rocket") and isinstance(v, dict):
                    v["_renderers"] = []
            replace_str_in_tree(tree, old_cab, new_cab_low)
            obj.save_typetree(tree)

        elif obj.type.name == "AssetBundle":
            tree = obj.read_typetree()
            ab_name = f"data/{BOT_ID}_odr/{BOT_ID}.assetbundle"
            tree["m_Name"] = ab_name
            tree["m_AssetBundleName"] = ab_name
            new_container = []
            for item in tree.get("m_Container", []):
                path_str = item[0].replace("sideswipe_gs", BOT_ID).replace("Sideswipe_GS", BOT_ID)
                new_container.append([path_str, item[1]])
            tree["m_Container"] = new_container
            replace_str_in_tree(tree, old_cab, new_cab_low)
            obj.save_typetree(tree)

        elif obj.path_id in injected_set:
            continue

        elif obj.type.name in ("AudioClip", "Texture2D", "Mesh") and obj.path_id not in replaced_pids:
            tree = obj.read_typetree()
            replace_str_in_tree(tree, old_cab, new_cab_low)
            obj.save_typetree(tree)

        elif obj.type.name in ("AnimatorController", "AnimatorOverrideController", "MonoBehaviour", "GameObject"):
            try:
                tree = obj.read_typetree()
                replace_str_in_tree(tree, old_cab, new_cab_low)
                obj.save_typetree(tree)
            except Exception:
                pass

    # 8. Flush & rebuild exact AssetBundle m_PreloadTable slices & CAB filenames
    print("[*] Rebuilding exact AssetBundle m_PreloadTable & CAB filenames...")
    raw_saved = s_env.file.save(packer="none")
    s_env = UnityPy.load(io.BytesIO(raw_saved))
    sf = [f for f in s_env.file.files.values() if hasattr(f, "objects")][0]
    ab_obj = next(o for o in sf.objects.values() if o.type.name == "AssetBundle")
    ab_tree = ab_obj.read_typetree()

    new_preload = []
    for cname, cinfo in ab_tree.get("m_Container", []):
        rpid = int(cinfo["asset"]["m_PathID"])
        _, closure_pptrs = collect_closure(sf, [rpid])
        sorted_pptrs = sorted(closure_pptrs)
        cinfo["preloadIndex"] = len(new_preload)
        cinfo["preloadSize"] = len(sorted_pptrs)
        for fid, pid in sorted_pptrs:
            new_preload.append({"m_FileID": fid, "m_PathID": pid})
        print(f"  [Preload Slice] {cname}: size={len(sorted_pptrs)} (index={cinfo['preloadIndex']})")
    ab_tree["m_PreloadTable"] = new_preload
    ab_obj.save_typetree(ab_tree)

    new_files = {}
    for subfname, subf in s_env.file.files.items():
        nk = subfname.replace(old_cab, NEW_CAB).replace(old_cab_low, new_cab_low)
        if hasattr(subf, "name") and isinstance(subf.name, str):
            subf.name = subf.name.replace(old_cab, NEW_CAB).replace(old_cab_low, new_cab_low)
        new_files[nk] = subf
    s_env.file.files = new_files

    target_bundle = out_dir / f"{BOT_ID}.assetbundle"
    target_bundle.write_bytes(s_env.file.save(packer="lz4"))
    size_mb = target_bundle.stat().st_size / (1024 * 1024)
    print(f"[✓] Saved {target_bundle} ({size_mb:.2f} MB, packer='lz4', CAB={NEW_CAB})")

    # Verify injected animation clips survived serialization intact
    chk_sf = [f for f in s_env.file.files.values() if hasattr(f, "objects")][0]
    s1_tt = chk_sf.objects[PID_S1].read_typetree()
    s2_tt = chk_sf.objects[PID_S2].read_typetree()
    assert s1_tt["m_Name"] == "breakdown_GS_attackSpecial_01", f"Corrupted S1 clip: {s1_tt['m_Name']}"
    assert s2_tt["m_Name"] == "breakdown_GS_attackSpecial_02", f"Corrupted S2 clip: {s2_tt['m_Name']}"
    print(f"[✓] Verified injected clips intact: '{s1_tt['m_Name']}' & '{s2_tt['m_Name']}'")
    print("[+] All Breakdown Stage 4 3D assets successfully generated!")


def main():
    parser = argparse.ArgumentParser(description="Generate Breakdown (打击) Stage 4 3D grafted assetbundle.")
    parser.add_argument("--output", "-o", default="assets_redeco", help="Output directory")
    args = parser.parse_args()
    generate_breakdown_assets(output_dir=args.output)


if __name__ == "__main__":
    main()
