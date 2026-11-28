#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_wildrider_assets.py

Stage 4 Production AssetBundle Grafting for Decepticon Wildrider (莽撞) using
the 3D Transformers: Alliance model grafted onto Prowl (prowl_gs_deluxe2016)
donor rig & preserving Wildrider's combat moveset:
  - Normal / Heavy attacks: Prowl (Preserved)
  - S1: Galvatron (Galvatron_GS_attackSpecial_01 / move_galvatron_special_01)
  - S2: Motormaster (motormaster_gs_attackSpecial_02 / move_motormaster_special_02)
  - S3: Prowl (prowl_gs_delux_attackSpecial_03_transformed / move_prowl_special_03 Preserved)
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
WR_DIR = ROOT / "3rd-party-models" / "WildRider"
MESH_BUNDLE = WR_DIR / "04_unity_bundles" / "wildrider_mesh.assetbundle"
TEX_DIR = WR_DIR / "02_textures"

BOT_ID = "wildrider_gs_deluxe2016"
NEW_CAB = "CAB-wildrider2016gs00001122334455"

# Prowl donor PIDs
MESH_ROBOT_PID = 1087879341501063368       # cha_prowl_gs_deluxe2016_00 (50 bones)
MESH_VEH_PID = 7295630905050477747         # cha_prowl_gs_deluxe2016_01 (26 bones)
MESH_GUN_PID = -7947891575776091319        # cha_prowl_gs_deluxe2016_wpns_shotgun (1 bone)

TEX_MAIN_DIFF_PID = 8699654113595830490    # cha_prowl_gs_deluxe2016_main_a
TEX_MAIN_NM_PID = -5650952820722940311     # main_NM (NM.B = Kabam metallic)
TEX_MAIN_RAOE_PID = -1377069345250401912   # main_tform_misc_RAOE (RGB)

MAT_MAIN_PID = 7500203752916154549         # 558FC8...
MAT_MISC_PID = -7118460493794104175
MAT_VEH_PID = 8471270994157717165
MAT_WPNS_PID = -7952106015500823235

