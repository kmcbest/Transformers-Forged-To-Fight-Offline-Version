import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import io
from pathlib import Path
from collections import deque
from PIL import Image
import UnityPy
from UnityPy.enums import TextureFormat
from UnityPy.streams import EndianBinaryReader

print("=== [StarSaber] Generating assets_redeco/starsaber_gs_leader2014.assetbundle (Gate 4 Production) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
TFTF_READ_ROOT = Path(r"E:\Agent\TFTF")

DONOR_BUNDLE = TFTF_READ_ROOT / "extracted_apk" / "assets" / "assetpack" / "jetfire_gs_leader2014_odr" / "jetfire_gs_leader2014.assetbundle"
WINDBLADE_BUNDLE = TFTF_READ_ROOT / "extracted_apk" / "assets" / "assetpack" / "windblade_gs_odr" / "windblade_gs.assetbundle"
MOVES_BUNDLE = TFTF_READ_ROOT / "assets_netflix" / "moves.assetbundle"
PROC_BUNDLE = TFTF_READ_ROOT / "assets_netflix" / "character_anim_procedural.assetbundle"

MESH_BUNDLE = ROOT / "3rd-party-models" / "StarSaber" / "04_unity_bundles" / "starsaber_mesh.assetbundle"
TEX_DIR = ROOT / "3rd-party-models" / "StarSaber" / "02_textures"
OUT_BUNDLE = ROOT / "assets_redeco" / "starsaber_gs_leader2014.assetbundle"

NEW_CAB = "CAB-7e3f890123456789abcdef0123456789"
BOT_ID = "starsaber_gs_leader2014"

# Donor Meshes & SMRs (Jetfire_GS_Leader2014)
MESH_ROBOT_PID = -2458698293407160617
MESH_VEHICLE_PID = -8840240213025646850

SMR_ROBOT_PIDS = (-2741591127294404007, 2800854444751231408)
SMR_VEHICLE_PIDS = (-6848498868240829709, 2289053572927707393)
SMR_WPNS_PIDS = (-6612254241771744554, 738325550751503188)

# Donor Textures (2 sets: Main Body+Jet, Weapons Sword; ContactShadowA/B left untouched)
TEX_MAIN_DIFF_PID = -3298116874233608628
TEX_MAIN_NM_PID = -266931228976835568
TEX_MAIN_RAOE_PID = 6229099485003052592

TEX_WPNS_DIFF_PID = -448195243497892205
TEX_WPNS_NM_PID = 6558738824407314539
TEX_WPNS_RAOE_PID = -2256090246337658038

# Donor Materials
MAT_MAIN_PID = -3031952169783397726
MAT_TRANSP_PID = -2512542713218239790
MAT_TFORM_PID = 3248942549265873418
MAT_WPNS_PID = 6381148994484861096

# Donor Combat / Audio / Props
FIGHT_AOC_PID = -8402565767957608701
S2_CLIP_SLOT_PID = 6966345187514932495
WB_S2_CLIP_PID = -2626501024704866973
MOVESET_PID = 2601823321879744519
CHAR_AUDIO_PID = -1461777177113225753
PROPS_CTRL_PIDS = (-9009354885740569570, 1062452820465670706)

AUDIO_HEAVY_PID = 6510216056584927456
AUDIO_HEAVY_HIT_PIDS = (-6040142654073938373, -1683915847129078070, 6184518808667980096)


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


def replace_str_in_tree(tree_obj, old_s: str, new_s: str):
    if isinstance(tree_obj, dict):
        for k, v in tree_obj.items():
            if isinstance(v, str) and old_s in v:
                tree_obj[k] = v.replace(old_s, new_s)
            else:
                replace_str_in_tree(v, old_s, new_s)
    elif isinstance(tree_obj, list):
        for idx, item in enumerate(tree_obj):
            if isinstance(item, str) and old_s in item:
                tree_obj[idx] = item.replace(old_s, new_s)
            else:
                replace_str_in_tree(item, old_s, new_s)


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


def patch_kabam_character_mat(mat_tt: dict, tex_overrides: dict, base_col: float = 0.85, roughness: float = 0.95):
    old_envs = mat_tt.get("m_SavedProperties", {}).get("m_TexEnvs", [])
    new_envs = []
    for item in old_envs:
        if isinstance(item, tuple) and len(item) == 2:
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
        "_roughness_range": roughness,
        "_clearcoat_reflectance_range": 0.03,
        "_emissive_range": 0.0,
        "_emissive_none": 0.0,
        "_emissive_overbright_range": 20.0,
    }
    floats = mat_tt["m_SavedProperties"]["m_Floats"]
    existing_keys = {k for k, _ in floats}
    new_floats = [(k, float_overrides[k] if k in float_overrides else v) for k, v in floats]
    for k, v in float_overrides.items():
        if k not in existing_keys:
            new_floats.append((k, v))
    mat_tt["m_SavedProperties"]["m_Floats"] = new_floats

    color_overrides = {
        "_Color": {"r": base_col, "g": base_col, "b": base_col, "a": 1.0},
        "_base_col": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
        "_emissive_intensity_col": {"r": 0.45, "g": 0.90, "b": 1.0, "a": 0.0},
    }
    colors = mat_tt["m_SavedProperties"]["m_Colors"]
    mat_tt["m_SavedProperties"]["m_Colors"] = [
        (k, dict(color_overrides[k]) if k in color_overrides else v) for k, v in colors
    ]


