import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import io
from pathlib import Path
from collections import deque
from PIL import Image
import UnityPy
from UnityPy.enums import TextureFormat

print("=== [Brawl] Generating assets_redeco/brawl_gs.assetbundle (Gate 4 Production) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
DONOR_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_cin_rotf_odr" / "megatron_cin_rotf.assetbundle"
MESH_BUNDLE = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "brawl_mesh.assetbundle"
MOVES_BUNDLE = ROOT / "assets_netflix" / "moves.assetbundle"
PROC_BUNDLE = ROOT / "assets_netflix" / "character_anim_procedural.assetbundle"
TEX_DIR = ROOT / "3rd-party-models" / "Brawl" / "02_textures"
OUT_BUNDLE = ROOT / "assets_redeco" / "brawl_gs.assetbundle"

NEW_CAB = "CAB-7b7a00007b7a00007b7a00007b7a0001"
BOT_ID = "brawl_gs"

MESH_ROBOT_PID = 8927022796776742380
MESH_VEHICLE_PID = -9025351850097636016

TEX_ROBOT_DIFF_PID = 7575930771601290721
TEX_ROBOT_NM_PID = 42717178677652158
TEX_ROBOT_RAOE_PID = -8652859075577142890

TEX_VEH_DIFF_PID = 2805008792520890735
TEX_VEH_NM_PID = -3665651547192902677
TEX_VEH_RAOE_PID = -4057584031439743300

MAT_ROBOT_PID = 2758279787216392959
MAT_VEHICLE_PID = -8143696719442631496

SMR_ROBOT_PIDS = (-1713043385139994820, 6657504797783083318)
SMR_VEHICLE_PIDS = (-4076617426109914192, -2983655943056242676)

FIGHT_AOC_PID = -8652027754329276107
MOVESET_PID = 8437944761280972800


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


def patch_kabam_character_mat(mat_tt: dict, tex_overrides: dict):
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
        "_roughness_range": 0.92,
        "_clearcoat_reflectance_range": 0.03,
        "_emissive_range": 0.0,
        "_emissive_none": 0.0,
        "_emissive_overbright_range": 24.0,
    }
    floats = mat_tt["m_SavedProperties"]["m_Floats"]
    existing_keys = {k for k, _ in floats}
    new_floats = [(k, float_overrides[k] if k in float_overrides else v) for k, v in floats]
    for k, v in float_overrides.items():
        if k not in existing_keys:
            new_floats.append((k, v))
    mat_tt["m_SavedProperties"]["m_Floats"] = new_floats

    # Preserve Diffuse colors faithfully (removing Megatron's 0.25x grey darkening & red/blue emissive tints)
    color_overrides = {
        "_Color": {"r": 0.92, "g": 0.92, "b": 0.92, "a": 1.0},
        "_base_col": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
        "_emissive_intensity_col": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 0.0},
    }
    colors = mat_tt["m_SavedProperties"]["m_Colors"]
    mat_tt["m_SavedProperties"]["m_Colors"] = [
        (k, dict(color_overrides[k]) if k in color_overrides else v) for k, v in colors
    ]


