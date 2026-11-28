#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_dragstrip_assets.py

Stage 4 Production AssetBundle Grafting for Decepticon Dragstrip (抢劫):
Class: Warrior (warr)
Faction: Decepticons (霸天虎)

1. 3D Model & PBR Textures (Transformers: Alliance grafted onto Mirage 59-bone rig):
   - Robot 00 (59 bones, Swoosh Track-B symmetrical combat fists, Symbol_DC on LeftArm)
   - Vehicle 01 (30 bones, Unity-baked seamless Tyrrell P34 6-wheel F1 chassis)
   - Dual Purple Blasters (blaster_right & blaster_left forward-aligned to Mirage X=-X)
   - Mirage hologram cube hidden cleanly (SMR disabled + Transform scale 0.0001 + PropsController cleared)
   - 2048x2048 Main PBR + 1024x1024 Weapon PBR (Diffuse + NM.B metallic + RGB24 RAOE)
2. Preserved Combat Animation & Moveset Grafting:
   - Heavy Attack: Cliffjumper (Ironhide_Normal_attackHeavy / move_heavy_cliffjumper_gs_shoot)
   - S1: Mirage (Preserved)
   - S2: Hot Rod (Hotrod_cin_attackSpecial_02 / move_hotrod_special_02)
   - S3: Mirage (Preserved)
   - L1: Jazz L3 (Jazz_GS_attackLight_03_leftKick / move_jazz_attack_light_03)
   - L2: Blaster L2 (blaster_GS_attackLight_02_leftKick / move_blaster_attack_light_02)
   - L3: Blaster L3 (blaster_GS_attackLight_03_rightKick / move_blaster_attack_light_03)
   - L4: Jazz L4 (Jazz_GS_attackLight_04_KickBackFlip / move_jazz_attack_light_04)
   - M1: Cheetor M1 (Cheetor_BW_attackMedium_01_FrontKick / move_cheetor_attack_medium_01)
   - M2: Mirage M2 (Preserved)
   - Ranged Gunshots: Mirage (Preserved)
   - Victory Pose: Mirage's Agile_Backflip_Victory (Preserved)
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
DS_DIR = ROOT / "3rd-party-models" / "DragStrip"
MESH_BUNDLE = DS_DIR / "04_unity_bundles" / "dragstrip_mesh.assetbundle"
TEX_DIR = DS_DIR / "02_textures"

BOT_ID = "dragstrip_gs_deluxe2016"
NEW_CAB = "CAB-dragstrip2016gs00001122334455"

# Mirage donor Mesh / Texture / Material / SMR PIDs
MESH_ROBOT_PID = -7047427799269870338      # cha_mirage_gs_deluxe2016_00 (59 bones)
MESH_VEH_PID = -7919032722081793131        # cha_mirage_gs_deluxe2016_01 (30 bones)
MESH_GUN_R_PID = -708779048876715111       # cha_mirage_gs_deluxe2016_wpns_blaster_right (2 bones)
MESH_GUN_L_PID = 3991515401293144586       # cha_mirage_gs_deluxe2016_wpns_blaster_left (2 bones)

TEX_MAIN_DIFF_PID = 4395477768874757111    # cha_mirage_gs_deluxe2016_main_a
TEX_MAIN_NM_PID = -6978092715990138129     # main_NM (NM.B = Kabam metallic)
TEX_MAIN_RAOE_PID = -850837903824500791    # main_tform_misc_RAOE (RGB24)

TEX_WPNS_DIFF_PID = 5622234077790621728    # cha_mirage_gs_deluxe2016_wpns_a
TEX_WPNS_NM_PID = -2093198935828166547     # wpns_NM (NM.B = Kabam metallic)
TEX_WPNS_RAOE_PID = 6915329565936758037    # wpns_RAOE (RGB24)

MAT_MAIN_PID = 7175098081916666581         # Main robot material
MAT_MISC_PID = -8318600222494959541        # Misc body parts material
MAT_VEH_PID = 3475926521476801325          # Vehicle material
MAT_WPNS_PID = 6410552648699303269         # Weapons material

