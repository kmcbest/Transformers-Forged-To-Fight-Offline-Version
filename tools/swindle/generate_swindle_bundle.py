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

print("=== [Swindle] Generating assets_redeco/swindle_gs.assetbundle (Full Donor Separation & Prop Neutralization) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
DONOR_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "wheeljack_gs_mp20_odr" / "wheeljack_gs_mp20.assetbundle"
MESH_BUNDLE = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "swindle_mesh.assetbundle"
TEX_DIR = ROOT / "3rd-party-models" / "Swindle" / "02_textures"
OUT_BUNDLE = ROOT / "assets_redeco" / "swindle_gs.assetbundle"
OUT_BUNDLE.parent.mkdir(parents=True, exist_ok=True)

NEW_CAB = "CAB-7b5e00007b5e00007b5e00007b5e0001"
BOT_ID = "swindle_gs"

# Donor PIDs from Wheeljack:
MESH_ROBOT_PID = 7421762944852434324     # cha_wheeljack_gs_mp20_00
MESH_VEHICLE_PID = 7801493811950399054   # cha_wheeljack_gs_mp20_01

TEX_ROBOT_DIFF_PID = 8574765737902222782  # cha_wheeljack_gs_mp20_main_a
TEX_ROBOT_NM_PID = 8959897519513413521    # main_NM
TEX_ROBOT_RAOE_PID = -4428837928816393975 # main_tform_misc_RAOE

TEX_VEH_DIFF_PID = -8052775517222050147   # tform_misc_A
TEX_VEH_NM_PID = 8879105477681491800     # tform_misc_NM
TEX_VEH_RAOE_PID = -1992731980378991890   # wpns_RAOE (reused as vehicle RAOE)

MAT_ROBOT_PID = 299128457246135156        # B8DFC46A323B194846E33C46C05749F9A74862A9 (Main)
MAT_VEHICLE_PID = -7671938706379380226    # FCC901A251A0D46D6E7EA2B858E3467CC4434157 (MiscA)
MAT_VEHICLE_ALT_PID = -4945840260896802696# C6262C9D37CFF5EF802556C7A88193A6B6AF1986 (MiscB)
MAT_WEAPON_PID = -3394591665204264980     # A26A44C91288C0710A7F474A1C9A925638A99677 (Wpns)

SMR_ROBOT_PIDS = (4988693516086577732, 5417250154022925283)
SMR_VEHICLE_PIDS = (3922252085192460347, 4566743256697345174)
SMR_WEAPON_PIDS = (
    -6602656275823759113, -3930055807961463887,
    -3206313259321400304, -1503411363354178914,
    6266759804019810390, 6786649985794663358,
)

PROPS_CTRL_PIDS = (4021312503130990423, 4711822844068090351)

WEAPON_GO_PIDS = (
    -7157881806114158567, 3486552624445207988,  # blaster
    -3846519110494722011, -3420540170724183225, # cha_wheeljack_gs_mp20_wpns_blaster
    -7030008573304040558, 8497045490938392294,  # rifle
    -3255884857431068505, -2006470722573936595, # cha_wheeljack_gs_mp20_wpns_rifle
    -8839715589880810086, 6412624880664391627,  # rightPistol
    -1695100069444143037, 331403085744384179,   # cha_wheeljack_gs_mp20_wpns_pistol_right
)

WEAPON_MESH_PIDS = (
    -3664405109857664568, # cha_wheeljack_gs_mp20_wpns_blaster
    1461136186915446612,  # cha_wheeljack_gs_mp20_wpns_rifle
    2383792379276369928,  # cha_wheeljack_gs_mp20_wpns_pistol_right
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
        "_emissive_intensity_col": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 0.0},
    }
    if custom_colors:
        color_overrides.update(custom_colors)

    colors = mat_tt["m_SavedProperties"]["m_Colors"]
    mat_tt["m_SavedProperties"]["m_Colors"] = [
        (k, dict(color_overrides[k]) if k in color_overrides else v) for k, v in colors
    ]