def build_starsaber_bundle():
    for req in (DONOR_BUNDLE, WINDBLADE_BUNDLE, MESH_BUNDLE):
        assert req.is_file(), f"Missing required bundle: {req}"

    moves_pids = {o.path_id for o in UnityPy.load(str(MOVES_BUNDLE)).objects} if MOVES_BUNDLE.is_file() else set()
    proc_pids = {o.path_id for o in UnityPy.load(str(PROC_BUNDLE)).objects} if PROC_BUNDLE.is_file() else set()

    print(f"Loading Mesh Bundle: {MESH_BUNDLE}")
    env_mesh = UnityPy.load(str(MESH_BUNDLE))
    ss_meshes = {}
    for obj in env_mesh.objects:
        if obj.type.name == "Mesh":
            tt = obj.read_typetree()
            ss_meshes[tt["m_Name"]] = tt
    assert "cha_jetfire_gs_leader2014_00" in ss_meshes and "cha_jetfire_gs_leader2014_01" in ss_meshes, (
        f"Missing grafted meshes in {MESH_BUNDLE}: {list(ss_meshes.keys())}"
    )

    print(f"Loading Windblade Bundle: {WINDBLADE_BUNDLE}")
    env_wb = UnityPy.load(str(WINDBLADE_BUNDLE))
    wb_obj_map = {o.path_id: o for o in env_wb.objects}
    assert WB_S2_CLIP_PID in wb_obj_map, "Missing Windblade S2 clip!"
    wb_s2_clip_tree = wb_obj_map[WB_S2_CLIP_PID].read_typetree()
    wb_s2_clip_tree["m_Name"] = "cha_starsaber_gs_leader2014_attackSpecial_02"
    wb_res_file = next((f for n, f in env_wb.file.files.items() if n.endswith(".resource")), None)
    assert wb_res_file is not None, "Missing Windblade .resource!"
    wb_clip1_data = wb_res_file.bytes[149760 : 149760 + 14368]
    wb_clip2_data = wb_res_file.bytes[170016 : 170016 + 15200]

    print(f"Loading Donor Bundle: {DONOR_BUNDLE}")
    env = UnityPy.load(str(DONOR_BUNDLE))
    obj_map = {o.path_id: o for o in env.objects}

    cab_files = [k for k in env.file.files.keys() if k.lower().startswith("cab-") and "." not in k]
    assert cab_files, "Could not find CAB file in donor bundle!"
    old_cab = cab_files[0]
    old_cab_low = old_cab.lower()
    new_cab_low = NEW_CAB.lower()
    print(f"[*] Remapping CAB: {old_cab} -> {NEW_CAB}")

    # 1. Rename AssetBundle & Container Keys (NEVER rename root GameObject m_Name per §11.10 Matinee safety!)
    ab_objs = [o for o in env.objects if o.type.name == "AssetBundle"]
    assert len(ab_objs) == 1
    ab_tt = ab_objs[0].read_typetree()
    ab_tt["m_Name"] = f"data/{BOT_ID}_odr/{BOT_ID}.assetbundle"
    ab_tt["m_AssetBundleName"] = f"data/{BOT_ID}_odr/{BOT_ID}.assetbundle"
    new_container = []
    for k, v in ab_tt["m_Container"]:
        nk = k.replace("jetfire_gs_leader2014", BOT_ID).replace("Jetfire_GS_Leader2014", BOT_ID)
        new_container.append([nk, v])
        print(f"  [Container] '{k}' -> '{nk}'")
    ab_tt["m_Container"] = new_container
    ab_objs[0].save_typetree(ab_tt)

    # 2. Append Windblade heavy attack audio into .resource BEFORE stream path remap
    res_name, res_file = next(((n, f) for n, f in env.file.files.items() if n.endswith(".resource")), (None, None))
    assert res_file is not None, "Missing donor .resource!"
    old_res_len = len(res_file.bytes)
    offset1 = old_res_len
    offset2 = old_res_len + len(wb_clip1_data)
    new_res_reader = EndianBinaryReader(res_file.bytes + wb_clip1_data + wb_clip2_data)
    new_res_reader.flags = getattr(res_file, "flags", 0)
    env.file.files[res_name] = new_res_reader

    t_heavy = obj_map[AUDIO_HEAVY_PID].read_typetree()
    t_heavy["m_Resource"] = {
        "m_Source": f"archive:/{NEW_CAB}/{NEW_CAB}.resource",
        "m_Offset": offset1,
        "m_Size": len(wb_clip1_data),
    }
    obj_map[AUDIO_HEAVY_PID].save_typetree(t_heavy)

    for pid in AUDIO_HEAVY_HIT_PIDS:
        t_hit = obj_map[pid].read_typetree()
        t_hit["m_Resource"] = {
            "m_Source": f"archive:/{NEW_CAB}/{NEW_CAB}.resource",
            "m_Offset": offset2,
            "m_Size": len(wb_clip2_data),
        }
        obj_map[pid].save_typetree(t_hit)
    print(f"[+] Appended Windblade heavy audio (+{len(wb_clip1_data)+len(wb_clip2_data)} bytes) to .resource")

    # 3. Remap stream paths across untouched AudioClips / Textures / Meshes
    replaced_pids = {
        MESH_ROBOT_PID, MESH_VEHICLE_PID,
        TEX_MAIN_DIFF_PID, TEX_MAIN_NM_PID, TEX_MAIN_RAOE_PID,
        TEX_WPNS_DIFF_PID, TEX_WPNS_NM_PID, TEX_WPNS_RAOE_PID,
        AUDIO_HEAVY_PID, *AUDIO_HEAVY_HIT_PIDS,
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
    print(f"[*] Remapped external stream paths on {remapped_streams} objects")

    # 4. Graft Robot (_00: 54 bones, 2 submeshes Body+Sword) & Vehicle (_01: 29 bones, 1 submesh Jet)
    for dst_pid, src_key, final_mesh_name, expected_subs in (
        (MESH_ROBOT_PID, "cha_jetfire_gs_leader2014_00", "cha_starsaber_gs_leader2014_00", 2),
        (MESH_VEHICLE_PID, "cha_jetfire_gs_leader2014_01", "cha_starsaber_gs_leader2014_01", 1),
    ):
        src_tt = ss_meshes[src_key]
        dst_obj = obj_map[dst_pid]
        dst_tt = dst_obj.read_typetree()

        keep_hashes = list(dst_tt["m_BoneNameHashes"])
        keep_root_hash = int(dst_tt["m_RootBoneNameHash"])
        assert len(src_tt["m_BindPose"]) == len(keep_hashes), (
            f"{final_mesh_name} bindpose len {len(src_tt['m_BindPose'])} != donor hashes len {len(keep_hashes)}"
        )
        assert len(src_tt["m_SubMeshes"]) == expected_subs, (
            f"{final_mesh_name} submeshes {len(src_tt['m_SubMeshes'])} != {expected_subs}"
        )
        vcount = src_tt["m_VertexData"]["m_VertexCount"]
        assert vcount > 10000, f"{final_mesh_name} vertexCount={vcount} too low!"

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
        print(f"[✓] Grafted Mesh '{final_mesh_name}': PID={dst_pid}, verts={vcount}, submeshes={expected_subs}, bones={len(keep_hashes)}")

    # 5. Inject Calibrated Textures (Diffuse RGBA32, Kabam NM.B Metallic Normal RGBA32, Strict RGB24 RAOE)
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
        print(f"  [Tex] {obj.path_id}: '{name}' {img.size[0]}x{img.size[1]} fmt={int(target_fmt)}")

    print("Injecting Star Saber Textures:")
    set_texture(obj_map[TEX_MAIN_DIFF_PID], TEX_DIR / "cha_starsaber_main_Diffuse.png", "cha_starsaber_main_a", is_raoe=False)
    set_texture(obj_map[TEX_MAIN_NM_PID], TEX_DIR / "cha_starsaber_main_Normal.png", "cha_starsaber_main_NM", is_raoe=False)
    set_texture(obj_map[TEX_MAIN_RAOE_PID], TEX_DIR / "cha_starsaber_main_RAOE.png", "cha_starsaber_main_RAOE", is_raoe=True)

    set_texture(obj_map[TEX_WPNS_DIFF_PID], TEX_DIR / "cha_starsaber_wpns_Diffuse.png", "cha_starsaber_wpns_a", is_raoe=False)
    set_texture(obj_map[TEX_WPNS_NM_PID], TEX_DIR / "cha_starsaber_wpns_Normal.png", "cha_starsaber_wpns_NM", is_raoe=False)
    set_texture(obj_map[TEX_WPNS_RAOE_PID], TEX_DIR / "cha_starsaber_wpns_RAOE.png", "cha_starsaber_wpns_RAOE", is_raoe=True)

    # 6. Patch Materials (Scale=(1,1), Offset=(0,0), Calibrated Color/Emissive/Clearcoat)
    main_tex_map = {
        "_base_tex": TEX_MAIN_DIFF_PID,
        "_normal_tex": TEX_MAIN_NM_PID,
        "_pbr_composite_tex": TEX_MAIN_RAOE_PID,
    }
    for mpid in (MAT_MAIN_PID, MAT_TRANSP_PID, MAT_TFORM_PID):
        m_tt = obj_map[mpid].read_typetree()
        patch_kabam_character_mat(m_tt, main_tex_map, base_col=0.85, roughness=0.95)
        obj_map[mpid].save_typetree(m_tt)

    wpn_tt = obj_map[MAT_WPNS_PID].read_typetree()
    patch_kabam_character_mat(
        wpn_tt,
        {
            "_base_tex": TEX_WPNS_DIFF_PID,
            "_normal_tex": TEX_WPNS_NM_PID,
            "_pbr_composite_tex": TEX_WPNS_RAOE_PID,
        },
        base_col=0.90,
        roughness=0.92,
    )
    obj_map[MAT_WPNS_PID].save_typetree(wpn_tt)
    print("[✓] Patched Body/Jet/Weapon Kabam Materials (Scale=(1,1), Offset=(0,0), NM.B dielectric armor)")

    # 7. Wire SMRs & Disable Old Rifle/Sword Prop (King's Sword is baked as _00 Submesh 1!)
    generous_aabb = {
        "m_Center": {"x": 0.0, "y": 5.0, "z": 0.0},
        "m_Extent": {"x": 12.0, "y": 12.0, "z": 12.0},
    }
    for pid in SMR_ROBOT_PIDS:
        smr_tt = obj_map[pid].read_typetree()
        assert len(smr_tt["m_Bones"]) == 54
        smr_tt["m_Mesh"] = {"m_FileID": 0, "m_PathID": MESH_ROBOT_PID}
        smr_tt["m_Materials"] = [
            {"m_FileID": 0, "m_PathID": MAT_MAIN_PID},
            {"m_FileID": 0, "m_PathID": MAT_WPNS_PID},
        ]
        smr_tt["m_AABB"] = generous_aabb
        smr_tt["m_UpdateWhenOffscreen"] = True
        smr_tt["m_Enabled"] = True
        obj_map[pid].save_typetree(smr_tt)

    for pid in SMR_VEHICLE_PIDS:
        smr_tt = obj_map[pid].read_typetree()
        assert len(smr_tt["m_Bones"]) == 29
        smr_tt["m_Mesh"] = {"m_FileID": 0, "m_PathID": MESH_VEHICLE_PID}
        smr_tt["m_Materials"] = [{"m_FileID": 0, "m_PathID": MAT_MAIN_PID}]
        smr_tt["m_AABB"] = generous_aabb
        smr_tt["m_UpdateWhenOffscreen"] = True
        smr_tt["m_Enabled"] = False
        obj_map[pid].save_typetree(smr_tt)

    for pid in SMR_WPNS_PIDS:
        smr_tt = obj_map[pid].read_typetree()
        smr_tt["m_Enabled"] = False
        obj_map[pid].save_typetree(smr_tt)

    for pid in PROPS_CTRL_PIDS:
        tree = obj_map[pid].read_typetree()
        props = tree.get("_props", {})
        keys = props.get("_serializedKeys", [])
        vals = props.get("_serializedValues", [])
        for idx, kname in enumerate(keys):
            if kname in ("gun", "sword"):
                vals[idx]["InitFlags"] = 0
                vals[idx]["_startActive"] = False
                vals[idx]["_renderers"] = []
        props["_serializedKeys"] = keys
        props["_serializedValues"] = vals
        tree["_props"] = props
        obj_map[pid].save_typetree(tree)
    print("[✓] Wired Robot (2 mats) & Vehicle (1 mat, 29 bones) SMRs; disabled legacy rifle prop.")

    # 8. Wire Windblade S2 Clip, Fight AOC, MoveSet & Swords Audio
    obj_map[S2_CLIP_SLOT_PID].save_typetree(wb_s2_clip_tree)

    aoc_tt = obj_map[FIGHT_AOC_PID].read_typetree()
    clips = aoc_tt.get("m_Clips", [])
    aoc_clip_verify = {
        2: 740649405912261330,     # Light 01
        3: -2512025252598410331,   # Light 02
        41: -4980757935915932854,  # Light 03
        43: -4106831893816218441,  # Light 04
        42: 6308122467145514604,   # Medium 01
        44: -705967800912522861,   # Medium 02
        45: 7146863003282264883,   # BlockReact
        46: 7146863003282264883,   # BlockReact Ranged
        4: -3664095140934993801,   # Drift S1
        58: 2534697979766001969,   # Windblade Heavy
    }
    for slot, cid in aoc_clip_verify.items():
        if proc_pids:
            assert cid in proc_pids, f"Missing clip PID {cid} in procBundle!"
        clips[slot]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": cid}
    clips[5]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": S2_CLIP_SLOT_PID}
    # Jetfire Ranged & SP3 kept local (FileID=0)
    clips[51]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": 7808332553383168359}
    clips[52]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": -7264490462704346615}
    clips[53]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": -1145688102861077554}
    clips[31]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": -4700446166485423738}
    clips[32]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": 5007219591915846681}
    aoc_tt["m_Clips"] = clips
    obj_map[FIGHT_AOC_PID].save_typetree(aoc_tt)

    ms_tt = obj_map[MOVESET_PID].read_typetree()
    moves_table = [
        (0, "move_sword_attack_light_01", "Base.LightAttack01", -1283304507747283112),
        (1, "move_sword_attack_light_02", "Base.LightAttack02", 7616440351077033282),
        (2, "move_sword_attack_light_03", "Base.LightAttack03", -3329254882358104680),
        (3, "move_sword_attack_light_04", "Base.LightAttack04", 4145453135915101152),
        (4, "move_sword_attack_medium_01", "Base.MediumAttack01", -1389778547757567769),
        (5, "move_sword_attack_medium_02", "Base.MediumAttack02", -3898379380470346085),
        (6, "move_drift_special_01", "Base.SpecialAttack01", -6173328959056132852),
        (7, "move_windblade_special_02", "Base.SpecialAttack02", -6524404075124180520),
        (8, "move_sword_block_react", "Base.BlockReact", 2656533506074151531),
        (9, "move_sword_block_react", "Base.BlockReactRanged", 6843684539569461767),
        (41, "move_heavy_plane_donut", "Base.HeavyAttack", 4908036883554989015),
        (42, "move_attackRanged_jetfire_handGun_right_01", "Base.RangedAttack01", 4026438278308373272),
        (43, "move_attackRanged_jetfire_handGun_right_02", "Base.RangedAttack02", -3609132228276371244),
        (44, "move_attackRanged_jetfire_handGun_right_03", "Base.RangedAttack03", -4303718209525360164),
    ]
    moves = ms_tt.get("_moves", [])
    assert len(moves) >= 50
    for idx, mname, state, mpid in moves_table:
        if moves_pids:
            assert mpid in moves_pids, f"Missing move PID {mpid} ({mname}) in moves.assetbundle!"
        moves[idx] = {"_name": mname, "_animStateName": state, "_asset": {"m_FileID": 3, "m_PathID": mpid}}
    ms_tt["_moves"] = moves
    obj_map[MOVESET_PID].save_typetree(ms_tt)

    aud_tt = obj_map[CHAR_AUDIO_PID].read_typetree()
    aud_tt["_categories"] = ["Swords", "Generations"]
    ev_overrides = {
        "gen_attack_1": "", "gen_attack_hit_1": "",
        "gen_attack_2": "", "gen_attack_hit_2": "",
        "gen_attack_3": "", "gen_attack_hit_3": "",
        "gen_attack_4": "", "gen_attack_hit_4": "",
        "gen_attack_5": "", "gen_attack_hit_5": "",
        "gen_attack_6": "", "gen_attack_hit_6": "",
        "gen_attack_heavy": "jetfire_attack_heavy",
        "gen_attack_heavy_hit": "jetfire_attack_heavy_hit",
        "gen_special_3": "jetfire_special_3",
        "gen_block": "", "gen_block_react": "",
    }
    for ev in aud_tt.get("_events", []):
        gn = ev.get("_genEvent")
        if gn in ev_overrides:
            ev["_override"] = ev_overrides[gn]
    obj_map[CHAR_AUDIO_PID].save_typetree(aud_tt)
    print("[✓] Wired Fight AOC, MoveSet (Motormaster+Drift S1+Windblade S2/Heavy+Jetfire Ranged/SP3), and Swords CharacterAudio.")

    # 9. Flush & rebuild exact AssetBundle m_PreloadTable & CAB
    print("[*] Rebuilding exact AssetBundle m_PreloadTable & CAB...")
    raw_saved = env.file.save(packer="none")
    env = UnityPy.load(io.BytesIO(raw_saved))
    sf = [f for f in env.file.files.values() if hasattr(f, "objects")][0]
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
    for k, v in env.file.files.items():
        if old_cab in k:
            nk = k.replace(old_cab, NEW_CAB)
        elif old_cab_low in k:
            nk = k.replace(old_cab_low, new_cab_low)
        else:
            nk = k
        if hasattr(v, "name") and isinstance(v.name, str):
            v.name = v.name.replace(old_cab, NEW_CAB).replace(old_cab_low, new_cab_low)
        new_files[nk] = v
    env.file.files = new_files

    print(f"\nSaving final assetbundle to: {OUT_BUNDLE}")
    OUT_BUNDLE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_BUNDLE, "wb") as f:
        f.write(env.file.save(packer="lz4"))
    size_mb = OUT_BUNDLE.stat().st_size / (1024 * 1024)
    print(f"[✓] Saved {OUT_BUNDLE.name} ({size_mb:.2f} MB, packer='lz4', CAB={NEW_CAB})")

    verify_starsaber_bundle_integrity(OUT_BUNDLE)


