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

print("=== [Blast Off] Generating assets_redeco/blastoff_gs.assetbundle (Stage 4 Production with Complete CAB & Coexistence Isolation) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
DONOR_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatronus_gs_kabam_odr" / "megatronus_gs_kabam.assetbundle"
MESH_BUNDLE = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "blastoff_mesh.assetbundle"
TEX_DIR = ROOT / "3rd-party-models" / "BlastOff" / "02_textures"
OUT_BUNDLE = ROOT / "assets_redeco" / "blastoff_gs.assetbundle"
OUT_BUNDLE.parent.mkdir(parents=True, exist_ok=True)

NEW_CAB = "CAB-7b0f00007b0f00007b0f00007b0f0001"
BOT_ID = "blastoff_gs"

# Donor PIDs from Megatronus:
MESH_ROBOT_PID = -5997044220716342942     # cha_megatronus_gs_kabam_00
MESH_VEHICLE_PID = 3108608853924595936    # cha_megatronus_gs_kabam_01

TEX_ROBOT_DIFF_PID = -6344108430470549335  # cha_megatronus_gs_kabam_main_a
TEX_ROBOT_NM_PID = -1036783645484789854    # main_NM
TEX_ROBOT_RAOE_PID = 5460940998983682046   # main_tform_misc_RAOE

TEX_VEH_DIFF_PID = 8885233584587298903     # tform_misc_A
TEX_VEH_NM_PID = 3555490749204138483       # tform_misc_NM
TEX_VEH_RAOE_PID = -3825908263228568922    # wpns_RAOE (reused as vehicle RAOE)

MAT_ROBOT_PID = -7624887367596881865       # 5B53266140A5AE6E02BAD843694A3B1F9D18EE73 (Main)
MAT_VEHICLE_PID = -1880645829306736032     # B0BFFABA061E55FB81D18649F2BF6F19F1108D6C (Veh)
MAT_VEHICLE_ALT_PID = 1599971990248223050  # CF5887BA03FACFAF6D6C3EE7DEAF23FECD3FCB23 (Veh Alt)
MAT_WEAPONS_PID = -286209363010135206      # ACD996109B6D950FBD6C6F68D7DE2F0F06E534BC (Wpns)

SMR_ROBOT_PIDS = (-7365343560906614841, -7018793243482077698)
SMR_VEHICLE_PIDS = (2199531639279207482, 4183817700869375963)


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
        for k, v in list(tree_obj.items()):
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


def patch_kabam_character_mat(mat_tt: dict, tex_overrides: dict, custom_floats: dict = None, custom_colors: dict = None):
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
        "_metallic": 1.0,
        "_ambient_occlusion_intensity": 1.0,
        "_cutoff": 0.5,
        "_emission_scaler": 1.0,
        "_roughness_intensity": 1.0,
        "_specular_intensity": 1.0,
        "_diffuse_wrap_intensity": 0.0,
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
        "_emissive_intensity_col": {"r": 0.8, "g": 0.15, "b": 1.0, "a": 0.0},
    }
    if custom_colors:
        color_overrides.update(custom_colors)

    colors = mat_tt["m_SavedProperties"]["m_Colors"]
    mat_tt["m_SavedProperties"]["m_Colors"] = [
        (k, dict(color_overrides[k]) if k in color_overrides else v) for k, v in colors
    ]