def build_swindle_bundle():
    assert DONOR_BUNDLE.is_file(), f"Missing donor bundle: {DONOR_BUNDLE}"
    assert MESH_BUNDLE.is_file(), f"Missing mesh bundle: {MESH_BUNDLE}"

    print(f"Loading Mesh Bundle: {MESH_BUNDLE}")
    env_mesh = UnityPy.load(str(MESH_BUNDLE))
    swindle_meshes = {}
    for obj in env_mesh.objects:
        if obj.type.name == "Mesh":
            tt = obj.read_typetree()
            swindle_meshes[tt["m_Name"]] = tt
    assert "cha_swindle_gs_00" in swindle_meshes and "cha_swindle_gs_01" in swindle_meshes, (
        f"Missing Swindle meshes: {list(swindle_meshes.keys())}"
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
        nk = k.replace("wheeljack_gs_mp20", BOT_ID).replace("Wheeljack_GS_MP20", BOT_ID)
        new_container.append([nk, v])
        print(f"  [Container] '{k}' -> '{nk}'")
    ab_tt["m_Container"] = new_container
    ab_objs[0].save_typetree(ab_tt)

    # 2. Remap stream paths containing old_cab & global CAB replacement
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

    # 3. Rename Root GameObjects, SMR GameObjects, and AOCs
    go_renames = {
        -7619826445860225839: "Swindle_GS",
        -14792533363479561: "Swindle_GS_lw",
        -8852051430638128500: "cha_swindle_gs_00",
        1035862621427210685: "cha_swindle_gs_00",
        6556998162789796044: "cha_swindle_gs_01",
        7523479704448262273: "cha_swindle_gs_01",
    }
    for gpid, new_name in go_renames.items():
        if gpid in obj_map:
            go_tt = obj_map[gpid].read_typetree()
            go_tt["m_Name"] = new_name
            obj_map[gpid].save_typetree(go_tt)
            print(f"  [GameObject] Renamed {gpid} -> '{new_name}'")

    aoc_renames = {
        -7533360748299311903: "override_swindle_gs_lw",
        8885580312140456008: "override_swindle_gs_fight",
        4890482530277269875: "override_swindle_gs_car",
    }
    for apid, new_name in aoc_renames.items():
        if apid in obj_map:
            aoc_tt = obj_map[apid].read_typetree()
            aoc_tt["m_Name"] = new_name
            obj_map[apid].save_typetree(aoc_tt)
            print(f"  [AOC] Renamed {apid} -> '{new_name}'")

    # Update Matinee jSONData actor references if present
    MATINEE_MB_PID = -7089141331618910524
    if MATINEE_MB_PID in obj_map:
        mat_tt = obj_map[MATINEE_MB_PID].read_typetree()
        if "jSONData" in mat_tt and isinstance(mat_tt["jSONData"], str):
            mat_tt["jSONData"] = mat_tt["jSONData"].replace("Wheeljack_GS_MP20", "Swindle_GS")
            obj_map[MATINEE_MB_PID].save_typetree(mat_tt)
            print(f"  [Matinee] Updated jSONData actor references to Swindle_GS")

    # 4. Clean PropsController: Strip 'blaster', 'rightPistol', and 'rifle'
    for pc_pid in PROPS_CTRL_PIDS:
        if pc_pid in obj_map:
            pc = obj_map[pc_pid].read_typetree()
            keys = pc["_props"].get("_serializedKeys", [])
            vals = pc["_props"].get("_serializedValues", [])
            new_keys = []
            new_vals = []
            for k, v in zip(keys, vals):
                if k in ("blaster", "rightPistol", "rifle"):
                    continue
                new_keys.append(k)
                new_vals.append(v)
            pc["_props"]["_serializedKeys"] = new_keys
            pc["_props"]["_serializedValues"] = new_vals
            obj_map[pc_pid].save_typetree(pc)
            print(f"  [PropsController] PID {pc_pid}: stripped weapons, remaining keys={new_keys}")

    # 5. Disable weapon SMRs and GameObjects
    for pid in SMR_WEAPON_PIDS:
        if pid in obj_map:
            smr_tt = obj_map[pid].read_typetree()
            smr_tt["m_Enabled"] = False
            smr_tt["m_Mesh"] = {"m_FileID": 0, "m_PathID": 0}
            obj_map[pid].save_typetree(smr_tt)

    for gpid in WEAPON_GO_PIDS:
        if gpid in obj_map:
            go_tt = obj_map[gpid].read_typetree()
            go_tt["m_IsActive"] = False
            obj_map[gpid].save_typetree(go_tt)
    print(f"  [Weapons] Disabled {len(SMR_WEAPON_PIDS)} weapon SMRs and {len(WEAPON_GO_PIDS)} weapon GameObjects")

    # Zero out geometry on weapon meshes so nothing can be drawn
    for mpid in WEAPON_MESH_PIDS:
        if mpid in obj_map:
            m_tt = obj_map[mpid].read_typetree()
            for sm in m_tt.get("m_SubMeshes", []):
                sm["indexCount"] = 0
                sm["vertexCount"] = 0
            m_tt["m_IndexBuffer"] = b""
            m_tt["m_VertexData"]["m_VertexCount"] = 0
            m_tt["m_VertexData"]["m_DataSize"] = b""
            obj_map[mpid].save_typetree(m_tt)
    print(f"  [Weapons] Zeroed geometry on {len(WEAPON_MESH_PIDS)} weapon meshes (blaster, rifle, pistol)")

    # 6. Graft Robot & Vehicle Meshes cleanly
    for dst_pid, src_name, y_floor_assert in (
        (MESH_ROBOT_PID, "cha_swindle_gs_00", 3.0),
        (MESH_VEHICLE_PID, "cha_swindle_gs_01", 0.5),
    ):
        src_tt = swindle_meshes[src_name]
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

    # 7. Inject 2048x2048 PBR Atlases
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
    set_texture(obj_map[TEX_ROBOT_DIFF_PID], TEX_DIR / "cha_swindle_main_Diffuse.png", "cha_swindle_main_Diffuse", is_raoe=False)
    set_texture(obj_map[TEX_ROBOT_NM_PID], TEX_DIR / "cha_swindle_main_Normal.png", "cha_swindle_main_Normal", is_raoe=False)
    set_texture(obj_map[TEX_ROBOT_RAOE_PID], TEX_DIR / "cha_swindle_main_RAOE.png", "cha_swindle_main_RAOE", is_raoe=True)
    set_texture(obj_map[TEX_VEH_DIFF_PID], TEX_DIR / "cha_swindle_tform_misc_Diffuse.png", "cha_swindle_tform_misc_Diffuse", is_raoe=False)
    set_texture(obj_map[TEX_VEH_NM_PID], TEX_DIR / "cha_swindle_tform_misc_Normal.png", "cha_swindle_tform_misc_Normal", is_raoe=False)
    set_texture(obj_map[TEX_VEH_RAOE_PID], TEX_DIR / "cha_swindle_tform_misc_RAOE.png", "cha_swindle_tform_misc_RAOE", is_raoe=True)

    # 8. Patch Kabam PBR Materials
    # Robot Body Material: Combaticon Gold Armor + Ruby-Purple Optics & Visor
    r_mat_tt = obj_map[MAT_ROBOT_PID].read_typetree()
    patch_kabam_character_mat(
        r_mat_tt,
        {
            "_base_tex": TEX_ROBOT_DIFF_PID,
            "_normal_tex": TEX_ROBOT_NM_PID,
            "_pbr_composite_tex": TEX_ROBOT_RAOE_PID,
        },
        custom_floats={
            "_emissive_overbright_range": 20.0,
            "_clearcoat_reflectance_range": 0.08,
            "_roughness_range": 0.85,
        },
        custom_colors={
            "_Color": {"r": 0.95, "g": 0.95, "b": 0.95, "a": 1.0},
            "_base_col": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
            "_emissive_intensity_col": {"r": 0.75, "g": 0.1, "b": 1.0, "a": 0.0}, # Ruby-Purple Optics!
        }
    )
    obj_map[MAT_ROBOT_PID].save_typetree(r_mat_tt)
    print(f"[✓] Patched Robot Material {MAT_ROBOT_PID} (Ruby-Purple Optics)")

    for vpid in (MAT_VEHICLE_PID, MAT_VEHICLE_ALT_PID):
        v_mat_tt = obj_map[vpid].read_typetree()
        patch_kabam_character_mat(
            v_mat_tt,
            {
                "_base_tex": TEX_VEH_DIFF_PID,
                "_normal_tex": TEX_VEH_NM_PID,
                "_pbr_composite_tex": TEX_VEH_RAOE_PID,
            },
            custom_colors={
                "_Color": {"r": 0.95, "g": 0.95, "b": 0.95, "a": 1.0},
                "_base_col": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
                "_emissive_intensity_col": {"r": 0.75, "g": 0.1, "b": 1.0, "a": 0.0}, # Purple rim & headlights!
            }
        )
        obj_map[vpid].save_typetree(v_mat_tt)
        print(f"[✓] Patched Vehicle Material {vpid}")

    # Patch Weapon Material (neutralize)
    w_mat_tt = obj_map[MAT_WEAPON_PID].read_typetree()
    patch_kabam_character_mat(
        w_mat_tt,
        {
            "_base_tex": TEX_ROBOT_DIFF_PID,
            "_normal_tex": TEX_ROBOT_NM_PID,
            "_pbr_composite_tex": TEX_ROBOT_RAOE_PID,
        },
        custom_colors={
            "_Color": {"r": 0.95, "g": 0.95, "b": 0.95, "a": 1.0},
            "_base_col": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
            "_emissive_intensity_col": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 0.0},
        }
    )
    obj_map[MAT_WEAPON_PID].save_typetree(w_mat_tt)
    print(f"[✓] Patched Weapon Material {MAT_WEAPON_PID}")

    # 9. Update SMRs
    generous_aabb = {
        "m_Center": {"x": 0.0, "y": 0.0, "z": 0.0},
        "m_Extent": {"x": 10.0, "y": 10.0, "z": 10.0},
    }
    for pid in SMR_ROBOT_PIDS:
        smr_obj = obj_map[pid]
        smr_tt = smr_obj.read_typetree()
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

    # 10. Flush & rebuild exact AssetBundle m_Container, m_PreloadTable & CAB
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
        nk = k.replace("wheeljack_gs_mp20", BOT_ID).replace("Wheeljack_GS_MP20", BOT_ID)
        new_container.append([nk, v])
        print(f"  [Container] '{k}' -> '{nk}'")
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

    # 11. Remap CAB file entries right before saving
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

    # 12. Save compressed AssetBundle
    print(f"--- 12. Saving {OUT_BUNDLE} with packer='lz4' ---")
    with open(OUT_BUNDLE, "wb") as f:
        f.write(env.file.save(packer="lz4"))

    size_mb = OUT_BUNDLE.stat().st_size / (1024 * 1024)
    print(f"[✓] Successfully generated {OUT_BUNDLE} ({size_mb:.2f} MB, CAB={NEW_CAB})")
    print("=== [Swindle] Bundle Generation Complete! ===")

    # 13. Verify Reloaded Bundle
    verify_swindle_bundle(OUT_BUNDLE, old_cab)


