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

print("=== [Sideswipe] Generating assets_redeco/sideswipe_cin_rotf.assetbundle (Stage 4 Production) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
DONOR_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "barricade_cin_dotm_odr" / "barricade_cin_dotm.assetbundle"
BONECRUSHER_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "bonecrusher_cin_rotf_odr" / "bonecrusher_cin_rotf.assetbundle"
MESH_BUNDLE = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "sideswipe_mesh.assetbundle"
TEX_DIR = ROOT / "3rd-party-models" / "Sideswipe" / "02_textures"
OUT_BUNDLE = ROOT / "assets_redeco" / "sideswipe_cin_rotf.assetbundle"

NEW_CAB = "CAB-7c7a00007c7a00007c7a00007c7a0001"
BOT_ID = "sideswipe_cin_rotf"

# Donor PIDs from Barricade:
MESH_ROBOT_PID = -3704701387459868067     # cha_barricade_cin_dotm_00
MESH_VEHICLE_PID = 6308912028819720523    # cha_barricade_cin_dotm_01
MESH_PISTOL_PID = -3372704949266581090
MESH_NUNCHUCK_PID = 7798518008873760914

TEX_ROBOT_DIFF_PID = 3751059866409916181  # cha_barricade_cin_dotm_main_a
TEX_ROBOT_NM_PID = -4998872889953564635   # main_NM
TEX_ROBOT_RAOE_PID = -3333073556533086091 # main_tform_misc_RAOE

TEX_VEH_DIFF_PID = 3825025440751305356    # tform_misc_A
TEX_VEH_NM_PID = -2397216155036329258     # tform_misc_NM
TEX_VEH_RAOE_PID = -5347487439809782      # wpns_RAOE (reused as vehicle RAOE)

MAT_ROBOT_PID = 6327179545371057975       # ECAF095CB70F4D4901654C149984C590798F6248 (Main)
MAT_VEHICLE_PID = -6718098035160789545    # FA2079035EB4A008B99E197DA9ED0138F06CC7E4 (Vehicle)
MAT_VEHICLE_ALT_PID = 5681344350055115988 # 5CC014EA22DD22EB6B83B654B5655448D5F7771E
MAT_WEAPON_PID = 5508013112655075757      # 63468FEB7734E97E61AC878C34663D358604F60B

SMR_ROBOT_PIDS = (-8424474371625542742, 4175356167918878908)
SMR_VEHICLE_PIDS = (-6985830099829588956, 4971384506341640743)
SMR_WEAPON_PIDS = (-7461690504352263342, -5711057110573806536, -4879794911437009642, -1551473720530804150)

FIGHT_AOC_PID = -2047393535863576714
NUNCHUCK_AOC_PID = -7666204224280581023
CAR_AOC_PID = 9188181967379678347


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
        "_roughness_range": 0.85,
        "_clearcoat_reflectance_range": 0.04,
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
        "_Color": {"r": 0.95, "g": 0.95, "b": 0.95, "a": 1.0},
        "_base_col": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
        "_emissive_intensity_col": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 0.0},
    }
    colors = mat_tt["m_SavedProperties"]["m_Colors"]
    mat_tt["m_SavedProperties"]["m_Colors"] = [
        (k, dict(color_overrides[k]) if k in color_overrides else v) for k, v in colors
    ]