def build_blastoff_bundle():
    assert DONOR_BUNDLE.is_file(), f"Missing donor bundle: {DONOR_BUNDLE}"
    assert MESH_BUNDLE.is_file(), f"Missing mesh bundle: {MESH_BUNDLE}"

    print(f"Loading Mesh Bundle: {MESH_BUNDLE}")
    env_mesh = UnityPy.load(str(MESH_BUNDLE))
    blastoff_meshes = {}
    for obj in env_mesh.objects:
        if obj.type.name == "Mesh":
            tt = obj.read_typetree()
            blastoff_meshes[tt["m_Name"]] = tt
    assert "cha_blastoff_gs_00" in blastoff_meshes and "cha_blastoff_gs_01" in blastoff_meshes, (
        f"Missing Blast Off meshes: {list(blastoff_meshes.keys())}"
    )

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
        nk = k.replace("megatronus_gs_kabam", BOT_ID).replace("Megatronus_GS_Kabam", BOT_ID)
        new_container.append([nk, v])
        print(f"  [Container] '{k}' -> '{nk}'")
    ab_tt["m_Container"] = new_container
    ab_objs[0].save_typetree(ab_tt)

    # 2. Remap stream paths containing old_cab & global CAB replacement in typetrees
    replaced_pids = {
        ab_objs[0].path_id,
        MESH_ROBOT_PID, MESH_VEHICLE_PID,
        TEX_ROBOT_DIFF_PID, TEX_ROBOT_NM_PID, TEX_ROBOT_RAOE_PID,
        TEX_VEH_DIFF_PID, TEX_VEH_NM_PID, TEX_VEH_RAOE_PID,
    }
    remapped_streams = 0
    for o in env.objects:
        if o.path_id in replaced_pids:
            continue
        try:
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
                remapped_streams += 1
            replace_str_in_tree(tt, old_cab, NEW_CAB)
            replace_str_in_tree(tt, old_cab_low, new_cab_low)
            o.save_typetree(tt)
        except Exception:
            pass
    print(f"[*] Remapped external stream paths and CAB strings on {remapped_streams} objects")

    # 3. Rename Root GameObjects and SMR GameObjects to eliminate identity collision with donor
    go_renames = {
        4878828359455866604: "Blastoff_GS",
        -9118908274669910453: "Blastoff_GS_lw",
        -1683702312459398693: "cha_blastoff_gs_00",
        8278229407078479105: "cha_blastoff_gs_00",
        4741281376311026684: "cha_blastoff_gs_01",
        6941743978463812848: "cha_blastoff_gs_01",
    }
    for pid, new_go_name in go_renames.items():
        if pid in obj_map:
            tt = obj_map[pid].read_typetree()
            old_name = tt.get("m_Name", "")
            tt["m_Name"] = new_go_name
            obj_map[pid].save_typetree(tt)
            print(f"  [GO Rename] {pid}: '{old_name}' -> '{new_go_name}'")

    # 3b. Scale character_model container uniformly (0.82x) to achieve true isometric scaling without deforming mesh or fingers
    # 3427378212942980363 is character_model in Blastoff_GS (combat)
    # -2861782103288704020 is character_model in Blastoff_GS_lw (showroom)
    SCALE_ISOMETRIC = 0.82  # Target height 10.53m (shorter than Brawl 12.58m and Onslaught 10.61m)
    for cm_pid in (3427378212942980363, -2861782103288704020):
        if cm_pid in obj_map:
            tt = obj_map[cm_pid].read_typetree()
            tt["m_LocalScale"] = {"x": SCALE_ISOMETRIC, "y": SCALE_ISOMETRIC, "z": SCALE_ISOMETRIC}
            obj_map[cm_pid].save_typetree(tt)
            print(f"  [character_model Scale] {cm_pid}: set to ({SCALE_ISOMETRIC}, {SCALE_ISOMETRIC}, {SCALE_ISOMETRIC})")

    # 4. Graft Robot & Vehicle Meshes cleanly
    for dst_pid, src_name, y_floor_assert in (
        (MESH_ROBOT_PID, "cha_blastoff_gs_00", 3.0),
        (MESH_VEHICLE_PID, "cha_blastoff_gs_01", 0.5),
    ):
        src_tt = blastoff_meshes[src_name]
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

    # 5. Inject 2048x2048 PBR Atlases
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
    set_texture(obj_map[TEX_ROBOT_DIFF_PID], TEX_DIR / "cha_blastoff_main_Diffuse.png", "cha_blastoff_main_Diffuse", is_raoe=False)
    set_texture(obj_map[TEX_ROBOT_NM_PID], TEX_DIR / "cha_blastoff_main_Normal_unity.png", "cha_blastoff_main_Normal", is_raoe=False)
    set_texture(obj_map[TEX_ROBOT_RAOE_PID], TEX_DIR / "cha_blastoff_main_RAOE.png", "cha_blastoff_main_RAOE", is_raoe=True)
    set_texture(obj_map[TEX_VEH_DIFF_PID], TEX_DIR / "cha_blastoff_tform_misc_Diffuse.png", "cha_blastoff_tform_misc_Diffuse", is_raoe=False)
    set_texture(obj_map[TEX_VEH_NM_PID], TEX_DIR / "cha_blastoff_tform_misc_Normal_unity.png", "cha_blastoff_tform_misc_Normal", is_raoe=False)
    set_texture(obj_map[TEX_VEH_RAOE_PID], TEX_DIR / "cha_blastoff_tform_misc_RAOE.png", "cha_blastoff_tform_misc_RAOE", is_raoe=True)

    # 6. Patch Kabam PBR Materials
    # Robot Body Material: Combaticon Brown/Gold Armor + Glowing Purple Optics & Visor
    r_mat_tt = obj_map[MAT_ROBOT_PID].read_typetree()
    patch_kabam_character_mat(
        r_mat_tt,
        {
            "_base_tex": TEX_ROBOT_DIFF_PID,
            "_normal_tex": TEX_ROBOT_NM_PID,
            "_pbr_composite_tex": TEX_ROBOT_RAOE_PID,
        },
        custom_floats={
            "_emissive_overbright_range": 15.0,
            "_emissive_range": 1.0,
            "_clearcoat_reflectance_range": 0.08,
            "_roughness_range": 0.85,
        },
        custom_colors={
            "_Color": {"r": 0.95, "g": 0.95, "b": 0.95, "a": 1.0},
            "_base_col": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
            "_emissive_intensity_col": {"r": 0.62, "g": 0.02, "b": 1.0, "a": 0.0}, # Rich Neon Violet/Purple without white washout!
        }
    )
    obj_map[MAT_ROBOT_PID].save_typetree(r_mat_tt)
    print(f"[✓] Patched Robot Material {MAT_ROBOT_PID} (Vivid Neon Purple Optics & Vents)")

    for vpid in (MAT_VEHICLE_PID, MAT_VEHICLE_ALT_PID):
        v_mat_tt = obj_map[vpid].read_typetree()
        patch_kabam_character_mat(
            v_mat_tt,
            {
                "_base_tex": TEX_VEH_DIFF_PID,
                "_normal_tex": TEX_VEH_NM_PID,
                "_pbr_composite_tex": TEX_VEH_RAOE_PID,
            },
            custom_floats={
                "_emissive_overbright_range": 15.0,
                "_emissive_range": 1.0,
                "_clearcoat_reflectance_range": 0.08,
                "_roughness_range": 0.85,
            },
            custom_colors={
                "_Color": {"r": 0.95, "g": 0.95, "b": 0.95, "a": 1.0},
                "_base_col": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
                "_emissive_intensity_col": {"r": 0.62, "g": 0.02, "b": 1.0, "a": 0.0},
            }
        )
        obj_map[vpid].save_typetree(v_mat_tt)
        print(f"[✓] Patched Vehicle Material {vpid}")

    # 7. Update SMRs
    generous_aabb = {
        "m_Center": {"x": 0.0, "y": 6.0, "z": 0.0},
        "m_Extent": {"x": 10.0, "y": 10.0, "z": 10.0},
    }
    for pid in SMR_ROBOT_PIDS:
        smr_obj = obj_map[pid]
        smr_tt = smr_obj.read_typetree()
        smr_tt["m_Mesh"] = {"m_FileID": 0, "m_PathID": MESH_ROBOT_PID}
        smr_tt["m_Materials"] = [
            {"m_FileID": 0, "m_PathID": MAT_ROBOT_PID},
        ]
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
    print(f"[✓] Configured SMRs: Robot & Vehicle active, bound to single-submesh materials.")

    # 8. Flush & rebuild exact AssetBundle m_Container, m_PreloadTable & CAB
    print("[*] Rebuilding exact AssetBundle m_Container, m_PreloadTable & CAB...")
    raw_saved = env.file.save(packer="none")
    env = UnityPy.load(io.BytesIO(raw_saved))
    sf = [f for f in env.file.files.values() if hasattr(f, "objects")][0]
    ab_obj = next(o for o in sf.objects.values() if o.type.name == "AssetBundle")
    ab_tree = ab_obj.read_typetree()

    ab_tree["m_Name"] = f"data/{BOT_ID}_odr/{BOT_ID}.assetbundle"
    ab_tree["m_AssetBundleName"] = f"data/{BOT_ID}_odr/{BOT_ID}.assetbundle"
    new_container = []
    for k, v in ab_tree.get("m_Container", []):
        nk = k.replace("megatronus_gs_kabam", BOT_ID).replace("Megatronus_GS_Kabam", BOT_ID)
        new_container.append([nk, v])
        print(f"  [Container Rebuild] '{k}' -> '{nk}'")
    ab_tree["m_Container"] = new_container

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

    # 9. Remap CAB file entries right before saving
    print(f"[*] Remapping env.file.files keys from {old_cab} to {NEW_CAB}...")
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
        print(f"  env.file.files: '{k}' -> '{nk}'")
    env.file.files = new_files

    # 10. Save compressed AssetBundle
    print(f"--- 10. Saving {OUT_BUNDLE} with packer='lz4' ---")
    with open(OUT_BUNDLE, "wb") as f:
        f.write(env.file.save(packer="lz4"))

    size_mb = OUT_BUNDLE.stat().st_size / (1024 * 1024)
    print(f"[✓] Successfully generated {OUT_BUNDLE} ({size_mb:.2f} MB, CAB={NEW_CAB})")
    print("=== [Blast Off] Bundle Generation Complete! ===")

    # 11. Verify Reloaded Bundle
    verify_blastoff_bundle(OUT_BUNDLE, old_cab)


