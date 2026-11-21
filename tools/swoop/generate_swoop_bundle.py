import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import copy
import io
from collections import deque
from pathlib import Path
from PIL import Image
import UnityPy
from UnityPy.enums import TextureFormat

print("=== [Swoop] Generating assets_redeco/swoop_gs_deluxe2008.assetbundle ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
TFTF_READ_ROOT = Path(r"E:\Agent\TFTF")

DONOR_BUNDLE = TFTF_READ_ROOT / "extracted_apk" / "assets" / "assetpack" / "ramjet_gs_deluxe2008_odr" / "ramjet_gs_deluxe2008.assetbundle"
GRIM_BUNDLE = TFTF_READ_ROOT / "extracted_apk" / "assets" / "assetpack" / "grimlock_gs_mp08_odr" / "grimlock_gs_mp08.assetbundle"
MESH_BUNDLE = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "swoop_mesh.assetbundle"
MOVES_BUNDLE = ROOT / "assets_redeco" / "moves.assetbundle"

TEX_DIR = ROOT / "3rd-party-models" / "swoop" / "02_textures"
OUT_BUNDLE = ROOT / "assets_redeco" / "swoop_gs_deluxe2008.assetbundle"

BOT_ID = "swoop_gs_deluxe2008"
NEW_CAB = "CAB-swoop00112233445566778899aabbccdd"

# Root Prefab PIDs
ROOT_MAIN_PID = 1529847556182042256
ROOT_LW_PID = -4280993829309278178

# Donor Meshes in Ramjet
MESH_ROBOT_PID = 8801638638334271379
MESH_VEHICLE_PID = 733405694182770835

# Donor SMRs for _00 and _01 (main + lw)
SMR_ROBOT_PIDS = (-3606013326717668247, 8363741050498555038)
SMR_VEHICLE_PIDS = (-1331665652208216405, 4450385079657545705)

# Vehicle transformed/Reference Transforms (Main + LW) to uniformly scale Pteranodon 1.53x (matching Robot missile length!)
VEHICLE_REF_TR_PIDS = (-6891910190203298850, -6726056130619506655)
VEHICLE_SCALE = 1.53

# Textures
TEX_ROBOT_DIFF_PID = 7894975478666169647    # cha_ramjet_gs_deluxe2008_main_a
TEX_ROBOT_NM_PID = -4178640796595132748     # main_NM (R=nx, G=ny, B=Metallic)
TEX_ROBOT_RAOE_PID = 4783134961327542118    # main_tform_misc_RAOE (RGB24: R=Roughness, G=AO, B=Emissive)

TEX_VEHICLE_DIFF_PID = 8532584703776603498  # tform_misc_A
TEX_VEHICLE_NM_PID = 5290645072316765759    # tform_misc_NM (R=nx, G=ny, B=Metallic)

# Materials
MAT_ROBOT_PID = 1469909421462177924         # 3B2BE6BA7E47582BBDEB1A581501B6C623131417 (Body + Blue Visor)
MAT_EMBLEM_PID = 3595971348910711679        # 50E4F2A67EE9DABE5DB20CEB76BAB43DFC5BDD88 (Red Autobot Chest Emblem)
MAT_VEHICLE_PID = 3520121911555544087       # 8A8977D16B6868C499019769B40F1FEDCC962D4B (Pteranodon + Blue Eyes)

# Controllers & MoveSet
FIGHT_AOC_PID = 6432204470035570307
JET_AOC_PID = -6340484879223379266
OCLIST_PID = -6569319870757306574
MOVESET_PID = -2598790904785067877
PREFABLIB_PID = -199056643045737730

# StarScream_Normal_attackHeavy in character_anim_procedural.assetbundle (m_FileID=5 in Ramjet, NOT 3 which is character_fx!)
STARSCREAM_HEAVY_CLIP_PID = 7645321843667068633

# Injected local / moves PIDs
SWOOP_WING_FLAP_PID = 7111222233334444555
SWOOP_HEAVY_MOVE_PID = -7777777777777777701

# Cloned Fireball Projectile PIDs from Grimlock
FIREBALL_GO_PID = 5433757232512100521
FIREBALL_TR_PID = -4968702237731866184
FIREBALL_PROJ_MB_PID = -4879017508623021442
FIREBALL_MOVE_MB_PID = 1433291203979908690
FIREBALL_PLIB_MB_PID = 4910730920747389235
FIREBALL_SEQ_MB_PID = -8633259674615553230

FIREBALL_PIDS = [
    FIREBALL_GO_PID,
    FIREBALL_TR_PID,
    FIREBALL_PROJ_MB_PID,
    FIREBALL_MOVE_MB_PID,
    FIREBALL_PLIB_MB_PID,
    FIREBALL_SEQ_MB_PID,
]

FIREBALL_TYPE_MAP = {
    FIREBALL_GO_PID: 1,        # GameObject
    FIREBALL_TR_PID: 2,        # Transform
    FIREBALL_PROJ_MB_PID: 29,  # Projectile
    FIREBALL_MOVE_MB_PID: 9,   # MoveSet
    FIREBALL_PLIB_MB_PID: 20,  # PrefabLib
    FIREBALL_SEQ_MB_PID: 44,   # MoveSequencer
}


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


def patch_kabam_character_mat(
    mat_tt: dict,
    tex_overrides: dict,
    custom_floats: dict | None = None,
    custom_colors: dict | None = None,
):
    # Reset m_Scale=(1,1) and m_Offset=(0,0) on every texture env to strip Ramjet's UV sub-tile crop!
    old_envs = mat_tt.get("m_SavedProperties", {}).get("m_TexEnvs", [])
    new_envs = []
    for item in old_envs:
        if isinstance(item, (tuple, list)) and len(item) == 2:
            prop_name, prop_data = item
            prop_data = copy.deepcopy(prop_data)
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
        "_emissive_overbright_range": 20.0,
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
        "_emissive_intensity_col": {"r": 0.05, "g": 0.45, "b": 1.0, "a": 0.0},
    }
    if custom_colors:
        color_overrides.update(custom_colors)

    colors = mat_tt["m_SavedProperties"]["m_Colors"]
    mat_tt["m_SavedProperties"]["m_Colors"] = [
        (k, dict(color_overrides[k]) if k in color_overrides else v) for k, v in colors
    ]