def build_sideswipe_bundle():
    assert DONOR_BUNDLE.is_file(), f"Missing donor bundle: {DONOR_BUNDLE}"
    assert MESH_BUNDLE.is_file(), f"Missing mesh bundle: {MESH_BUNDLE}"
    assert BONECRUSHER_BUNDLE.is_file(), f"Missing Bonecrusher bundle: {BONECRUSHER_BUNDLE}"

    print(f"Loading Mesh Bundle: {MESH_BUNDLE}")
    env_mesh = UnityPy.load(str(MESH_BUNDLE))
    sideswipe_meshes = {}
    for obj in env_mesh.objects:
        if obj.type.name == "Mesh":
            tt = obj.read_typetree()
            sideswipe_meshes[tt["m_Name"]] = tt
    assert "cha_sideswipe_cin_rotf_00" in sideswipe_meshes and "cha_sideswipe_cin_rotf_01" in sideswipe_meshes, (
        f"Missing Sideswipe meshes: {list(sideswipe_meshes.keys())}"
    )

    # Load Bonecrusher_Normal_locoRun clip from Bonecrusher bundle
    print(f"Loading Bonecrusher locomotion run from: {BONECRUSHER_BUNDLE}")
    env_bc = UnityPy.load(str(BONECRUSHER_BUNDLE))
    bc_run_clip_tt = None
    for obj in env_bc.objects:
        if obj.type.name == "AnimationClip":
            tt = obj.read_typetree()
            if tt.get("m_Name") == "Bonecrusher_Normal_locoRun":
                bc_run_clip_tt = tt
                print(f"[✓] Extracted Bonecrusher_Normal_locoRun: pid={obj.path_id}")
                break
    assert bc_run_clip_tt is not None, "Failed to find Bonecrusher_Normal_locoRun in Bonecrusher bundle!"

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
        nk = k.replace("barricade_cin_dotm", BOT_ID).replace("Barricade_Cin_DOTM", BOT_ID)
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

    # 3. Graft Robot & Vehicle Meshes cleanly
    for dst_pid, src_name, y_floor_assert in (
        (MESH_ROBOT_PID, "cha_sideswipe_cin_rotf_00", 3.0),
        (MESH_VEHICLE_PID, "cha_sideswipe_cin_rotf_01", 0.5),
    ):
        src_tt = sideswipe_meshes[src_name]
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
        assert vcount > 4000, f"{src_name} vertexCount={vcount} too low!"

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

    # 4. Inject 2048x2048 PBR Atlases
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
    set_texture(obj_map[TEX_ROBOT_DIFF_PID], TEX_DIR / "cha_sideswipe_main_Diffuse.png", "cha_sideswipe_main_Diffuse", is_raoe=False)
    set_texture(obj_map[TEX_ROBOT_NM_PID], TEX_DIR / "cha_sideswipe_main_Normal.png", "cha_sideswipe_main_Normal", is_raoe=False)
    set_texture(obj_map[TEX_ROBOT_RAOE_PID], TEX_DIR / "cha_sideswipe_main_RAOE.png", "cha_sideswipe_main_RAOE", is_raoe=True)
    set_texture(obj_map[TEX_VEH_DIFF_PID], TEX_DIR / "cha_sideswipe_tform_misc_Diffuse.png", "cha_sideswipe_tform_misc_Diffuse", is_raoe=False)
    set_texture(obj_map[TEX_VEH_NM_PID], TEX_DIR / "cha_sideswipe_tform_misc_Normal.png", "cha_sideswipe_tform_misc_Normal", is_raoe=False)
    set_texture(obj_map[TEX_VEH_RAOE_PID], TEX_DIR / "cha_sideswipe_tform_misc_RAOE.png", "cha_sideswipe_tform_misc_RAOE", is_raoe=True)

    # 5. Patch Kabam PBR Materials
    r_mat_tt = obj_map[MAT_ROBOT_PID].read_typetree()
    patch_kabam_character_mat(r_mat_tt, {
        "_base_tex": TEX_ROBOT_DIFF_PID,
        "_normal_tex": TEX_ROBOT_NM_PID,
        "_pbr_composite_tex": TEX_ROBOT_RAOE_PID,
    })
    obj_map[MAT_ROBOT_PID].save_typetree(r_mat_tt)
    print(f"[✓] Patched Robot Material {MAT_ROBOT_PID}")

    for vpid in (MAT_VEHICLE_PID, MAT_VEHICLE_ALT_PID):
        v_mat_tt = obj_map[vpid].read_typetree()
        patch_kabam_character_mat(v_mat_tt, {
            "_base_tex": TEX_VEH_DIFF_PID,
            "_normal_tex": TEX_VEH_NM_PID,
            "_pbr_composite_tex": TEX_VEH_RAOE_PID,
        })
        obj_map[vpid].save_typetree(v_mat_tt)
        print(f"[✓] Patched Vehicle Material {vpid}")

    w_mat_tt = obj_map[MAT_WEAPON_PID].read_typetree()
    patch_kabam_character_mat(w_mat_tt, {
        "_base_tex": TEX_ROBOT_DIFF_PID,
        "_normal_tex": TEX_ROBOT_NM_PID,
        "_pbr_composite_tex": TEX_ROBOT_RAOE_PID,
    })
    obj_map[MAT_WEAPON_PID].save_typetree(w_mat_tt)
    print(f"[✓] Patched Weapon Material {MAT_WEAPON_PID}")

    # 6. Update SMRs
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
        smr_tt["m_Mesh"] = {"m_FileID": 0, "m_PathID": MESH_VEHICLE_PID}
        smr_tt["m_Materials"] = [{"m_FileID": 0, "m_PathID": MAT_VEHICLE_PID}]
        smr_tt["m_AABB"] = generous_aabb
        smr_tt["m_UpdateWhenOffscreen"] = True
        smr_tt["m_Enabled"] = False
        smr_obj.save_typetree(smr_tt)

    # Disable Barricade's standalone weapon SMRs (Sideswipe blades are integrated into forearm mesh)
    for pid in SMR_WEAPON_PIDS:
        smr_obj = obj_map[pid]
        smr_tt = smr_obj.read_typetree()
        smr_tt["m_Enabled"] = False
        smr_obj.save_typetree(smr_tt)
    print(f"[✓] Configured SMRs: Robot & Vehicle active, Barricade weapon props disabled.")

    # 7. Inject Bonecrusher Skating Locomotion Clip into Bundle
    # We replace an unused or duplicate animation clip, or reuse Barricade's own fight run clip slot
    # Let's check Barricade's fight AOC:
    fight_aoc_obj = obj_map[FIGHT_AOC_PID]
    aoc_tt = fight_aoc_obj.read_typetree()

    # Find the current run override in fight AOC:
    # orig=8310889249667241404 is the generic locoRun
    # In Barricade's fight AOC, orig=8310889249667241404 was mapped to -938117991230282500 (external feral run)
    # We will inject Bonecrusher_Normal_locoRun into a local AnimationClip slot!
    # Let's find an AnimationClip in Barricade bundle to replace with Bonecrusher_Normal_locoRun:
    clip_objs = [o for o in env.objects if o.type.name == "AnimationClip"]
    print(f"Found {len(clip_objs)} AnimationClips in Barricade bundle.")

    # We can inject Bonecrusher's clip into an existing clip object, e.g. a heavy attack or weapon clip
    # Or create/overwrite one:
    target_clip_obj = None
    for c in clip_objs:
        ctt = c.read_typetree()
        cname = ctt.get("m_Name", "")
        if "wpns" in cname.lower() or "nunchuck" in cname.lower() or "pistol" in cname.lower():
            target_clip_obj = c
            print(f"Selected weapon clip {cname} (pid={c.path_id}) for Bonecrusher run clip injection.")
            break
    if target_clip_obj is None:
        target_clip_obj = clip_objs[0]

    # Save Bonecrusher_Normal_locoRun into target_clip_obj:
    bc_run_pid = target_clip_obj.path_id
    target_clip_obj.save_typetree(bc_run_clip_tt)
    print(f"[✓] Injected 'Bonecrusher_Normal_locoRun' into PID {bc_run_pid}")

    # Rewire AOCs to use Bonecrusher run clip:
    for aoc_pid in (FIGHT_AOC_PID, NUNCHUCK_AOC_PID, CAR_AOC_PID):
        if aoc_pid in obj_map:
            a_obj = obj_map[aoc_pid]
            att = a_obj.read_typetree()
            for cl in att.get("m_Clips", []):
                orig_id = cl.get("m_OriginalClip", {}).get("m_PathID")
                if orig_id == 8310889249667241404:
                    cl["m_OverrideClip"]["m_FileID"] = 0
                    cl["m_OverrideClip"]["m_PathID"] = bc_run_pid
                    print(f"  [AOC {aoc_pid}] Mapped locoRun (8310889249667241404) -> Bonecrusher locoRun ({bc_run_pid})")
            a_obj.save_typetree(att)

    # 8. Flush & rebuild exact AssetBundle m_PreloadTable & CAB
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

    verify_sideswipe_bundle_integrity(OUT_BUNDLE)


def verify_sideswipe_bundle_integrity(bundle_path: Path):
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

    assert ab_tree is not None, "Missing AssetBundle object!"
    container_keys = [k for k, _ in ab_tree.get("m_Container", [])]
    print(f"Verified {len(container_keys)} Container entries:")
    for ck in container_keys:
        print(f"  Container: {ck}")
        assert BOT_ID in ck, f"Container key '{ck}' does not contain '{BOT_ID}'"

    print("\n[PASS] All Gate 4 Bundle Integrity Checks Passed Cleanly!")


if __name__ == "__main__":
    build_sideswipe_bundle()