def verify_blastoff_bundle(bundle_path: Path, old_cab: str):
    print("\n=== Verifying Blast Off Bundle Coexistence & Identity Isolation ===")
    v_env = UnityPy.load(str(bundle_path))
    v_files = list(v_env.file.files.keys())
    print(f"  Files in saved bundle: {v_files}")
    for vf in v_files:
        assert old_cab not in vf, f"FAIL: Old CAB {old_cab} still present in bundle file keys: {vf}"
        assert NEW_CAB in vf, f"FAIL: NEW_CAB {NEW_CAB} missing from bundle file key: {vf}"
    print(f"  [PASS] CAB Namespace 100% Isolated: {NEW_CAB}")

    # Check Root GameObjects
    root_names = {o.read_typetree().get("m_Name") for o in v_env.objects if o.type.name == "GameObject"}
    assert "Blastoff_GS" in root_names, f"FAIL: Blastoff_GS root GameObject missing! {root_names}"
    assert "Blastoff_GS_lw" in root_names, f"FAIL: Blastoff_GS_lw root GameObject missing! {root_names}"
    assert "Megatronus_GS_Kabam" not in root_names, "FAIL: Old root Megatronus_GS_Kabam still present!"
    assert "Megatronus_GS_Kabam_lw" not in root_names, "FAIL: Old root Megatronus_GS_Kabam_lw still present!"
    print(f"  [PASS] Root GameObjects Isolated: 'Blastoff_GS', 'Blastoff_GS_lw'")

    # Check AssetBundle container & name
    ab_tree = next(o.read_typetree() for o in v_env.objects if o.type.name == "AssetBundle")
    assert BOT_ID in ab_tree.get("m_Name", ""), f"FAIL: m_Name wrong: {ab_tree.get('m_Name')}"
    assert BOT_ID in ab_tree.get("m_AssetBundleName", ""), f"FAIL: m_AssetBundleName wrong: {ab_tree.get('m_AssetBundleName')}"
    for ck, cv in ab_tree.get("m_Container", []):
        assert BOT_ID in ck, f"FAIL: Container key still has donor name: {ck}"
    print(f"  [PASS] AssetBundle Container 100% Isolated: {[k for k, v in ab_tree.get('m_Container', [])]}")

    # Check Meshes
    mesh_counts = {o.read_typetree().get("m_Name"): o.read_typetree().get("m_VertexData", {}).get("m_VertexCount", 0)
                   for o in v_env.objects if o.type.name == "Mesh"}
    assert "cha_blastoff_gs_00" in mesh_counts and mesh_counts["cha_blastoff_gs_00"] > 4000, "cha_blastoff_gs_00 invalid!"
    assert "cha_blastoff_gs_01" in mesh_counts and mesh_counts["cha_blastoff_gs_01"] > 4000, "cha_blastoff_gs_01 invalid!"
    print(f"  [PASS] Meshes Verified: {mesh_counts}")

    print("[ALL CHECKS PASSED] Blast Off bundle is 100% isolated and ready for coexistence with Megatronus!\n")


if __name__ == "__main__":
    build_blastoff_bundle()