SMR_ROBOT_PIDS = (-4162633114742165930, -360973636754071276)
SMR_VEH_PIDS = (7623886199718479523, 7962935959443397066)
SMR_GUN_PIDS = (-5139469930961036181, 6504325044332464931, 8763026051381471918, 9151386682529925607)
SMR_CUBE_PIDS = (-842429708391054887, 505331748733393460, 6460812292277991026)


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
        "_emissive_overbright_range": 18.0,
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
        "_Color": {"r": 0.95, "g": 0.95, "b": 0.95, "a": 1.0},
        "_base_col": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
        "_emissive_intensity_col": {"r": 1.0, "g": 0.08, "b": 0.08, "a": 0.0},
    }
    if custom_colors:
        color_overrides.update(custom_colors)

    colors = mat_tt["m_SavedProperties"]["m_Colors"]
    mat_tt["m_SavedProperties"]["m_Colors"] = [
        (k, dict(color_overrides[k]) if k in color_overrides else v) for k, v in colors
    ]


def generate_dragstrip_assets(apk_path: str | None = None, output_dir: str = "assets_redeco") -> None:
    out_dir = Path(output_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    assert MESH_BUNDLE.is_file(), f"Missing Stage 3 mesh bundle: {MESH_BUNDLE}"
    for tf in (
        "cha_dragstrip_main_Diffuse.png", "cha_dragstrip_main_Normal.png", "cha_dragstrip_main_RAOE.png",
        "cha_dragstrip_wpns_Diffuse.png", "cha_dragstrip_wpns_Normal.png", "cha_dragstrip_wpns_RAOE.png",
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

    print("[*] Loading component assetbundles & Stage 3 DragStrip mesh bundle...")
    mirage_bytes = load_bundle("mirage_gs_deluxe2016_odr/mirage_gs_deluxe2016.assetbundle")
    cliff_bytes = load_bundle("cliffjumper_gs_kabam_odr/cliffjumper_gs_kabam.assetbundle")
    hotrod_bytes = load_bundle("hotrod_cin_tlk_odr/hotrod_cin_tlk.assetbundle")
    jazz_bytes = load_bundle("jazz_gs_twm05_odr/jazz_gs_twm05.assetbundle")
    blaster_bytes = load_bundle("blaster_gs_leader2016_odr/blaster_gs_leader2016.assetbundle")
    cheetor_bytes = load_bundle("cheetor_bw_transmetal_odr/cheetor_bw_transmetal.assetbundle")

    print("[*] Parsing source bundles...")
    m_env = UnityPy.load(mirage_bytes)
    c_env = UnityPy.load(cliff_bytes)
    h_env = UnityPy.load(hotrod_bytes)
    j_env = UnityPy.load(jazz_bytes)
    bl_env = UnityPy.load(blaster_bytes)
    ch_env = UnityPy.load(cheetor_bytes)
    mesh_env = UnityPy.load(str(MESH_BUNDLE))

    ds_meshes = {}
    for obj in mesh_env.objects:
        if obj.type.name == "Mesh":
            tt = obj.read_typetree()
            ds_meshes[tt["m_Name"]] = tt
    for req in (
        "cha_mirage_gs_deluxe2016_00",
        "cha_mirage_gs_deluxe2016_01",
        "cha_mirage_gs_deluxe2016_wpns_blaster_right",
        "cha_mirage_gs_deluxe2016_wpns_blaster_left",
    ):
        assert req in ds_meshes, f"Missing '{req}' in {MESH_BUNDLE}: {list(ds_meshes.keys())}"

    # 1. Extract required AnimationClips (preserve existing Dragstrip kick/gunshot combat flow)
    print("[*] Extracting external combat animation clips...")
    clip_heavy = next(
        (obj.read_typetree() for obj in c_env.objects if obj.path_id == -2721040065330547388 and obj.type.name == "AnimationClip"),
        None,
    )
    assert clip_heavy is not None
    clip_heavy["m_Name"] = "dragstrip_Normal_attackHeavy"

    clip_s2 = next(
        (obj.read_typetree() for obj in h_env.objects if obj.path_id == 3923599842407920377 and obj.type.name == "AnimationClip"),
        None,
    )
    assert clip_s2 is not None
    clip_s2["m_Name"] = "dragstrip_Normal_attackSpecial_02"

    clip_l1_jazz = None
    clip_l4_jazz = None
    for obj in j_env.objects:
        if obj.path_id == 6919999024148056483 and obj.type.name == "AnimationClip":
            clip_l1_jazz = obj.read_typetree()
            clip_l1_jazz["m_Name"] = "dragstrip_GS_attackLight_01_kick"
        elif obj.path_id == -491266744809317325 and obj.type.name == "AnimationClip":
            clip_l4_jazz = obj.read_typetree()
            clip_l4_jazz["m_Name"] = "dragstrip_GS_attackLight_04_backflip"

    clip_l2_blaster = None
    clip_l3_blaster = None
    for obj in bl_env.objects:
        if obj.path_id == 2310569694197683561 and obj.type.name == "AnimationClip":
            clip_l2_blaster = obj.read_typetree()
            clip_l2_blaster["m_Name"] = "dragstrip_GS_attackLight_02_kick"
        elif obj.path_id == 285458249171271195 and obj.type.name == "AnimationClip":
            clip_l3_blaster = obj.read_typetree()
            clip_l3_blaster["m_Name"] = "dragstrip_GS_attackLight_03_kick"

    clip_m1_cheetor = next(
        (obj.read_typetree() for obj in ch_env.objects if obj.path_id == -82464947619687576 and obj.type.name == "AnimationClip"),
        None,
    )
    assert clip_m1_cheetor is not None
    clip_m1_cheetor["m_Name"] = "dragstrip_BW_attackMedium_01_frontkick"

    # 2. Re-wire Mirage donor bundle CAB & inject AnimationClips + Projectile entities
    m_asset = list(m_env.assets)[0]
    obj_map = {o.path_id: o for o in m_env.objects}

    cab_files = [k for k in m_env.file.files.keys() if k.lower().startswith("cab-") and "." not in k]
    assert cab_files, "Could not find CAB file in Mirage donor bundle!"
    old_cab = cab_files[0]
    old_cab_low = old_cab.lower()
    new_cab_low = NEW_CAB.lower()
    print(f"[*] Remapping CAB: {old_cab} -> {NEW_CAB}")

    PID_HEAVY = 991001
    PID_S2 = 991002
    PID_L1_JAZZ = 991005
    PID_L2_BLASTER = 991006
    PID_L3_BLASTER = 991007
    PID_L4_JAZZ = 991008
    PID_M1_CHEETOR = 991009

    new_clips = [
        (PID_HEAVY, clip_heavy),
        (PID_S2, clip_s2),
        (PID_L1_JAZZ, clip_l1_jazz),
        (PID_L2_BLASTER, clip_l2_blaster),
        (PID_L3_BLASTER, clip_l3_blaster),
        (PID_L4_JAZZ, clip_l4_jazz),
        (PID_M1_CHEETOR, clip_m1_cheetor),
    ]

    template_clip = next(o for o in m_asset.objects.values() if o.type.name == "AnimationClip")
    for pid, ctree in new_clips:
        new_obj = copy.copy(template_clip)
        new_obj.path_id = pid
        replace_str_in_tree(ctree, old_cab, new_cab_low)
        new_obj.save_typetree(ctree)
        m_asset.objects[pid] = new_obj
    print(f"[+] Injected {len(new_clips)} custom combat AnimationClips into Dragstrip bundle")

    c_asset = list(c_env.assets)[0]
    h_asset = list(h_env.assets)[0]
    tmpl_go = m_asset.objects[8211146528821479566]
    tmpl_tr = m_asset.objects[7833009063040620157]
    tmpl_fire_explode = m_asset.objects[6911381496922764941]
    tmpl_moves = m_asset.objects[4570473581685628392]
    tmpl_prefablist = m_asset.objects[6656473622135015614]
    tmpl_combat = m_asset.objects[-2567301930229054027]

    def get_template(obj_type, tree):
        if obj_type == "GameObject":
            return tmpl_go
        if obj_type == "Transform":
            return tmpl_tr
        if obj_type == "MonoBehaviour":
            script_pid = tree.get("m_Script", {}).get("m_PathID")
            if script_pid == -3660570848581127988:
                return tmpl_fire_explode
            if script_pid == 2297153707519481197:
                return tmpl_moves
            if script_pid == -3815473324432562333:
                return tmpl_prefablist
            if script_pid == 4113389322536752908:
                return tmpl_combat
            raise ValueError(f"Unknown script pid {script_pid}")
        raise ValueError(f"Unknown type {obj_type}")

    cj_proj_pids = [9003878510878022874, -3703404665488950760, 7614484081745325141, -2714705455090383668, -4642064524079818382, 5864972968936471992]
    hr_proj_pids = [-8172610782387618255, 6789086250395783446, 9083784432851756083, -8264554495304631612, -802258416909754905, -2962032538932338988]

    for pid in cj_proj_pids:
        obj = c_asset.objects[pid]
        tree = obj.read_typetree()
        if pid == -2714705455090383668:
            for m in tree.get("_moves", []):
                if m.get("_asset", {}).get("m_FileID") == 6:
                    m["_asset"]["m_FileID"] = 5
        elif pid == -4642064524079818382:
            for item in tree.get("PrefabList", []):
                if item.get("Prefab", {}).get("m_FileID") == 2:
                    item["Prefab"]["m_FileID"] = 3
        tmpl = get_template(obj.type.name, tree)
        new_obj = copy.copy(tmpl)
        new_obj.path_id = pid
        replace_str_in_tree(tree, old_cab, new_cab_low)
        new_obj.save_typetree(tree)
        m_asset.objects[pid] = new_obj

    for pid in hr_proj_pids:
        obj = h_asset.objects[pid]
        tree = obj.read_typetree()
        if pid == -802258416909754905:
            for item in tree.get("PrefabList", []):
                if item.get("Prefab", {}).get("m_FileID") == 1:
                    item["Prefab"]["m_FileID"] = 3
        tmpl = get_template(obj.type.name, tree)
        new_obj = copy.copy(tmpl)
        new_obj.path_id = pid
        replace_str_in_tree(tree, old_cab, new_cab_low)
        new_obj.save_typetree(tree)
        m_asset.objects[pid] = new_obj
    print(f"[+] Injected {len(cj_proj_pids) + len(hr_proj_pids)} projectile objects into Dragstrip bundle")

    # 3. Graft 3D Alliance Meshes (Robot 00, F1 Car 01, Dual Blasters) cleanly
    mesh_specs = (
        (MESH_ROBOT_PID, "cha_mirage_gs_deluxe2016_00", "cha_dragstrip_gs_deluxe2016_00", 3.0),
        (MESH_VEH_PID, "cha_mirage_gs_deluxe2016_01", "cha_dragstrip_gs_deluxe2016_01", 0.5),
        (MESH_GUN_R_PID, "cha_mirage_gs_deluxe2016_wpns_blaster_right", "cha_dragstrip_gs_deluxe2016_wpns_blaster_right", -10.0),
        (MESH_GUN_L_PID, "cha_mirage_gs_deluxe2016_wpns_blaster_left", "cha_dragstrip_gs_deluxe2016_wpns_blaster_left", -10.0),
    )
    for dst_pid, src_name, dst_name, y_floor in mesh_specs:
        src_tt = copy.deepcopy(ds_meshes[src_name])
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
        print(f"[✓] Grafted Mesh '{dst_name}': PID={dst_pid}, verts={src_tt['m_VertexData']['m_VertexCount']}, bones={len(keep_hashes)}")

    # 4. Inject 2048x2048 Main & 1024x1024 Weapon PBR Atlases
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

    print("[*] Injecting DragStrip Main 2048 & Weapon 1024 PBR textures...")
    set_texture(obj_map[TEX_MAIN_DIFF_PID], TEX_DIR / "cha_dragstrip_main_Diffuse.png", "cha_dragstrip_main_Diffuse", is_raoe=False)
    set_texture(obj_map[TEX_MAIN_NM_PID], TEX_DIR / "cha_dragstrip_main_Normal.png", "cha_dragstrip_main_Normal", is_raoe=False)
    set_texture(obj_map[TEX_MAIN_RAOE_PID], TEX_DIR / "cha_dragstrip_main_RAOE.png", "cha_dragstrip_main_RAOE", is_raoe=True)

    set_texture(obj_map[TEX_WPNS_DIFF_PID], TEX_DIR / "cha_dragstrip_wpns_Diffuse.png", "cha_dragstrip_wpns_Diffuse", is_raoe=False)
    set_texture(obj_map[TEX_WPNS_NM_PID], TEX_DIR / "cha_dragstrip_wpns_Normal.png", "cha_dragstrip_wpns_Normal", is_raoe=False)
    set_texture(obj_map[TEX_WPNS_RAOE_PID], TEX_DIR / "cha_dragstrip_wpns_RAOE.png", "cha_dragstrip_wpns_RAOE", is_raoe=True)

    # 5. Patch Main/Veh/Misc Materials & Weapon Material
    main_tex_overrides = {
        "_base_tex": TEX_MAIN_DIFF_PID,
        "_normal_tex": TEX_MAIN_NM_PID,
        "_pbr_composite_tex": TEX_MAIN_RAOE_PID,
    }
    for mpid in (MAT_MAIN_PID, MAT_MISC_PID, MAT_VEH_PID):
        m_obj = obj_map[mpid]
        m_tt = m_obj.read_typetree()
        patch_kabam_character_mat(m_tt, main_tex_overrides)
        m_obj.save_typetree(m_tt)

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
    print("[✓] Patched DragStrip Main/Veh/Weapon Materials (Scale=(1,1), Offset=(0,0), Crimson Visor Emissive)")

    # 6. Configure SMRs (1 submesh each) & hide Mirage hologram cube
    generous_aabb = {"m_Center": {"x": 0.0, "y": 0.0, "z": 0.0}, "m_Extent": {"x": 10.0, "y": 10.0, "z": 10.0}}
    for pid in SMR_ROBOT_PIDS + SMR_VEH_PIDS:
        smr_obj = obj_map[pid]
        smr_tt = smr_obj.read_typetree()
        smr_tt["m_Materials"] = [{"m_FileID": 0, "m_PathID": MAT_MAIN_PID}]
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
    for pid in SMR_CUBE_PIDS:
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
    print(f"[✓] Updated Robot/Veh/Blaster SMRs & silenced {len(SMR_CUBE_PIDS)} Mirage hologram cube renderers")

    # 7. Configure Fight AOC, Car AOC, MoveSet, Root PrefabList, PropsController, Container, & stream paths
    replaced_pids = {
        MESH_ROBOT_PID, MESH_VEH_PID, MESH_GUN_R_PID, MESH_GUN_L_PID,
        TEX_MAIN_DIFF_PID, TEX_MAIN_NM_PID, TEX_MAIN_RAOE_PID,
        TEX_WPNS_DIFF_PID, TEX_WPNS_NM_PID, TEX_WPNS_RAOE_PID,
    }
    injected_set = {pid for pid, _ in new_clips} | set(cj_proj_pids) | set(hr_proj_pids)
    for obj in list(m_env.objects):
        if obj.path_id == 740305678794743262 and obj.type.name == "AnimatorOverrideController":
            tree = obj.read_typetree()
            clips = tree.get("m_Clips", [])
            clips[2]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_L1_JAZZ}
            clips[3]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_L2_BLASTER}
            clips[5]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_S2}
            clips[39]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": -3005405672129804380}
            clips[40]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": 5259930176709765285}
            clips[41]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_L3_BLASTER}
            clips[42]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_M1_CHEETOR}
            clips[43]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_L4_JAZZ}
            clips[58]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_HEAVY}
            tree["m_Clips"] = clips
            replace_str_in_tree(tree, old_cab, new_cab_low)
            obj.save_typetree(tree)
            print("[+] Configured Dragstrip Fight AOC (preserved kicks, S1/S2/S3, Heavy & victory)")

        elif obj.path_id == -6155136737816236521 and obj.type.name == "AnimatorOverrideController":
            tree = obj.read_typetree()
            replace_str_in_tree(tree, old_cab, new_cab_low)
            obj.save_typetree(tree)

        elif obj.path_id == 1840605340213205441 and obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            moves = tree.get("_moves", [])
            moves[0]["_name"] = "move_jazz_attack_light_03"
            moves[0]["_asset"] = {"m_FileID": 5, "m_PathID": 4591432870569280388}
            moves[1]["_name"] = "move_blaster_attack_light_02"
            moves[1]["_asset"] = {"m_FileID": 5, "m_PathID": -5768502813711380021}
            moves[2]["_name"] = "move_blaster_attack_light_03"
            moves[2]["_asset"] = {"m_FileID": 5, "m_PathID": -7697654508267001063}
            moves[3]["_name"] = "move_jazz_attack_light_04"
            moves[3]["_asset"] = {"m_FileID": 5, "m_PathID": -7349256443508413755}
            moves[4]["_name"] = "move_cheetor_attack_medium_01"
            moves[4]["_asset"] = {"m_FileID": 5, "m_PathID": 7744598786624021798}
            moves[7]["_name"] = "move_hotrod_special_02"
            moves[7]["_asset"] = {"m_FileID": 5, "m_PathID": 7236302885264655572}
            moves[41]["_name"] = "move_heavy_cliffjumper_gs_shoot"
            moves[41]["_asset"] = {"m_FileID": 5, "m_PathID": 3468014272436761367}
            tree["_moves"] = moves
            replace_str_in_tree(tree, old_cab, new_cab_low)
            obj.save_typetree(tree)
            print("[+] Configured Dragstrip MoveSet hitboxes and damage frames")

        elif obj.path_id == -2249602606274241856 and obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            plist = tree.get("PrefabList", [])
            extra_prefabs = [
                {"Prefab": {"m_FileID": 3, "m_PathID": -1408646010089090896}, "Amount": 1},
                {"Prefab": {"m_FileID": 0, "m_PathID": 9003878510878022874}, "Amount": 1},
                {"Prefab": {"m_FileID": 3, "m_PathID": -2054079777877699854}, "Amount": 1},
                {"Prefab": {"m_FileID": 4, "m_PathID": 4727641465992916545}, "Amount": 1},
                {"Prefab": {"m_FileID": 4, "m_PathID": -5363481920856949953}, "Amount": 2},
                {"Prefab": {"m_FileID": 0, "m_PathID": -8172610782387618255}, "Amount": 1},
            ]
            plist.extend(extra_prefabs)
            tree["PrefabList"] = plist
            replace_str_in_tree(tree, old_cab, new_cab_low)
            obj.save_typetree(tree)

        elif obj.path_id in (-3532403574792160156, 7448022809538486323) and obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            props = tree.get("_props", {})
            keys = props.get("_serializedKeys", [])
            values = props.get("_serializedValues", [])
            for k, v in zip(keys, values):
                if k == "cube" and isinstance(v, dict):
                    v["_renderers"] = []
            if obj.path_id == -3532403574792160156 and "gunRight" not in keys:
                for val in values:
                    if val.get("Name") == "rightgun":
                        gun_right_val = copy.deepcopy(val)
                        gun_right_val["Name"] = "gunRight"
                        keys.append("gunRight")
                        values.append(gun_right_val)
                        break
            replace_str_in_tree(tree, old_cab, new_cab_low)
            obj.save_typetree(tree)

        elif obj.type.name == "AssetBundle":
            tree = obj.read_typetree()
            ab_name = f"data/{BOT_ID}_odr/{BOT_ID}.assetbundle"
            tree["m_Name"] = ab_name
            tree["m_AssetBundleName"] = ab_name
            new_container = []
            for item in tree.get("m_Container", []):
                path_str = item[0].replace("mirage_gs_deluxe2016", BOT_ID).replace("Mirage_GS_Deluxe2016", BOT_ID)
                new_container.append([path_str, item[1]])
            tree["m_Container"] = new_container
            replace_str_in_tree(tree, old_cab, new_cab_low)
            obj.save_typetree(tree)

        elif obj.path_id in injected_set:
            # Never overwrite newly cloned AnimationClips / Projectile objects with template bytes
            continue

        elif obj.type.name in ("AudioClip", "Texture2D", "Mesh") and obj.path_id not in replaced_pids:
            tree = obj.read_typetree()
            replace_str_in_tree(tree, old_cab, new_cab_low)
            obj.save_typetree(tree)

        elif obj.type.name in ("AnimatorController", "MonoBehaviour", "GameObject"):
            try:
                tree = obj.read_typetree()
                replace_str_in_tree(tree, old_cab, new_cab_low)
                obj.save_typetree(tree)
            except Exception:
                pass

    # 8. Flush & rebuild exact AssetBundle m_PreloadTable slices & CAB filenames
    print("[*] Rebuilding exact AssetBundle m_PreloadTable & CAB filenames...")
    raw_saved = m_env.file.save(packer="none")
    m_env = UnityPy.load(io.BytesIO(raw_saved))
    sf = [f for f in m_env.file.files.values() if hasattr(f, "objects")][0]
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
    for subfname, subf in m_env.file.files.items():
        nk = subfname.replace(old_cab, NEW_CAB).replace(old_cab_low, new_cab_low)
        if hasattr(subf, "name") and isinstance(subf.name, str):
            subf.name = subf.name.replace(old_cab, NEW_CAB).replace(old_cab_low, new_cab_low)
        new_files[nk] = subf
    m_env.file.files = new_files

    target_bundle = out_dir / f"{BOT_ID}.assetbundle"
    target_bundle.write_bytes(m_env.file.save(packer="lz4"))
    size_mb = target_bundle.stat().st_size / (1024 * 1024)
    print(f"[✓] Saved {target_bundle} ({size_mb:.2f} MB, packer='lz4', CAB={NEW_CAB})")

    # Verify injected projectile prefabs survived serialization intact
    chk_sf = [f for f in m_env.file.files.values() if hasattr(f, "objects")][0]
    hr_go = chk_sf.objects[-8172610782387618255].read_typetree()
    cj_go = chk_sf.objects[9003878510878022874].read_typetree()
    assert hr_go["m_Name"] == "projectile_hotrod_bullet", f"Corrupted HR proj: {hr_go['m_Name']}"
    assert cj_go["m_Name"] == "projectile_megatron_gs_bullet", f"Corrupted CJ proj: {cj_go['m_Name']}"
    print(f"[✓] Verified projectile prefabs intact: '{hr_go['m_Name']}' & '{cj_go['m_Name']}'")

    # 9. Preserve existing custom Dragstrip UI Portraits if present; only create fallback if missing
    p_large_path = next((b / "portraits_odr/portraits/portrait_mirage_gs_large.png" for b in extracted_candidates if (b / "portraits_odr/portraits/portrait_mirage_gs_large.png").is_file()), None)
    p_small_path = next((b / "portraits_odr/portraits/portrait_mirage_gs_small.jpg" for b in extracted_candidates if (b / "portraits_odr/portraits/portrait_mirage_gs_small.jpg").is_file()), None)
    p_quest_path = next((b / "questboard_odr/questboard/portrait_mirage_gs_quest.png" for b in extracted_candidates if (b / "questboard_odr/questboard/portrait_mirage_gs_quest.png").is_file()), None)

    for fname, src_p in (
        ("portrait_dragstrip_large.png", p_large_path),
        ("dragstrip.png", p_large_path),
        ("portrait_dragstrip_small.jpg", p_small_path),
        ("portrait_dragstrip_quest.png", p_quest_path or p_large_path),
    ):
        dst_p = out_dir / fname
        if not dst_p.is_file() and src_p is not None:
            Image.open(src_p).save(dst_p)
            print(f"[*] Generated fallback portrait: {dst_p}")

    print("[+] All Dragstrip Stage 4 3D assets successfully generated!")


def main():
    parser = argparse.ArgumentParser(description="Generate Dragstrip (抢劫) Stage 4 3D grafted assetbundle.")
    parser.add_argument("--output", "-o", default="assets_redeco", help="Output directory")
    args = parser.parse_args()
    generate_dragstrip_assets(output_dir=args.output)


if __name__ == "__main__":
    main()