def disable_wpns_subtrees(obj_map: dict, root_go_pid: int) -> int:
    """Disable SMR, deactivate GO, and zero Transform scale on all *_wpns_* children in character prefab."""
    count = 0
    visited = set()

    def walk(go_pid: int):
        nonlocal count
        if go_pid in visited or go_pid not in obj_map:
            return
        visited.add(go_pid)
        go_obj = obj_map[go_pid]
        go_tt = go_obj.read_typetree()
        gname = go_tt.get("m_Name", "")

        if "_wpns_" in gname.lower():
            if go_tt.get("m_IsActive", True):
                go_tt["m_IsActive"] = False
                go_obj.save_typetree(go_tt)
            for comp in go_tt.get("m_Component", []):
                cpid = comp["component"]["m_PathID"]
                cobj = obj_map.get(cpid)
                if not cobj:
                    continue
                if cobj.type.name in ("SkinnedMeshRenderer", "MeshRenderer"):
                    ct = cobj.read_typetree()
                    ct["m_Enabled"] = False
                    cobj.save_typetree(ct)
                elif cobj.type.name == "Transform":
                    ct = cobj.read_typetree()
                    ct["m_LocalScale"] = {"x": 0.0, "y": 0.0, "z": 0.0}
                    cobj.save_typetree(ct)
            count += 1

        for comp in go_tt.get("m_Component", []):
            cpid = comp["component"]["m_PathID"]
            cobj = obj_map.get(cpid)
            if cobj and cobj.type.name == "Transform":
                tr_tt = cobj.read_typetree()
                for ch in tr_tt.get("m_Children", []):
                    ch_tr = obj_map.get(ch["m_PathID"])
                    if ch_tr:
                        ch_go_pid = ch_tr.read_typetree()["m_GameObject"]["m_PathID"]
                        walk(ch_go_pid)

    walk(root_go_pid)
    return count