def verify_starsaber_bundle_integrity(bundle_path: Path):
    print("\n=== Verifying Gate 4 Bundle Integrity ===")
    env = UnityPy.load(str(bundle_path))
    sf = list(env.assets)[0]

    st_keys = [(s.local_serialized_file_index, s.local_identifier_in_file) for s in sf.script_types]
    assert st_keys == sorted(st_keys), "sf.script_types is not sorted ascending!"

    new_cab_low = NEW_CAB.lower()
    ab_tree = None
    for pid, obj in sf.objects.items():
        tree = obj.read_typetree()
        if obj.type.name == "AssetBundle":
            ab_tree = tree
        if obj.type.name == "Texture2D":
            t = obj.read()
            if hasattr(t, "m_StreamData") and getattr(t.m_StreamData, "size", 0) == 0:
                expected_bpp = 4 if int(t.m_TextureFormat) == 4 else (3 if int(t.m_TextureFormat) == 3 else None)
                if expected_bpp:
                    expected_len = t.m_Width * t.m_Height * expected_bpp
                    actual_len = len(getattr(t, "image_data", b""))
                    assert actual_len == expected_len, f"Texture {pid} ('{t.m_Name}') len mismatch: {actual_len} != {expected_len}"

        for pptr in iter_pptrs_in_tree(tree):
            fid, tpid = int(pptr.get("m_FileID", 0)), int(pptr.get("m_PathID", 0))
            if tpid == 0:
                continue
            if fid == 0:
                assert tpid in sf.objects, f"Dangling local PPtr {tpid} in {pid} ({obj.type.name})"
            else:
                assert 1 <= fid <= len(sf.externals), f"Out-of-range external fid={fid} in {pid}"

        sd = tree.get("m_StreamData")
        if isinstance(sd, dict) and int(sd.get("size", 0)) > 0:
            assert new_cab_low in sd.get("path", "").lower(), f"Bad stream path on {pid}: {sd}"
        res = tree.get("m_Resource")
        if isinstance(res, dict) and int(res.get("m_Size", 0)) > 0:
            assert new_cab_low in res.get("m_Source", "").lower(), f"Bad resource path on {pid}: {res}"

    # Verify root GameObject m_Name NOT renamed (§11.10 Matinee safety)
    go_names = {o.read().m_Name for o in sf.objects.values() if o.type.name == "GameObject"}
    assert "Jetfire_GS_Leader2014" in go_names, f"Missing preserved root GO 'Jetfire_GS_Leader2014'! (got sample: {sorted(go_names)[:10]})"
    for pid in SMR_WPNS_PIDS:
        assert not sf.objects[pid].read_typetree()["m_Enabled"], f"Legacy weapon SMR {pid} is still enabled!"

    assert ab_tree is not None
    preload = [(int(p["m_FileID"]), int(p["m_PathID"])) for p in ab_tree.get("m_PreloadTable", [])]
    cursor = 0
    for cname, cinfo in ab_tree.get("m_Container", []):
        assert "starsaber_gs_leader2014" in cname.lower(), f"Unrenamed container key: {cname}"
        pidx, psize = int(cinfo["preloadIndex"]), int(cinfo["preloadSize"])
        assert pidx == cursor, f"Non-contiguous slice on {cname}: {pidx} != {cursor}"
        cursor += psize
        sl = preload[pidx : pidx + psize]
        _, expected_set = collect_closure(sf, [int(cinfo["asset"]["m_PathID"])])
        sl_set = set(sl)
        assert sl_set == expected_set, f"Preload mismatch on {cname}: missing={len(expected_set-sl_set)}, extra={len(sl_set-expected_set)}"

    print(f"[PASS] Gate 4 Integrity PASSED! objects={len(sf.objects)}, types={len(sf.types)}, preload={len(preload)}")


if __name__ == "__main__":
    build_starsaber_bundle()