def build_brawl_bundle():
    assert DONOR_BUNDLE.is_file(), f"Missing donor bundle: {DONOR_BUNDLE}"
    assert MESH_BUNDLE.is_file(), f"Missing mesh bundle: {MESH_BUNDLE}"

    # Verify external Move & Clip PIDs exist before injecting!
    moves_pids = set()
    if MOVES_BUNDLE.is_file():
        env_mv = UnityPy.load(str(MOVES_BUNDLE))
        moves_pids = {o.path_id for o in env_mv.objects}
    proc_pids = set()
    if PROC_BUNDLE.is_file():
        env_pr = UnityPy.load(str(PROC_BUNDLE))
        proc_pids = {o.path_id for o in env_pr.objects}

    print(f"Loading Mesh Bundle: {MESH_BUNDLE}")
    env_mesh = UnityPy.load(str(MESH_BUNDLE))
    brawl_meshes = {}
    for obj in env_mesh.objects:
        if obj.type.name == "Mesh":
            tt = obj.read_typetree()
            brawl_meshes[tt["m_Name"]] = tt
    assert "cha_brawl_gs_00" in brawl_meshes and "cha_brawl_gs_01" in brawl_meshes, f"Missing Brawl meshes: {list(brawl_meshes.keys())}"

    print(f"Loading Donor Bundle: {DONOR_BUNDLE}")
    env = UnityPy.load(str(DONOR_BUNDLE))
    obj_map = {o.path_id: o for o in env.objects}

    cab_files = [k for k in env.file.files.keys() if k.lower().startswith("cab-") and "." not in k]
    assert cab_files, "Could not find CAB file in donor bundle!"
    old_cab = cab_files[0]
    old_cab_low = old_cab.lower()
    new_cab_low = NEW_CAB.lower()
    print(f"[*] Remapping CAB: {old_cab} -> {NEW_CAB}")

    # 1. Rewrite AssetBundle container & m_AssetBundleName
    ab_objs = [o for o in env.objects if o.type.name == "AssetBundle"]
    assert len(ab_objs) == 1
    ab_tt = ab_objs[0].read_typetree()
    ab_tt["m_Name"] = f"data/{BOT_ID}_odr/{BOT_ID}.assetbundle"
    ab_tt["m_AssetBundleName"] = f"data/{BOT_ID}_odr/{BOT_ID}.assetbundle"
    new_container = []
    for k, v in ab_tt["m_Container"]:
        nk = k.replace("megatron_cin_rotf", BOT_ID).replace("Megatron_Cin_ROTF", BOT_ID)
        new_container.append([nk, v])
        print(f"  [Container] '{k}' -> '{nk}'")
    ab_tt["m_Container"] = new_container
    ab_objs[0].save_typetree(ab_tt)

    # 2. Remap stream paths containing old_cab
    replaced_pids = {
        MESH_ROBOT_PID, MESH_VEHICLE_PID,
        TEX_ROBOT_DIFF_PID, TEX_ROBOT_NM_PID, TEX_ROBOT_RAOE_PID,
        TEX_VEH_DIFF_PID, TEX_VEH_NM_PID, TEX_VEH_RAOE_PID,
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

    # 3. Graft Robot & Vehicle Meshes cleanly WITHOUT corrupting Stream 2 or bindpose counts
    # Both cha_brawl_gs_00 (39 bones) and cha_brawl_gs_01 (37 bones, 100% on COG idx 21) were
    # built against Megatron's exact SMR bindposes & bone indices in BuildBrawlInspectionScene.cs!
    for dst_pid, src_name, y_floor_assert in (
        (MESH_ROBOT_PID, "cha_brawl_gs_00", 3.0),
        (MESH_VEHICLE_PID, "cha_brawl_gs_01", 0.5),
    ):
        src_tt = brawl_meshes[src_name]
        dst_obj = obj_map[dst_pid]
        dst_tt = dst_obj.read_typetree()

        keep_hashes = list(dst_tt["m_BoneNameHashes"])
        keep_root_hash = int(dst_tt["m_RootBoneNameHash"])
        assert len(src_tt["m_BindPose"]) == len(keep_hashes), (
            f"{src_name} bindpose len {len(src_tt['m_BindPose'])} != donor hashes len {len(keep_hashes)}"
        )

        c_y = src_tt["m_LocalAABB"]["m_Center"]["y"]
        assert c_y > y_floor_assert, f"{src_name} m_LocalAABB center.y={c_y} failed height guard (>{y_floor_assert})"
        vcount = src_tt["m_VertexData"]["m_VertexCount"]
        assert vcount > 5000, f"{src_name} vertexCount={vcount} too low!"

        dst_tt["m_Name"] = src_name
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
        print(f"[✓] Grafted Mesh '{src_name}': PID={dst_pid}, verts={vcount}, bones={len(keep_hashes)}, centerY={c_y:.3f}")

    # 4. Inject 2048x2048 PBR Atlases (Diffuse RGBA32, Kabam NM.B Metallic Normal RGBA32, Strict RGB24 RAOE)
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

    print("Injecting PBR Atlased Textures:")
    set_texture(obj_map[TEX_ROBOT_DIFF_PID], TEX_DIR / "cha_brawl_main_Diffuse.png", "cha_brawl_main_a", is_raoe=False)
    set_texture(obj_map[TEX_ROBOT_NM_PID], TEX_DIR / "cha_brawl_main_Normal.png", "cha_brawl_main_NM", is_raoe=False)
    set_texture(obj_map[TEX_ROBOT_RAOE_PID], TEX_DIR / "cha_brawl_main_RAOE.png", "cha_brawl_main_RAOE", is_raoe=True)
    set_texture(obj_map[TEX_VEH_DIFF_PID], TEX_DIR / "cha_brawl_tform_misc_Diffuse.png", "cha_brawl_tform_misc_A", is_raoe=False)
    set_texture(obj_map[TEX_VEH_NM_PID], TEX_DIR / "cha_brawl_tform_misc_Normal.png", "cha_brawl_tform_misc_NM", is_raoe=False)
    set_texture(obj_map[TEX_VEH_RAOE_PID], TEX_DIR / "cha_brawl_tform_misc_RAOE.png", "cha_brawl_tform_misc_RAOE", is_raoe=True)

    # 5. Patch Kabam PBR Materials (Scale=(1,1), Offset=(0,0), True Colors, Emissive Calibration)
    r_mat_tt = obj_map[MAT_ROBOT_PID].read_typetree()
    patch_kabam_character_mat(r_mat_tt, {
        "_base_tex": TEX_ROBOT_DIFF_PID,
        "_normal_tex": TEX_ROBOT_NM_PID,
        "_pbr_composite_tex": TEX_ROBOT_RAOE_PID,
    })
    obj_map[MAT_ROBOT_PID].save_typetree(r_mat_tt)
    print(f"[✓] Patched Robot Material {MAT_ROBOT_PID} (Color=0.92, NM.B metallic, Scale=(1,1))")

    v_mat_tt = obj_map[MAT_VEHICLE_PID].read_typetree()
    patch_kabam_character_mat(v_mat_tt, {
        "_base_tex": TEX_VEH_DIFF_PID,
        "_normal_tex": TEX_VEH_NM_PID,
        "_pbr_composite_tex": TEX_VEH_RAOE_PID,
    })
    obj_map[MAT_VEHICLE_PID].save_typetree(v_mat_tt)
    print(f"[✓] Patched Vehicle Material {MAT_VEHICLE_PID} (Color=0.92, NM.B metallic, Scale=(1,1))")

    # 6. Update SMRs cleanly while preserving all 37 Vehicle Donor Bones!
    generous_aabb = {
        "m_Center": {"x": 0.0, "y": 0.0, "z": 0.0},
        "m_Extent": {"x": 10.0, "y": 10.0, "z": 10.0},
    }
    for pid in SMR_ROBOT_PIDS:
        smr_obj = obj_map[pid]
        smr_tt = smr_obj.read_typetree()
        smr_tt["m_Materials"] = [{"m_FileID": 0, "m_PathID": MAT_ROBOT_PID}]
        smr_tt["m_AABB"] = generous_aabb
        smr_tt["m_UpdateWhenOffscreen"] = True
        smr_obj.save_typetree(smr_tt)

    for pid in SMR_VEHICLE_PIDS:
        smr_obj = obj_map[pid]
        smr_tt = smr_obj.read_typetree()
        assert len(smr_tt["m_Bones"]) == 37, f"Vehicle SMR {pid} bones len={len(smr_tt['m_Bones'])}"
        smr_tt["m_Mesh"] = {"m_FileID": 0, "m_PathID": MESH_VEHICLE_PID}
        smr_tt["m_Materials"] = [{"m_FileID": 0, "m_PathID": MAT_VEHICLE_PID}]
        smr_tt["m_AABB"] = generous_aabb
        smr_tt["m_UpdateWhenOffscreen"] = True
        smr_tt["m_Enabled"] = False
        smr_obj.save_typetree(smr_tt)
    print(f"[✓] Updated Robot & Vehicle SMRs cleanly (all 37 Vehicle bones preserved).")

    # 7. Rewire MoveSet (Optimus Prime Melee + Grindor S1; Megatron S2 & S3 kept)
    moveset_obj = obj_map[MOVESET_PID]
    ms_tt = moveset_obj.read_typetree()
    moveset_remap = {
        "Base.LightAttack01": ("move_brawler_attack_light_01", 1253534208046253437),
        "Base.LightAttack02": ("move_brawler_attack_light_02", -5739966146551603970),
        "Base.LightAttack03": ("move_brawler_attack_light_03", 4395974147525317656),
        "Base.LightAttack04": ("move_brawler_attack_light_04", 2626987635675716951),
        "Base.MediumAttack01": ("move_brawler_attack_medium_02", 8863364277361988242),
        "Base.MediumAttack02": ("move_brawler_attack_medium_01", -4699933484649724452),
        "Base.SpecialAttack01": ("move_grindor_special_01", -3216243042041681492),
    }
    remapped_moves = 0
    for m in ms_tt.get("_moves", []):
        state = m.get("_animStateName", "")
        if state in moveset_remap:
            new_name, new_pid = moveset_remap[state]
            if moves_pids:
                assert new_pid in moves_pids, f"Missing move PID {new_pid} ({new_name}) in moves.assetbundle!"
            m["_name"] = new_name
            m["_asset"]["m_FileID"] = 2
            m["_asset"]["m_PathID"] = new_pid
            remapped_moves += 1
            print(f"  [MoveSet] {state:<22} -> {new_name} (PID={new_pid})")
    assert remapped_moves == len(moveset_remap)
    moveset_obj.save_typetree(ms_tt)

    # 8. Rewire Fight AOC
    fight_aoc_obj = obj_map[FIGHT_AOC_PID]
    aoc_tt = fight_aoc_obj.read_typetree()
    fight_aoc_clip_map = {
        3149807030316843707: -4436169046226876345,   # brawler_normal_attackLight_01_jab
        1493990355315399625: -6097583617840917686,   # brawler_normal_attackLight_02_jab
        -8618744054794967589: 7516767159529040107,   # brawler_normal_attackLight_03_uppcut
        7758611357151580349: -7211214383178331208,   # brawler_normal_attackLight_04_frontkick
        424597727730099647: -7925637137891657471,    # brawler_normal_attackMedium_02_shouldercharge
        1189595235236326705: -7521383106890636294,   # brawler_normal_attackMedium_01_backhand
        6889857548200950017: -2481087801159876808,   # Grindor_Normal_attackSpecial_01
    }
    remapped_aoc = 0
    for c in aoc_tt.get("m_Clips", []):
        orig_pid = c.get("m_OriginalClip", {}).get("m_PathID")
        if orig_pid in fight_aoc_clip_map:
            new_clip_pid = fight_aoc_clip_map[orig_pid]
            if proc_pids:
                assert new_clip_pid in proc_pids, f"Missing clip PID {new_clip_pid} in procedural bundle!"
            c["m_OverrideClip"]["m_FileID"] = 3
            c["m_OverrideClip"]["m_PathID"] = new_clip_pid
            remapped_aoc += 1
    assert remapped_aoc == len(fight_aoc_clip_map), f"Remapped {remapped_aoc} != {len(fight_aoc_clip_map)}"
    fight_aoc_obj.save_typetree(aoc_tt)
    print(f"[✓] Remapped {remapped_aoc} Fight AOC clips (all verified in character_anim_procedural.assetbundle).")

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

    verify_brawl_bundle_integrity(OUT_BUNDLE)


def verify_brawl_bundle_integrity(bundle_path: Path):
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

    assert ab_tree is not None
    preload = [(int(p["m_FileID"]), int(p["m_PathID"])) for p in ab_tree.get("m_PreloadTable", [])]
    cursor = 0
    for cname, cinfo in ab_tree.get("m_Container", []):
        assert "brawl_gs" in cname.lower(), f"Unrenamed container key: {cname}"
        pidx, psize = int(cinfo["preloadIndex"]), int(cinfo["preloadSize"])
        assert pidx == cursor, f"Non-contiguous slice on {cname}: {pidx} != {cursor}"
        cursor += psize
        sl = preload[pidx : pidx + psize]
        _, expected_set = collect_closure(sf, [int(cinfo["asset"]["m_PathID"])])
        sl_set = set(sl)
        assert sl_set == expected_set, f"Preload mismatch on {cname}: missing={len(expected_set-sl_set)}, extra={len(sl_set-expected_set)}"

    print(f"[PASS] Gate 4 Integrity PASSED! objects={len(sf.objects)}, types={len(sf.types)}, preload={len(preload)}")


if __name__ == "__main__":
    build_brawl_bundle()