def build_swoop_bundle():
    for req in (DONOR_BUNDLE, GRIM_BUNDLE, MESH_BUNDLE, MOVES_BUNDLE):
        assert req.is_file(), f"Missing required bundle: {req}"

    print(f"Loading Mesh Bundle: {MESH_BUNDLE}")
    env_mesh = UnityPy.load(str(MESH_BUNDLE))
    mesh_objs = {obj.read_typetree().get("m_Name"): obj for obj in env_mesh.objects if obj.type.name in ["Mesh", "AnimationClip"]}

    assert "cha_swoop_gs_00" in mesh_objs, "Missing cha_swoop_gs_00 in mesh bundle!"
    assert "cha_swoop_gs_01" in mesh_objs, "Missing cha_swoop_gs_01 in mesh bundle!"
    assert "Swoop_Vehicle_WingFlap_transformed" in mesh_objs, "Missing Swoop_Vehicle_WingFlap_transformed in mesh bundle!"

    swoop_meshes = {
        "cha_swoop_gs_00": mesh_objs["cha_swoop_gs_00"].read_typetree(),
        "cha_swoop_gs_01": mesh_objs["cha_swoop_gs_01"].read_typetree(),
    }
    wing_flap_clip_tt = mesh_objs["Swoop_Vehicle_WingFlap_transformed"].read_typetree()

    print(f"Loading Grimlock Bundle: {GRIM_BUNDLE}")
    env_grim = UnityPy.load(str(GRIM_BUNDLE))
    grim_map = {obj.path_id: obj for obj in env_grim.objects}
    for pid in FIREBALL_PIDS:
        assert pid in grim_map, f"Missing fireball component {pid} in Grimlock bundle!"

    print(f"Loading Donor Bundle: {DONOR_BUNDLE}")
    env = UnityPy.load(str(DONOR_BUNDLE))
    sf = list(env.assets)[0]
    obj_map = {o.path_id: o for o in env.objects}

    cab_files = [k for k in env.file.files.keys() if k.lower().startswith("cab-") and "." not in k]
    assert cab_files, "Could not find CAB file in donor bundle!"
    old_cab = cab_files[0]
    old_cab_low = old_cab.lower()
    new_cab_low = NEW_CAB.lower()
    print(f"[*] Remapping CAB: {old_cab} -> {NEW_CAB}")

    # 1. Remap stream paths ONLY on untouched AudioClips / Textures / Meshes FIRST
    #    (Never touch replaced_pids after writing them, or read_typetree() from stream will overwrite!)
    replaced_pids = {
        MESH_ROBOT_PID, MESH_VEHICLE_PID,
        TEX_ROBOT_DIFF_PID, TEX_ROBOT_NM_PID, TEX_ROBOT_RAOE_PID,
        TEX_VEHICLE_DIFF_PID, TEX_VEHICLE_NM_PID,
    }
    remapped_streams = 0
    for o in env.objects:
        if o.path_id in replaced_pids:
            continue
        if o.type.name in ("AudioClip", "Texture2D", "Mesh"):
            tt = o.read_typetree()
            dirty = False
            sd = tt.get("m_StreamData")
            if isinstance(sd, dict) and isinstance(sd.get("path"), str) and old_cab_low in sd["path"].lower():
                sd["path"] = sd["path"].replace(old_cab, NEW_CAB).replace(old_cab_low, new_cab_low)
                dirty = True
            res = tt.get("m_Resource")
            if isinstance(res, dict) and isinstance(res.get("m_Source"), str) and old_cab_low in res["m_Source"].lower():
                res["m_Source"] = res["m_Source"].replace(old_cab, NEW_CAB).replace(old_cab_low, new_cab_low)
                dirty = True
            if dirty:
                o.save_typetree(tt)
                remapped_streams += 1
    print(f"[*] Remapped external stream paths on {remapped_streams} untouched objects")

    # 2. Graft Meshes (preserve donor m_BoneNameHashes & m_RootBoneNameHash)
    print("[*] Grafting Robot (_00) and Vehicle (_01) Meshes...")
    for dst_pid, src_key, final_mesh_name, expected_submeshes in (
        (MESH_ROBOT_PID, "cha_swoop_gs_00", "cha_swoop_gs_00", 2),
        (MESH_VEHICLE_PID, "cha_swoop_gs_01", "cha_swoop_gs_01", 1),
    ):
        src_tt = swoop_meshes[src_key]
        dst_obj = obj_map[dst_pid]
        dst_tt = dst_obj.read_typetree()

        keep_hashes = list(dst_tt["m_BoneNameHashes"])
        keep_root_hash = int(dst_tt["m_RootBoneNameHash"])
        assert len(src_tt["m_BindPose"]) == len(keep_hashes), (
            f"{final_mesh_name} bindpose len {len(src_tt['m_BindPose'])} != donor hashes len {len(keep_hashes)}"
        )
        assert len(src_tt["m_SubMeshes"]) == expected_submeshes, (
            f"{final_mesh_name} expected {expected_submeshes} submeshes, got {len(src_tt['m_SubMeshes'])}"
        )
        vcount = src_tt["m_VertexData"]["m_VertexCount"]
        assert vcount > 1000, f"{final_mesh_name} vertexCount={vcount} too low!"

        dst_tt["m_Name"] = final_mesh_name
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
        print(f"  [+] Grafted '{final_mesh_name}' into PID {dst_pid}: verts={vcount}, submeshes={expected_submeshes}, bones={len(keep_hashes)}")

    # 3. Clean up SkinnedMeshRenderers on _00 (2 materials: Body+Blue Eyes, Red Emblem) / _01 (1 material) & Disable all Ramjet *_wpns_* parts
    generous_aabb = {
        "m_Center": {"x": 0.0, "y": 4.0, "z": 0.0},
        "m_Extent": {"x": 12.0, "y": 12.0, "z": 12.0},
    }
    for pid in SMR_ROBOT_PIDS:
        smr = obj_map[pid].read_typetree()
        smr["m_Materials"] = [
            {"m_FileID": 0, "m_PathID": MAT_ROBOT_PID},
            {"m_FileID": 0, "m_PathID": MAT_EMBLEM_PID},
        ]
        smr["m_AABB"] = generous_aabb
        smr["m_UpdateWhenOffscreen"] = True
        obj_map[pid].save_typetree(smr)

    for pid in SMR_VEHICLE_PIDS:
        smr = obj_map[pid].read_typetree()
        smr["m_Materials"] = [{"m_FileID": 0, "m_PathID": MAT_VEHICLE_PID}]
        smr["m_AABB"] = generous_aabb
        smr["m_UpdateWhenOffscreen"] = True
        obj_map[pid].save_typetree(smr)

    wpn_main_cnt = disable_wpns_subtrees(obj_map, ROOT_MAIN_PID)
    wpn_lw_cnt = disable_wpns_subtrees(obj_map, ROOT_LW_PID)
    print(f"  [+] Cleaned _00/_01 SMR material slots & disabled legacy Ramjet _wpns_ parts (main={wpn_main_cnt}, lw={wpn_lw_cnt})")

    # 4. Replace Textures using UnityPy t.set_image() (proper OpenGL flip + Format 4 RGBA32 / RGB24 RAOE)
    def set_texture(obj, img_path: Path, name: str, is_raoe: bool = False):
        assert img_path.is_file(), f"Missing texture: {img_path}"
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
        print(f"  [+] Injected '{name}' ({img.size[0]}x{img.size[1]}, fmt={int(target_fmt)}) into PID {obj.path_id}")

    print("[*] Injecting Kabam-calibrated Swoop PBR Textures...")
    set_texture(obj_map[TEX_ROBOT_DIFF_PID], TEX_DIR / "cha_swoop_main_Diffuse.png", "cha_swoop_main_Diffuse", is_raoe=False)
    set_texture(obj_map[TEX_ROBOT_NM_PID], TEX_DIR / "cha_swoop_main_Normal.png", "cha_swoop_main_Normal", is_raoe=False)
    set_texture(obj_map[TEX_ROBOT_RAOE_PID], TEX_DIR / "cha_swoop_main_RAOE.png", "cha_swoop_main_RAOE", is_raoe=True)
    set_texture(obj_map[TEX_VEHICLE_DIFF_PID], TEX_DIR / "cha_swoop_vh_Diffuse.png", "cha_swoop_vh_Diffuse", is_raoe=False)
    set_texture(obj_map[TEX_VEHICLE_NM_PID], TEX_DIR / "cha_swoop_vh_Normal.png", "cha_swoop_vh_Normal", is_raoe=False)

    # 5. Patch Materials (Grimlock-grade Kabam Exposure + Clearcoat + Blue Eyes / Deep Crimson Emblem)
    print("[*] Tuning Materials (Grimlock-Calibrated Metallic + Blue Eyes / Deep Red Emblem)...")
    mat_tt = obj_map[MAT_ROBOT_PID].read_typetree()
    patch_kabam_character_mat(
        mat_tt,
        {
            "_base_tex": TEX_ROBOT_DIFF_PID,
            "_normal_tex": TEX_ROBOT_NM_PID,
            "_pbr_composite_tex": TEX_ROBOT_RAOE_PID,
        },
        custom_floats={
            "_emissive_overbright_range": 18.0,
            "_clearcoat_reflectance_range": 0.10,
            "_roughness_range": 1.0,
        },
        custom_colors={
            "_Color": {"r": 0.65, "g": 0.65, "b": 0.65, "a": 1.0},
            "_base_col": {"r": 0.56, "g": 0.56, "b": 0.56, "a": 1.0},
            "_emissive_intensity_col": {"r": 0.04, "g": 0.52, "b": 1.0, "a": 0.0},  # Electric Autobot Blue Eyes
        },
    )
    obj_map[MAT_ROBOT_PID].save_typetree(mat_tt)

    mat_emblem_tt = obj_map[MAT_EMBLEM_PID].read_typetree()
    patch_kabam_character_mat(
        mat_emblem_tt,
        {
            "_base_tex": TEX_ROBOT_DIFF_PID,
            "_normal_tex": TEX_ROBOT_NM_PID,
            "_pbr_composite_tex": TEX_ROBOT_RAOE_PID,
        },
        custom_floats={
            "_emissive_overbright_range": 9.0,
            "_clearcoat_reflectance_range": 0.10,
            "_roughness_range": 1.0,
        },
        custom_colors={
            "_Color": {"r": 0.65, "g": 0.04, "b": 0.04, "a": 1.0},
            "_base_col": {"r": 0.50, "g": 0.03, "b": 0.03, "a": 1.0},
            "_emissive_intensity_col": {"r": 1.0, "g": 0.0, "b": 0.0, "a": 0.0},   # Deep Rich Crimson Chest Emblem (no pastel pink!)
        },
    )
    obj_map[MAT_EMBLEM_PID].save_typetree(mat_emblem_tt)

    mat_veh_tt = obj_map[MAT_VEHICLE_PID].read_typetree()
    patch_kabam_character_mat(
        mat_veh_tt,
        {
            "_base_tex": TEX_VEHICLE_DIFF_PID,
            "_normal_tex": TEX_VEHICLE_NM_PID,
            "_pbr_composite_tex": TEX_ROBOT_RAOE_PID,
        },
        custom_floats={
            "_emissive_overbright_range": 18.0,
            "_clearcoat_reflectance_range": 0.10,
            "_roughness_range": 1.0,
        },
        custom_colors={
            "_Color": {"r": 0.65, "g": 0.65, "b": 0.65, "a": 1.0},
            "_base_col": {"r": 0.56, "g": 0.56, "b": 0.56, "a": 1.0},
            "_emissive_intensity_col": {"r": 0.04, "g": 0.52, "b": 1.0, "a": 0.0},  # Electric Autobot Blue Pteranodon Eyes
        },
    )
    obj_map[MAT_VEHICLE_PID].save_typetree(mat_veh_tt)

    # 5b. Scale Vehicle transformed/Reference (Main + LW) uniformly by 1.53x to match Robot missile pod length
    for tr_pid in VEHICLE_REF_TR_PIDS:
        tr_tt = obj_map[tr_pid].read_typetree()
        tr_tt["m_LocalScale"] = {"x": VEHICLE_SCALE, "y": VEHICLE_SCALE, "z": VEHICLE_SCALE}
        obj_map[tr_pid].save_typetree(tr_tt)
    print(f"  [+] Scaled Main & LW transformed/Reference uniformly to ({VEHICLE_SCALE}, {VEHICLE_SCALE}, {VEHICLE_SCALE})")

    # 6. Inject Swoop Wing-Flap AnimationClip into SerializedFile
    print("[*] Injecting Swoop_Vehicle_WingFlap_transformed...")
    clip_template = next(o for o in sf.objects.values() if o.type.name == "AnimationClip")
    wing_flap_reader = copy.copy(clip_template)
    wing_flap_reader.path_id = SWOOP_WING_FLAP_PID
    wing_flap_reader.type_id = 6  # AnimationClip type_id in Ramjet
    sf.objects[SWOOP_WING_FLAP_PID] = wing_flap_reader
    wing_flap_clip_tt["m_Name"] = "Swoop_Vehicle_WingFlap_transformed"
    wing_flap_reader.save_typetree(wing_flap_clip_tt)
    print(f"  [+] Injected Swoop_Vehicle_WingFlap_transformed as PID {SWOOP_WING_FLAP_PID}")

    # 7. Wire Controllers & MoveSet
    print("[*] Wiring AnimatorOverrideControllers & MoveSet...")
    # Jet AOC: wire prop_idle (slot 5), prop_attackHeavy (slot 12), prop_levelup_transformIdle (slot 16)
    jet_aoc_tt = obj_map[JET_AOC_PID].read_typetree()
    jet_clips = jet_aoc_tt["m_Clips"]
    assert jet_clips[5]["m_OriginalClip"]["m_PathID"] == 3658090888164254241    # prop_idle
    jet_clips[5]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": SWOOP_WING_FLAP_PID}

    assert jet_clips[12]["m_OriginalClip"]["m_PathID"] == -7632205551962568777  # prop_attackHeavy
    jet_clips[12]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": SWOOP_WING_FLAP_PID}

    assert jet_clips[16]["m_OriginalClip"]["m_PathID"] == -8823098701810809179  # prop_levelup_transformIdle
    jet_clips[16]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": SWOOP_WING_FLAP_PID}
    jet_aoc_tt["m_Clips"] = jet_clips
    obj_map[JET_AOC_PID].save_typetree(jet_aoc_tt)
    print(f"  [+] Wired Jet AOC slots 5, 12, 16 to Wing Flap clip")

    # Fight AOC: wire slot 58 (char_attackHeavy) to StarScream_Normal_attackHeavy (m_FileID=5 = character_anim_procedural.assetbundle!)
    fight_aoc_tt = obj_map[FIGHT_AOC_PID].read_typetree()
    fight_clips = fight_aoc_tt["m_Clips"]
    assert fight_clips[58]["m_OriginalClip"]["m_PathID"] == -643812257501667161
    fight_clips[58]["m_OverrideClip"] = {"m_FileID": 5, "m_PathID": STARSCREAM_HEAVY_CLIP_PID}
    fight_aoc_tt["m_Clips"] = fight_clips
    obj_map[FIGHT_AOC_PID].save_typetree(fight_aoc_tt)
    print(f"  [+] Wired Fight AOC slot 58 to StarScream_Normal_attackHeavy (FileID=5, PathID={STARSCREAM_HEAVY_CLIP_PID})")

    # Update OverrideControllerList Base.HeavyAttack metadata string to match StarScream_Normal_attackHeavy
    oclist_tt = obj_map[OCLIST_PID].read_typetree()
    for entry in oclist_tt.get("_overrideControllerList", []):
        if entry.get("StateUniqueName") == "Base.HeavyAttack":
            entry["OverrideClipName"] = "StarScream_Normal_attackHeavy"
    obj_map[OCLIST_PID].save_typetree(oclist_tt)

    # MoveSet: wire slot 44 (Base.HeavyAttack) -> move_heavy_swoop
    moveset_tt = obj_map[MOVESET_PID].read_typetree()
    moves = moveset_tt["_moves"]
    assert moves[44]["_animStateName"] == "Base.HeavyAttack"
    moves[44]["_name"] = "move_heavy_swoop"
    moves[44]["_asset"] = {"m_FileID": 2, "m_PathID": SWOOP_HEAVY_MOVE_PID}
    moveset_tt["_moves"] = moves
    obj_map[MOVESET_PID].save_typetree(moveset_tt)
    print(f"  [+] Wired MoveSet slot 44 to move_heavy_swoop (FileID=2, PathID={SWOOP_HEAVY_MOVE_PID})")

    # 8. Clone Fireball Projectile from Grimlock with strict type_id mapping
    print("[*] Cloning Fireball Projectile...")
    for pid in FIREBALL_PIDS:
        grim_obj = grim_map[pid]
        new_reader = copy.copy(grim_obj)
        new_reader.path_id = pid
        new_reader.type_id = FIREBALL_TYPE_MAP[pid]
        sf.objects[pid] = new_reader

        fb_tt = grim_obj.read_typetree()
        if pid == FIREBALL_MOVE_MB_PID:
            for m in fb_tt.get("_moves", []):
                m["_asset"]["m_FileID"] = 2  # moves.assetbundle in Ramjet
        elif pid == FIREBALL_PLIB_MB_PID:
            for item in fb_tt.get("PrefabList", []):
                pref = item.get("Prefab", {})
                if pref.get("m_FileID") == 5:
                    pref["m_FileID"] = 3
        new_reader.save_typetree(fb_tt)
        print(f"  [+] Injected {grim_obj.type.name} (PID: {pid}, type_id: {new_reader.type_id})")

    # 9. Add projectile_grimlock_fireball to Root PrefabLib
    root_plib_tt = obj_map[PREFABLIB_PID].read_typetree()
    plist = root_plib_tt.get("PrefabList", [])
    if not any(item.get("Prefab", {}).get("m_PathID") == FIREBALL_GO_PID for item in plist):
        plist.append({"Prefab": {"m_FileID": 0, "m_PathID": FIREBALL_GO_PID}, "Amount": 1})
        root_plib_tt["PrefabList"] = plist
        obj_map[PREFABLIB_PID].save_typetree(root_plib_tt)
        print(f"  [+] Added projectile_grimlock_fireball to Root PrefabLib (PID: {PREFABLIB_PID})")

    # 10. Audit script_types sorting
    st_entries = [(st.local_serialized_file_index, st.local_identifier_in_file) for st in sf.script_types]
    assert st_entries == sorted(st_entries), "script_types were not sorted ascending!"
    print(f"  [+] Verified {len(sf.script_types)} script_types strictly sorted ascending")

    # 11. Flush to uncompressed bytes & reload cleanly before rebuilding AssetBundle Container & PreloadTable
    print("[*] Flushing changes & reloading cleanly to rebuild AssetBundle Container & PreloadTable...")
    raw_saved = env.file.save(packer="none")
    env = UnityPy.load(io.BytesIO(raw_saved))
    sf = [f for f in env.file.files.values() if hasattr(f, "objects")][0]
    ab_obj = next(o for o in sf.objects.values() if o.type.name == "AssetBundle")
    ab_tree = ab_obj.read_typetree()

    ab_tree["m_Name"] = f"data/{BOT_ID}_odr/{BOT_ID}.assetbundle"
    ab_tree["m_AssetBundleName"] = f"data/{BOT_ID}_odr/{BOT_ID}.assetbundle"

    new_container = []
    for k, v in ab_tree.get("m_Container", []):
        nk = k.replace("ramjet_gs_deluxe2008", BOT_ID).replace("Ramjet_GS_Deluxe2008", BOT_ID)
        v_dict = dict(v) if isinstance(v, dict) else copy.deepcopy(v)
        new_container.append([nk, v_dict])
    ab_tree["m_Container"] = new_container

    new_preload = []
    for cname, cinfo in ab_tree.get("m_Container", []):
        rpid = int(cinfo["asset"]["m_PathID"])
        if rpid == ROOT_MAIN_PID:
            roots_to_collect = [ROOT_MAIN_PID, SWOOP_WING_FLAP_PID] + FIREBALL_PIDS
        else:
            roots_to_collect = [rpid]
        _, closure_pptrs = collect_closure(sf, roots_to_collect)

        grouped = {}
        for fid, pid in closure_pptrs:
            grouped.setdefault(fid, []).append(pid)
        sorted_pptrs = []
        for fid in sorted(grouped.keys()):
            for pid in sorted(grouped[fid]):
                sorted_pptrs.append((fid, pid))

        cinfo["preloadIndex"] = len(new_preload)
        cinfo["preloadSize"] = len(sorted_pptrs)
        for fid, pid in sorted_pptrs:
            new_preload.append({"m_FileID": fid, "m_PathID": pid})
        print(f"  [Preload Slice] {cname}: size={len(sorted_pptrs)} (index={cinfo['preloadIndex']})")

    ab_tree["m_PreloadTable"] = new_preload
    ab_obj.save_typetree(ab_tree)

    # Rename ALL CAB files (.resS, .resource, serialized file)
    new_files = {}
    for k, v in env.file.files.items():
        if old_cab in k:
            nk = k.replace(old_cab, NEW_CAB)
        elif old_cab_low in k:
            nk = k.replace(old_cab_low, new_cab_low)
        else:
            nk = k
        new_files[nk] = v
    env.file.files = new_files

    # 12. Save bundle with packer="lz4"
    print(f"[*] Saving {OUT_BUNDLE} with packer='lz4'...")
    OUT_BUNDLE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_BUNDLE, "wb") as f:
        f.write(env.file.save(packer="lz4"))

    bundle_size_mb = OUT_BUNDLE.stat().st_size / (1024 * 1024)
    print(f"✅ [SUCCESS] Generated {OUT_BUNDLE} ({bundle_size_mb:.2f} MB)")


if __name__ == "__main__":
    build_swoop_bundle()