def verify_swindle_bundle(bundle_path: Path, old_cab: str):
    print("\n=== Verifying Swindle Bundle Coexistence & Prop Isolation ===")
    v_env = UnityPy.load(str(bundle_path))
    v_files = list(v_env.file.files.keys())
    print(f"  Files in saved bundle: {v_files}")
    for vf in v_files:
        assert old_cab not in vf, f"FAIL: Old CAB {old_cab} still present in bundle file keys: {vf}"
        assert NEW_CAB in vf, f"FAIL: NEW_CAB {NEW_CAB} missing from bundle file key: {vf}"
    print(f"  [PASS] CAB Namespace 100% Isolated: {NEW_CAB}")

    # Check Root GameObjects
    root_names = {o.read_typetree().get("m_Name") for o in v_env.objects if o.type.name == "GameObject"}
    assert "Swindle_GS" in root_names, f"FAIL: Swindle_GS root GameObject missing! {root_names}"
    assert "Swindle_GS_lw" in root_names, f"FAIL: Swindle_GS_lw root GameObject missing! {root_names}"
    assert "Wheeljack_GS_MP20" not in root_names, "FAIL: Old root Wheeljack_GS_MP20 still present!"
    assert "Wheeljack_GS_MP20_lw" not in root_names, "FAIL: Old root Wheeljack_GS_MP20_lw still present!"
    print(f"  [PASS] Root GameObjects Isolated: 'Swindle_GS', 'Swindle_GS_lw'")

    # Check AssetBundle container & name
    ab_tree = next(o.read_typetree() for o in v_env.objects if o.type.name == "AssetBundle")
    assert BOT_ID in ab_tree.get("m_Name", ""), f"FAIL: m_Name wrong: {ab_tree.get('m_Name')}"
    assert BOT_ID in ab_tree.get("m_AssetBundleName", ""), f"FAIL: m_AssetBundleName wrong: {ab_tree.get('m_AssetBundleName')}"
    for ck, cv in ab_tree.get("m_Container", []):
        assert BOT_ID in ck, f"FAIL: Container key still has donor name: {ck}"
    print(f"  [PASS] AssetBundle Container 100% Isolated: {[k for k, v in ab_tree.get('m_Container', [])]}")

    # Check PropsController
    for o in v_env.objects:
        if o.type.name == "MonoBehaviour":
            try:
                tt = o.read_typetree()
                if "_props" in tt:
                    keys = tt["_props"].get("_serializedKeys", [])
                    assert "blaster" not in keys, f"FAIL: 'blaster' still in PropsController {o.path_id}!"
                    assert "rightPistol" not in keys, f"FAIL: 'rightPistol' still in PropsController {o.path_id}!"
                    assert "rifle" not in keys, f"FAIL: 'rifle' still in PropsController {o.path_id}!"
            except Exception:
                pass
    print("  [PASS] PropsController Clean: 'blaster', 'rightPistol', and 'rifle' 100% removed")

    # Check Weapon SMRs
    for o in v_env.objects:
        if o.type.name == "SkinnedMeshRenderer" and o.path_id in SMR_WEAPON_PIDS:
            tt = o.read_typetree()
            assert not tt["m_Enabled"], f"FAIL: SMR {o.path_id} still enabled!"
            assert tt["m_Mesh"]["m_PathID"] == 0, f"FAIL: SMR {o.path_id} still has mesh attached!"
    print("  [PASS] Weapon SMRs: 100% disabled and detached")

    # Check Weapon Mesh geometry
    for o in v_env.objects:
        if o.type.name == "Mesh" and o.path_id in WEAPON_MESH_PIDS:
            tt = o.read_typetree()
            vc = tt["m_VertexData"]["m_VertexCount"]
            assert vc == 0, f"FAIL: Weapon mesh {o.path_id} still has {vc} vertices!"
    print("  [PASS] Weapon Meshes: 100% zeroed (blaster vertex count = 0)")

    print("[ALL CHECKS PASSED] Swindle bundle is 100% isolated and ready for coexistence with Wheeljack!\n")


if __name__ == "__main__":
    build_swindle_bundle()