SMR_ROBOT_PIDS = (-6772043811355011877, 7725939028951263287)
SMR_VEH_PIDS = (4296255992570358690, 6486922263386044909)
SMR_SHOTGUN_PIDS = (-4002460477049825425, 4165745812915728584)
SMR_HIDE_WEAPON_PIDS = (
    -1938348056671453853, 7981783545579534422,   # baton
    1900885066796996306, 2654023469926453624,    # chain
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


def generate_wildrider_assets(apk_path: str | None = None, output_dir: str = "assets_redeco") -> None:
    out_dir = Path(output_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    assert MESH_BUNDLE.is_file(), f"Missing Stage 3 mesh bundle: {MESH_BUNDLE}"
    for tf in ("cha_wildrider_main_Diffuse.png", "cha_wildrider_main_Normal.png", "cha_wildrider_main_RAOE.png"):
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

    print("[*] Loading component assetbundles & Stage 3 WildRider mesh bundle...")
    prowl_bytes = load_bundle("prowl_gs_deluxe2016_odr/prowl_gs_deluxe2016.assetbundle")
    galvatron_bytes = load_bundle("galvatron_gs_voyager2016_odr/galvatron_gs_voyager2016.assetbundle")
    procedural_bytes = load_bundle("characters_procedural_odr/character_anim_procedural.assetbundle")

    p_env = UnityPy.load(prowl_bytes)
    g_env = UnityPy.load(galvatron_bytes)
    proc_env = UnityPy.load(procedural_bytes)
    m_env = UnityPy.load(str(MESH_BUNDLE))

    wr_meshes = {}
    for obj in m_env.objects:
        if obj.type.name == "Mesh":
            tt = obj.read_typetree()
            wr_meshes[tt["m_Name"]] = tt
    for req in ("cha_prowl_gs_deluxe2016_00", "cha_prowl_gs_deluxe2016_01", "cha_prowl_gs_deluxe2016_wpns_shotgun"):
        assert req in wr_meshes, f"Missing '{req}' in {MESH_BUNDLE}: {list(wr_meshes.keys())}"

    # 1. Extract Galvatron S1 & Motormaster S2 AnimationClips (preserve existing combat moveset!)
    print("[*] Extracting Galvatron S1 and Motormaster S2 animation clips...")
    clip_s1 = None
    for obj in g_env.objects:
        if obj.path_id == -1265828487359043164 and obj.type.name == "AnimationClip":
            clip_s1 = obj.read_typetree()
            clip_s1["m_Name"] = "wildrider_GS_attackSpecial_01"
            break
    assert clip_s1 is not None, "Could not find Galvatron S1 clip!"

    clip_s2 = None
    for obj in proc_env.objects:
        if obj.path_id == -5547817616214473576 and obj.type.name == "AnimationClip":
            clip_s2 = obj.read_typetree()
            clip_s2["m_Name"] = "wildrider_GS_attackSpecial_02"
            break
    assert clip_s2 is not None, "Could not find Motormaster S2 clip!"

    p_asset = list(p_env.assets)[0]
    obj_map = {o.path_id: o for o in p_env.objects}

    cab_files = [k for k in p_env.file.files.keys() if k.lower().startswith("cab-") and "." not in k]
    assert cab_files, "Could not find CAB file in Prowl donor bundle!"
    old_cab = cab_files[0]
    old_cab_low = old_cab.lower()
    new_cab_low = NEW_CAB.lower()
    print(f"[*] Remapping CAB: {old_cab} -> {NEW_CAB}")

    PID_S1 = 991001
    PID_S2 = 991002
    template_clip = [o for o in p_asset.objects.values() if o.type.name == "AnimationClip"][0]
    for pid, ctree in ((PID_S1, clip_s1), (PID_S2, clip_s2)):
        new_obj = copy.copy(template_clip)
        new_obj.path_id = pid
        replace_str_in_tree(ctree, old_cab, new_cab_low)
        new_obj.save_typetree(ctree)
        p_asset.objects[pid] = new_obj
    print("[+] Injected Galvatron S1 (991001) & Motormaster S2 (991002)")

    # 2. Graft 3D Meshes (Robot 00, Vehicle 01, Shotgun Gun) cleanly
    mesh_specs = (
        (MESH_ROBOT_PID, "cha_prowl_gs_deluxe2016_00", "cha_wildrider_gs_deluxe2016_00", 3.0),
        (MESH_VEH_PID, "cha_prowl_gs_deluxe2016_01", "cha_wildrider_gs_deluxe2016_01", 0.5),
        (MESH_GUN_PID, "cha_prowl_gs_deluxe2016_wpns_shotgun", "cha_wildrider_gs_deluxe2016_wpns_shotgun", -10.0),
    )
    for dst_pid, src_name, dst_name, y_floor in mesh_specs:
        src_tt = copy.deepcopy(wr_meshes[src_name])
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

    # 3. Inject 2048x2048 PBR Atlases
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

    print("[*] Injecting 2048x2048 WildRider PBR textures...")
    set_texture(obj_map[TEX_MAIN_DIFF_PID], TEX_DIR / "cha_wildrider_main_Diffuse.png", "cha_wildrider_main_Diffuse", is_raoe=False)
    set_texture(obj_map[TEX_MAIN_NM_PID], TEX_DIR / "cha_wildrider_main_Normal.png", "cha_wildrider_main_Normal", is_raoe=False)
    set_texture(obj_map[TEX_MAIN_RAOE_PID], TEX_DIR / "cha_wildrider_main_RAOE.png", "cha_wildrider_main_RAOE", is_raoe=True)

    # 4. Patch character/vehicle/weapon materials to single WildRider PBR atlas & Crimson Red eyes
    tex_overrides = {
        "_base_tex": TEX_MAIN_DIFF_PID,
        "_normal_tex": TEX_MAIN_NM_PID,
        "_pbr_composite_tex": TEX_MAIN_RAOE_PID,
    }
    for mpid in (MAT_MAIN_PID, MAT_MISC_PID, MAT_VEH_PID, MAT_WPNS_PID):
        m_obj = obj_map.get(mpid)
        if m_obj is None:
            continue
        m_tt = m_obj.read_typetree()
        patch_kabam_character_mat(m_tt, tex_overrides)
        m_obj.save_typetree(m_tt)
    print("[✓] Patched Materials (Scale=(1,1), Offset=(0,0), Crimson Red Eyes Emissive=(1.0, 0.08, 0.08))")

    # 5. Configure SMRs (1 submesh each -> MAT_MAIN_PID) & hide Prowl's Baton/Chain props
    generous_aabb = {"m_Center": {"x": 0.0, "y": 0.0, "z": 0.0}, "m_Extent": {"x": 10.0, "y": 10.0, "z": 10.0}}
    hidden_transform_pids = set()
    for pid in SMR_ROBOT_PIDS + SMR_VEH_PIDS + SMR_SHOTGUN_PIDS:
        smr_obj = obj_map[pid]
        smr_tt = smr_obj.read_typetree()
        smr_tt["m_Materials"] = [{"m_FileID": 0, "m_PathID": MAT_MAIN_PID}]
        smr_tt["m_AABB"] = generous_aabb
        smr_tt["m_UpdateWhenOffscreen"] = True
        smr_obj.save_typetree(smr_tt)

    for pid in SMR_HIDE_WEAPON_PIDS:
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
    print(f"[✓] Updated SMRs and silenced {len(SMR_HIDE_WEAPON_PIDS)} donor baton/chain renderers")

    # 6. Update Fight AOC, MoveSet, PropsController (clear Baton renderers), Container, & Stream paths
    replaced_pids = {
        MESH_ROBOT_PID, MESH_VEH_PID, MESH_GUN_PID,
        TEX_MAIN_DIFF_PID, TEX_MAIN_NM_PID, TEX_MAIN_RAOE_PID,
    }
    for obj in list(p_env.objects):
        if obj.path_id == -8799352062880271755 and obj.type.name == "AnimatorOverrideController":
            tree = obj.read_typetree()
            clips = tree.get("m_Clips", [])
            clips[4]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_S1}
            clips[5]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_S2}
            tree["m_Clips"] = clips
            replace_str_in_tree(tree, old_cab, new_cab_low)
            obj.save_typetree(tree)
            print("[+] Configured Wildrider Fight AOC (S1=Galvatron, S2=Motormaster, S3=Prowl, Normals=Prowl)!")

        elif obj.path_id == 4685508596578817746 and obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            moves = tree.get("_moves", [])
            moves[6]["_name"] = "move_galvatron_special_01"
            moves[6]["_asset"] = {"m_FileID": 6, "m_PathID": -5882940919102495494}
            moves[7]["_name"] = "move_motormaster_special_02"
            moves[7]["_asset"] = {"m_FileID": 6, "m_PathID": -564276376835722605}
            tree["_moves"] = moves
            replace_str_in_tree(tree, old_cab, new_cab_low)
            obj.save_typetree(tree)
            print("[+] Configured Wildrider MoveSet (S1=Galvatron, S2=Motormaster)!")

        elif obj.type.name == "AssetBundle":
            tree = obj.read_typetree()
            ab_name = f"data/{BOT_ID}_odr/{BOT_ID}.assetbundle"
            tree["m_Name"] = ab_name
            tree["m_AssetBundleName"] = ab_name
            new_container = []
            for item in tree.get("m_Container", []):
                path_str = item[0].replace("prowl_gs_deluxe2016", BOT_ID).replace("Prowl_GS_Deluxe2016", BOT_ID)
                new_container.append([path_str, item[1]])
            tree["m_Container"] = new_container
            replace_str_in_tree(tree, old_cab, new_cab_low)
            obj.save_typetree(tree)

        elif obj.type.name in ("AudioClip", "Texture2D", "Mesh") and obj.path_id not in replaced_pids:
            tree = obj.read_typetree()
            replace_str_in_tree(tree, old_cab, new_cab_low)
            obj.save_typetree(tree)

        elif obj.type.name in ("AnimatorOverrideController", "AnimatorController", "MonoBehaviour"):
            try:
                tree = obj.read_typetree()
                if "_props" in tree:
                    keys = tree["_props"].get("_serializedKeys", [])
                    vals = tree["_props"].get("_serializedValues", [])
                    for k, v in zip(keys, vals):
                        if k == "Baton" and isinstance(v, dict):
                            v["_renderers"] = []
                replace_str_in_tree(tree, old_cab, new_cab_low)
                obj.save_typetree(tree)
            except Exception:
                pass

    # 7. Flush & rebuild exact AssetBundle m_PreloadTable slices & CAB filenames
    print("[*] Rebuilding exact AssetBundle m_PreloadTable & CAB filenames...")
    raw_saved = p_env.file.save(packer="none")
    p_env = UnityPy.load(io.BytesIO(raw_saved))
    sf = [f for f in p_env.file.files.values() if hasattr(f, "objects")][0]
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
    for subfname, subf in p_env.file.files.items():
        nk = subfname.replace(old_cab, NEW_CAB).replace(old_cab_low, new_cab_low)
        if hasattr(subf, "name") and isinstance(subf.name, str):
            subf.name = subf.name.replace(old_cab, NEW_CAB).replace(old_cab_low, new_cab_low)
        new_files[nk] = subf
    p_env.file.files = new_files

    target_bundle = out_dir / f"{BOT_ID}.assetbundle"
    target_bundle.write_bytes(p_env.file.save(packer="lz4"))
    size_mb = target_bundle.stat().st_size / (1024 * 1024)
    print(f"[✓] Saved {target_bundle} ({size_mb:.2f} MB, packer='lz4', CAB={NEW_CAB})")


def main():
    parser = argparse.ArgumentParser(description="Generate Wildrider (莽撞) Stage 4 production assetbundle.")
    parser.add_argument("--output", "-o", default="assets_redeco", help="Output directory")
    args = parser.parse_args()
    generate_wildrider_assets(output_dir=args.output)


if __name__ == "__main__":
    main()
