#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_blitzwing_bundle.py
Builds assets_redeco/blitzwing_gs.assetbundle by grafting Blitzwing's baked Robot/Vehicle meshes
and Kabam PBR textures onto Megatron (megatron_gs_leader2015) donor bundle:
  - Strict adherence to THIRD_PARTY_3D_MODEL_PIPELINE.md Section 11.9:
    * RAOE: R=Roughness, G=AO, B=Emissive (strictly 0.0, eliminating White Supernova blowout!)
    * Normal: RG=Normal, B=Metallic (0 for armor, 95 for neutral dark grey metal skeleton/treads)
    * Materials: _emissive_none=1.0, _emissive_overbright_range=0.0, _emissive_intensity_col=0,
                 _Color=0.72, _base_col=0.72 (prevent specular clipping on cartoon paint)
  - Strict adherence to TRIPLE_CHANGER_ARCHITECTURE_GUIDE.md:
    * Showcase screen: ONLY Tank mode displayed ("transformed", InitFlags=8), Jet hidden (InitFlags=0)
    * Combat mode: Tank mode ("transformed") vs Jet mode ("transformed_2") dynamically driven by hook.c
    * Tank mesh bound 100% to COG bone (identity bindpose, zero distortion from Megatron limb animations)
    * Jet mesh bound 100% to COG bone (identity bindpose, zero distortion from Megatron arm mount)
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import copy
from pathlib import Path
TOOLS_BW = Path(__file__).resolve().parent
if str(TOOLS_BW) not in sys.path:
    sys.path.insert(0, str(TOOLS_BW))

from PIL import Image
import UnityPy
from UnityPy.enums import TextureFormat
from UnityPy.streams import EndianBinaryReader

ROOT = Path(r"E:\Agent\TFTF-blender")
ROOT_GM = Path(r"E:\Agent\TFTF")
DONOR_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_gs_leader2015_odr" / "megatron_gs_leader2015.assetbundle"
CAP_BUNDLE = ROOT / "assets_netflix" / "character_audio_procedural.assetbundle"
MESH_BUNDLE = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "blitzwing_mesh.assetbundle"
TEX_DIR = ROOT / "tools" / "blitzwing" / "atlased_textures"
OUT_BUNDLE = ROOT / "assets_redeco" / "blitzwing_gs.assetbundle"

NEW_CAB = "CAB-7b4900007b4900007b4900007b490001"

# Exact donor PIDs from megatron_gs_leader2015.assetbundle
MESH_ROBOT_PID = 3463271531423751283
MESH_VEHICLE_PID = 8396146535644667895
MESH_JET_PID = -6391917038499381755
MESH_GUN_PID = -3217264854751393828
MESH_SWORD_PID = -8888888888888888911  # Cloned dedicated PID (since MESH_JET_PID took staticCannon's mesh!)

SMR_ROBOT_PIDS = (-8610528988658655013, -4173104293130818967)
SMR_VEHICLE_PIDS = (2138194849323017337, 4626197738286450028)
SMR_JET_PIDS = (-7481134504555158405, 3992037002325232027)
SMR_GUN_PIDS = (7267330081541926865, -6758328762533593613)
SMR_SWORD_PIDS = (4561093141354196631, 8495398593779105175)

PROPS_SHOWCASE_PID = -8490429130128858862
PROPS_COMBAT_PID = -3021806434293993593

# Exact COG Transforms under transformed & cannon
SHOWCASE_TANK_COG_PID = -7543220954911659241
COMBAT_TANK_COG_PID = -7942071043123098758

SHOWCASE_JET_COG_PID = 9041275945456695869
COMBAT_JET_COG_PID = 4936350875999462921

MAT_ROBOT_PID = 8075787426780741283
MAT_VEHICLE_PID = 1722215546450231611
MAT_SECONDARY_PID = 8175378592256487408
MAT_WPNS_PID = -9117353815363826346

TEX_ROBOT_DIFF_PID = 1215366976128313824
TEX_ROBOT_NM_PID = 3871664243983383179
TEX_ROBOT_RAOE_PID = 4263548866435318379

TEX_VEH_DIFF_PID = -1301823324166226518
TEX_VEH_NM_PID = -3812894415876002048
TEX_VEH_RAOE_PID = -8835585150668275629

TEX_WPNS_DIFF_PID = -3077338877283958343
TEX_WPNS_NM_PID = -669899812022169322
TEX_WPNS_RAOE_PID = -8888888888888888912  # Cloned dedicated PID (since TEX_VEH_RAOE_PID took wpns_RAOE!)

AUDIO_GUN_FIRE_PIDS = (941368445438371770, -3153366270135029083, 6494165064040424260, -9094754406746335516)


def identity_matrix():
    return {
        "e00": 1.0, "e01": 0.0, "e02": 0.0, "e03": 0.0,
        "e10": 0.0, "e11": 1.0, "e12": 0.0, "e13": 0.0,
        "e20": 0.0, "e21": 0.0, "e22": 1.0, "e23": 0.0,
        "e30": 0.0, "e31": 0.0, "e32": 0.0, "e33": 1.0,
    }


def cog_inverse_matrix():
    # Inverse of Reference/COG animated rotation q=(0.5, 0.5, -0.5, -0.5)
    # In all vehicle animations (Showcase idle, Tank heavy, Jet heavy), Reference/COG has
    # localRotation = (0.5, 0.5, -0.5, -0.5) -> M_tf_from_cog: e02=-1, e10=1, e21=-1, e33=1.
    # Setting BindPose[0] = M_tf_from_cog^-1 guarantees M_tf_from_cog * BindPose[0] = Identity,
    # keeping pre-transformed vertices (x, z, -y) upright on Y>=0 and facing +Z forward!
    return {
        "e00": 0.0, "e01": 1.0, "e02": 0.0, "e03": 0.0,
        "e10": 0.0, "e11": 0.0, "e12": -1.0, "e13": 0.0,
        "e20": -1.0, "e21": 0.0, "e22": 0.0, "e23": 0.0,
        "e30": 0.0, "e31": 0.0, "e32": 0.0, "e33": 1.0,
    }


def patch_kabam_character_mat(mat: dict, diff_pid: int, nm_pid: int, raoe_pid: int, metallic: float, is_wpn: bool = False):
    tex_map = {
        "_base_tex": diff_pid,
        "_normal_tex": nm_pid,
        "_pbr_composite_tex": raoe_pid,
    }
    for name, entry in mat["m_SavedProperties"]["m_TexEnvs"]:
        if name in tex_map:
            entry["m_Texture"] = {"m_FileID": 0, "m_PathID": tex_map[name]}
            entry["m_Scale"] = {"x": 1.0, "y": 1.0}
            entry["m_Offset"] = {"x": 0.0, "y": 0.0}

    if is_wpn:
        float_overrides = {
            "_Mode": 3.0,
            "_ZWrite": 1.0,
            "_metallic_range": 0.0,            # Driven by NM.B mask
            "_metallic_toggle": 0.0,
            "_roughness_range": 0.90,
            "_clearcoat_reflectance_range": 0.04,
            "_emissive_none": 0.0,              # Enable emissive shader branch for glowing sword blade!
            "_emissive_range": 1.0,             # Enable emissive intensity scaling
            "_emissive_overbright_range": 35.0, # Onslaught (袭击) gold standard overbright (was 16.0)
        }
    else:
        float_overrides = {
            "_Mode": 3.0,
            "_ZWrite": 1.0,
            "_metallic_range": 0.0,            # Let NM.B mask drive localized metalness without washing armor white
            "_metallic_toggle": 0.0,
            "_roughness_range": 0.90,
            "_clearcoat_reflectance_range": 0.03,
            "_emissive_none": 1.0,              # Disable emissive shader branch completely
            "_emissive_range": 0.0,
            "_emissive_overbright_range": 0.0,  # Zero emissive overbright
        }
    floats = mat["m_SavedProperties"]["m_Floats"]
    existing_keys = {k for k, _ in floats}
    new_floats = [(k, float_overrides[k] if k in float_overrides else v) for k, v in floats]
    for k, v in float_overrides.items():
        if k not in existing_keys:
            new_floats.append((k, v))
    mat["m_SavedProperties"]["m_Floats"] = new_floats

    if is_wpn:
        main_color = {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}
        base_col = {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}
        emissive_col = {"r": 0.75, "g": 0.10, "b": 1.0, "a": 0.0} # Onslaught (袭击) neon purple color (0.75, 0.10, 1.00)
        color_overrides = {
            "_Color": main_color,
            "_base_col": base_col,
            "_EmissionColor": emissive_col,
            "_emissive_intensity_col": emissive_col,
        }
    else:
        # Keep _Color >= 0.72 (passes Gate 4 >= 0.65 threshold) & _base_col = 0.56 so sand-tan paint stays faithful instead of over-exposing white
        main_color = {"r": 0.72, "g": 0.72, "b": 0.72, "a": 1.0}
        base_col = {"r": 0.56, "g": 0.56, "b": 0.56, "a": 1.0}
        zero_emissive = {"r": 0.0, "g": 0.0, "b": 0.0, "a": 0.0}
        color_overrides = {
            "_Color": main_color,
            "_base_col": base_col,
            "_EmissionColor": zero_emissive,
            "_emissive_intensity_col": zero_emissive,
        }
    colors = mat["m_SavedProperties"]["m_Colors"]
    existing_c_keys = {k for k, _ in colors}
    new_colors = [(k, dict(color_overrides[k]) if k in color_overrides else v) for k, v in colors]
    for k, v in color_overrides.items():
        if k not in existing_c_keys:
            new_colors.append((k, dict(v)))
    mat["m_SavedProperties"]["m_Colors"] = new_colors


def neutralize_emissive_only(mat: dict):
    float_overrides = {
        "_emissive_none": 1.0,
        "_emissive_range": 0.0,
        "_emissive_overbright_range": 0.0,
    }
    floats = mat["m_SavedProperties"]["m_Floats"]
    existing_keys = {k for k, _ in floats}
    new_floats = [(k, float_overrides[k] if k in float_overrides else v) for k, v in floats]
    for k, v in float_overrides.items():
        if k not in existing_keys:
            new_floats.append((k, v))
    mat["m_SavedProperties"]["m_Floats"] = new_floats

    zero_emissive = {"r": 0.0, "g": 0.0, "b": 0.0, "a": 0.0}
    color_overrides = {
        "_EmissionColor": zero_emissive,
        "_emissive_intensity_col": zero_emissive,
    }
    colors = mat["m_SavedProperties"]["m_Colors"]
    existing_c_keys = {k for k, _ in colors}
    new_colors = [(k, dict(color_overrides[k]) if k in color_overrides else v) for k, v in colors]
    for k, v in color_overrides.items():
        if k not in existing_c_keys:
            new_colors.append((k, dict(v)))
    mat["m_SavedProperties"]["m_Colors"] = new_colors


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
    print(f"  [Tex queued] {obj.path_id}: '{name}' {img.size[0]}x{img.size[1]} target_fmt={int(target_fmt)}")


def main():
    assert DONOR_BUNDLE.is_file(), f"Missing donor bundle: {DONOR_BUNDLE}"
    assert MESH_BUNDLE.is_file(), f"Missing mesh bundle: {MESH_BUNDLE}"

    print(f"[*] Loading blitzwing_mesh bundle: {MESH_BUNDLE}")
    env_m = UnityPy.load(str(MESH_BUNDLE))
    bw_meshes = {}
    for o in env_m.objects:
        if o.type.name == "Mesh":
            tt = o.read_typetree()
            bw_meshes[tt["m_Name"]] = tt
    print(f"  Found meshes in bundle: {list(bw_meshes.keys())}")
    robot_mesh_name = "cha_blitzwing_gs_00_atlased" if "cha_blitzwing_gs_00_atlased" in bw_meshes else "cha_blitzwing_gs_00"
    tank_mesh_name = "cha_blitzwing_gs_01_tank" if "cha_blitzwing_gs_01_tank" in bw_meshes else "cha_blitzwing_gs_01"
    jet_mesh_name = "cha_blitzwing_gs_02_jet" if "cha_blitzwing_gs_02_jet" in bw_meshes else "cha_blitzwing_gs_02"
    assert robot_mesh_name in bw_meshes, "Missing robot mesh"
    assert tank_mesh_name in bw_meshes, "Missing tank mesh"
    assert jet_mesh_name in bw_meshes, "Missing jet mesh"
    assert "cha_blitzwing_wpns_gun" in bw_meshes, "Missing gun mesh"
    assert "cha_blitzwing_wpns_sword" in bw_meshes, "Missing sword mesh"
    for m_key in (robot_mesh_name, tank_mesh_name, jet_mesh_name, "cha_blitzwing_wpns_gun", "cha_blitzwing_wpns_sword"):
        vd = bw_meshes[m_key].get("m_VertexData", {})
        vc = vd.get("m_VertexCount", 0)
        ds = len(vd.get("m_DataSize", b""))
        assert vc > 0 and ds > 0, f"Corrupt empty mesh '{m_key}' in {MESH_BUNDLE}: vc={vc}, datasize={ds}"

    print(f"[*] Extracting Motormaster/Optimus gunshot FSB5 audio from {CAP_BUNDLE}...")
    env_cap = UnityPy.load(str(CAP_BUNDLE))
    cap_res = next((f for n, f in env_cap.file.files.items() if n.endswith(".resource")), None)
    assert cap_res is not None, "Missing character_audio_procedural .resource!"
    fire_clip_names = [
        "optimus_prime_gs_projectile_fire_a",
        "optimus_prime_gs_projectile_fire_b",
        "optimus_prime_gs_projectile_fire_c",
        "optimus_prime_gs_projectile_fire_d",
    ]
    mm_fire_clips = {}
    for o in env_cap.objects:
        if o.type.name == "AudioClip":
            tt = o.read_typetree()
            nm = tt.get("m_Name", "")
            if nm in fire_clip_names:
                res = tt.get("m_Resource", {})
                cap_res.seek(res["m_Offset"])
                chunk = cap_res.read(res["m_Size"])
                assert len(chunk) == res["m_Size"] and chunk[:4] == b"FSB5"
                mm_fire_clips[nm] = (chunk, tt.get("m_Length", 2.6644897))
    assert len(mm_fire_clips) == 4, f"Missing fire clips: {set(fire_clip_names) - set(mm_fire_clips.keys())}"

    print(f"[*] Loading Megatron donor bundle: {DONOR_BUNDLE}")
    env = UnityPy.load(str(DONOR_BUNDLE))

    cab_files = [k for k in env.file.files.keys() if k.lower().startswith("cab-") and "." not in k]
    assert cab_files, f"Could not detect CAB inside donor bundle: {list(env.file.files.keys())}"
    old_cab = cab_files[0]
    old_cab_low = old_cab.lower()
    new_cab_low = NEW_CAB.lower()
    print(f"[*] Remapping CAB: {old_cab} -> {NEW_CAB}")

    cab_sf = env.file.files[old_cab]
    obj_map = {o.path_id: o for o in env.objects}

    def clone_object(src_pid: int, new_pid: int):
        if new_pid in cab_sf.objects:
            return cab_sf.objects[new_pid]
        src_obj = cab_sf.objects[src_pid]
        new_obj = copy.copy(src_obj)
        new_obj.path_id = new_pid
        cab_sf.objects[new_pid] = new_obj
        obj_map[new_pid] = new_obj
        return new_obj

    # Clone dedicated slots BEFORE overwriting MESH_JET_PID / TEX_VEH_RAOE_PID
    clone_object(MESH_JET_PID, MESH_SWORD_PID)
    clone_object(TEX_VEH_RAOE_PID, TEX_WPNS_RAOE_PID)

    # Append Motormaster gunshot audio to .resource & rewire AUDIO_GUN_FIRE_PIDS
    res_name, res_file = next(((n, f) for n, f in env.file.files.items() if n.endswith(".resource")), (None, None))
    assert res_file is not None, "Missing donor .resource!"
    curr_fire_offset = len(res_file.bytes)
    mm_fire_bytes = b"".join(mm_fire_clips[nm][0] for nm in fire_clip_names)
    new_res_reader = EndianBinaryReader(res_file.bytes + mm_fire_bytes)
    new_res_reader.flags = getattr(res_file, "flags", 0)
    env.file.files[res_name] = new_res_reader
    for pid, cname in zip(AUDIO_GUN_FIRE_PIDS, fire_clip_names):
        chunk, length = mm_fire_clips[cname]
        t_fire = obj_map[pid].read_typetree()
        t_fire["m_Length"] = length
        t_fire["m_Resource"] = {
            "m_Source": f"archive:/{NEW_CAB}/{NEW_CAB}.resource",
            "m_Offset": curr_fire_offset,
            "m_Size": len(chunk),
        }
        obj_map[pid].save_typetree(t_fire)
        curr_fire_offset += len(chunk)
    print(f"  [Audio] Injected 4 Motormaster gunshot FSB5 clips (+{len(mm_fire_bytes)} bytes) into .resource")

    # 1. Update AssetBundle container and name
    ab_objs = [o for o in env.objects if o.type.name == "AssetBundle"]
    assert len(ab_objs) == 1
    ab_tt = ab_objs[0].read_typetree()
    ab_tt["m_Name"] = "data/blitzwing_gs_odr/blitzwing_gs.assetbundle"
    ab_tt["m_AssetBundleName"] = "data/blitzwing_gs_odr/blitzwing_gs.assetbundle"
    new_container = []
    for k, v in ab_tt["m_Container"]:
        nk = k.replace("megatron_gs_leader2015", "blitzwing_gs")
        new_container.append([nk, v])
        print(f"  [Container] '{k}' -> '{nk}'")
    ab_tt["m_Container"] = new_container
    ab_objs[0].save_typetree(ab_tt)

    # 2. Remap stream paths containing old_cab
    replaced_pids = {
        MESH_ROBOT_PID, MESH_VEHICLE_PID, MESH_JET_PID, MESH_GUN_PID, MESH_SWORD_PID,
        TEX_ROBOT_DIFF_PID, TEX_ROBOT_NM_PID, TEX_ROBOT_RAOE_PID,
        TEX_VEH_DIFF_PID, TEX_VEH_NM_PID, TEX_VEH_RAOE_PID,
        TEX_WPNS_DIFF_PID, TEX_WPNS_NM_PID, TEX_WPNS_RAOE_PID,
        *AUDIO_GUN_FIRE_PIDS,
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

    # 3. Graft Robot Mesh (keeping donor 51 bone hashes)
    src_r_tt = bw_meshes[robot_mesh_name]
    dst_r_obj = obj_map[MESH_ROBOT_PID]
    dst_r_tt = dst_r_obj.read_typetree()
    keep_r_hashes = list(dst_r_tt["m_BoneNameHashes"])
    keep_r_root = int(dst_r_tt["m_RootBoneNameHash"])

    dst_r_tt["m_Name"] = "cha_blitzwing_gs_00"
    for field in (
        "m_SubMeshes", "m_Shapes", "m_BindPose", "m_BonesAABB",
        "m_VariableBoneCountWeights", "m_MeshCompression", "m_IndexFormat",
        "m_IndexBuffer", "m_VertexData", "m_CompressedMesh", "m_LocalAABB",
        "m_StreamData",
    ):
        dst_r_tt[field] = src_r_tt[field]
    dst_r_tt["m_BoneNameHashes"] = keep_r_hashes
    dst_r_tt["m_RootBoneNameHash"] = keep_r_root
    dst_r_tt["m_IsReadable"] = True
    dst_r_tt["m_KeepVertices"] = True
    dst_r_tt["m_KeepIndices"] = True
    dst_r_tt["m_MeshUsageFlags"] = 1
    dst_r_obj.save_typetree(dst_r_tt)
    print(f"  [Mesh Robot] {MESH_ROBOT_PID} -> 'cha_blitzwing_gs_00' verts={src_r_tt['m_VertexData']['m_VertexCount']} bones={len(keep_r_hashes)}")

    # 4. Graft Tank Mesh
    # Meshes inside blitzwing_mesh.assetbundle are ALREADY in correct Unity coordinates:
    # Ground at y=0.0, Cannon forward at +Z forward.
    # Vertex data is natively compiled by Unity 2020 with 100% weight on bone index 0.
    src_t_tt = bw_meshes[tank_mesh_name]
    dst_t_obj = obj_map[MESH_VEHICLE_PID]
    dst_t_tt = dst_t_obj.read_typetree()

    dst_t_tt["m_Name"] = "cha_blitzwing_gs_01"
    for field in (
        "m_SubMeshes", "m_Shapes", "m_BonesAABB",
        "m_VariableBoneCountWeights", "m_MeshCompression", "m_IndexFormat",
        "m_IndexBuffer", "m_VertexData", "m_CompressedMesh",
        "m_StreamData",
    ):
        dst_t_tt[field] = src_t_tt[field]
    dst_t_tt["m_BindPose"] = [cog_inverse_matrix()]
    dst_t_tt["m_BoneNameHashes"] = [239972378]       # Avatar TOS hash("Reference/COG")
    dst_t_tt["m_RootBoneNameHash"] = 239972378
    dst_t_tt["m_BonesAABB"] = [{
        "m_Min": {"x": -10.0, "y": -10.0, "z": -10.0},
        "m_Max": {"x": 10.0, "y": 10.0, "z": 10.0},
    }]
    dst_t_tt["m_LocalAABB"] = src_t_tt["m_LocalAABB"]
    for sm in dst_t_tt.get("m_SubMeshes", []):
        sm["localAABB"] = dict(dst_t_tt["m_LocalAABB"])
    dst_t_tt["m_IsReadable"] = True
    dst_t_tt["m_KeepVertices"] = True
    dst_t_tt["m_KeepIndices"] = True
    dst_t_tt["m_MeshUsageFlags"] = 1
    dst_t_obj.save_typetree(dst_t_tt)
    vcount_t = src_t_tt["m_VertexData"]["m_VertexCount"]
    print(f"  [Mesh Tank] {MESH_VEHICLE_PID} -> 'cha_blitzwing_gs_01' verts={vcount_t} bound to COG")

    # 5. Graft Jet Mesh
    # Meshes inside blitzwing_mesh.assetbundle are ALREADY in correct Unity coordinates:
    # Ground at y=0.30, Nosecone forward at +Z forward.
    # Vertex data is natively compiled by Unity 2020 with 100% weight on bone index 0.
    src_j_tt = bw_meshes[jet_mesh_name]
    dst_j_obj = obj_map[MESH_JET_PID]
    dst_j_tt = dst_j_obj.read_typetree()

    dst_j_tt["m_Name"] = "cha_blitzwing_gs_02"
    for field in (
        "m_SubMeshes", "m_Shapes", "m_BonesAABB",
        "m_VariableBoneCountWeights", "m_MeshCompression", "m_IndexFormat",
        "m_IndexBuffer", "m_VertexData", "m_CompressedMesh",
        "m_StreamData",
    ):
        dst_j_tt[field] = src_j_tt[field]
    dst_j_tt["m_BindPose"] = [cog_inverse_matrix()]
    dst_j_tt["m_BoneNameHashes"] = [239972378]       # Avatar TOS hash("Reference/COG")
    dst_j_tt["m_RootBoneNameHash"] = 239972378
    dst_j_tt["m_BonesAABB"] = [{
        "m_Min": {"x": -10.0, "y": -10.0, "z": -10.0},
        "m_Max": {"x": 10.0, "y": 10.0, "z": 10.0},
    }]
    dst_j_tt["m_LocalAABB"] = src_j_tt["m_LocalAABB"]
    for sm in dst_j_tt.get("m_SubMeshes", []):
        sm["localAABB"] = dict(dst_j_tt["m_LocalAABB"])
    dst_j_tt["m_IsReadable"] = True
    dst_j_tt["m_KeepVertices"] = True
    dst_j_tt["m_KeepIndices"] = True
    dst_j_tt["m_MeshUsageFlags"] = 1
    dst_j_obj.save_typetree(dst_j_tt)
    vcount_j = src_j_tt["m_VertexData"]["m_VertexCount"]
    print(f"  [Mesh Jet] {MESH_JET_PID} -> 'cha_blitzwing_gs_02' verts={vcount_j} bound to COG")

    # 5b. Graft Gun & Sword Meshes (1-bone COG Identity BindPose in Unity LeftHand / RightHand space)
    for dst_pid, src_name in ((MESH_GUN_PID, "cha_blitzwing_wpns_gun"), (MESH_SWORD_PID, "cha_blitzwing_wpns_sword")):
        src_w_tt = bw_meshes[src_name]
        dst_w_obj = obj_map[dst_pid]
        dst_w_tt = dst_w_obj.read_typetree()
        dst_w_tt["m_Name"] = src_name
        for field in (
            "m_SubMeshes", "m_Shapes", "m_BonesAABB",
            "m_VariableBoneCountWeights", "m_MeshCompression", "m_IndexFormat",
            "m_IndexBuffer", "m_VertexData", "m_CompressedMesh",
            "m_StreamData",
        ):
            dst_w_tt[field] = src_w_tt[field]
        dst_w_tt["m_BindPose"] = [identity_matrix()]
        dst_w_tt["m_BoneNameHashes"] = [239972378]
        dst_w_tt["m_RootBoneNameHash"] = 239972378
        dst_w_tt["m_BonesAABB"] = [{
            "m_Min": {"x": -10.0, "y": -10.0, "z": -10.0},
            "m_Max": {"x": 10.0, "y": 10.0, "z": 10.0},
        }]
        dst_w_tt["m_LocalAABB"] = src_w_tt["m_LocalAABB"]
        for sm in dst_w_tt.get("m_SubMeshes", []):
            sm["localAABB"] = dict(dst_w_tt["m_LocalAABB"])
        dst_w_tt["m_IsReadable"] = True
        dst_w_tt["m_KeepVertices"] = True
        dst_w_tt["m_KeepIndices"] = True
        dst_w_tt["m_MeshUsageFlags"] = 1
        dst_w_obj.save_typetree(dst_w_tt)
        print(f"  [Mesh Wpn] {dst_pid} -> '{src_name}' verts={src_w_tt['m_VertexData']['m_VertexCount']} bound to COG")

    # 6. Update SMRs
    generous_aabb = {
        "m_Center": {"x": 0.0, "y": 0.0, "z": 0.0},
        "m_Extent": {"x": 10.0, "y": 10.0, "z": 10.0},
    }
    # Robot SMRs
    for pid in SMR_ROBOT_PIDS:
        smr = obj_map[pid].read_typetree()
        smr["m_Materials"] = [{"m_FileID": 0, "m_PathID": MAT_ROBOT_PID}]
        smr["m_AABB"] = generous_aabb
        smr["m_UpdateWhenOffscreen"] = True
        obj_map[pid].save_typetree(smr)
        print(f"  [SMR Robot] {pid}: mat={MAT_ROBOT_PID}, bones={len(smr['m_Bones'])}")

    # Tank SMRs (Showcase PID=2138194849323017337, Combat PID=4626197738286450028)
    for pid, cog_pid in [
        (2138194849323017337, SHOWCASE_TANK_COG_PID),
        (4626197738286450028, COMBAT_TANK_COG_PID),
    ]:
        smr = obj_map[pid].read_typetree()
        smr["m_Materials"] = [{"m_FileID": 0, "m_PathID": MAT_VEHICLE_PID}]
        smr["m_Mesh"] = {"m_FileID": 0, "m_PathID": MESH_VEHICLE_PID}
        smr["m_RootBone"] = {"m_FileID": 0, "m_PathID": cog_pid}
        smr["m_Bones"] = [{"m_FileID": 0, "m_PathID": cog_pid}]
        smr["m_Enabled"] = False
        smr["m_AABB"] = generous_aabb
        smr["m_UpdateWhenOffscreen"] = True
        obj_map[pid].save_typetree(smr)
        print(f"  [SMR Tank] {pid}: mesh={MESH_VEHICLE_PID}, mat={MAT_VEHICLE_PID}, bone=COG({cog_pid})")

    # Jet SMRs (Showcase PID=-7481134504555158405, Combat PID=3992037002325232027)
    for pid, cog_pid in [
        (-7481134504555158405, SHOWCASE_JET_COG_PID),
        (3992037002325232027, COMBAT_JET_COG_PID),
    ]:
        smr = obj_map[pid].read_typetree()
        smr["m_Materials"] = [{"m_FileID": 0, "m_PathID": MAT_VEHICLE_PID}]
        smr["m_Mesh"] = {"m_FileID": 0, "m_PathID": MESH_JET_PID}
        smr["m_RootBone"] = {"m_FileID": 0, "m_PathID": cog_pid}
        smr["m_Bones"] = [{"m_FileID": 0, "m_PathID": cog_pid}]
        smr["m_Enabled"] = False
        smr["m_AABB"] = generous_aabb
        smr["m_UpdateWhenOffscreen"] = True
        obj_map[pid].save_typetree(smr)
        print(f"  [SMR Jet] {pid}: mesh={MESH_JET_PID}, mat={MAT_VEHICLE_PID}, bone=COG({cog_pid})")

    # 6a. Configure Dynamic Gun (LeftHand, was mace) & Dynamic Sword (RightHand, reparented from RightForeArm)
    GUN_POS_LH = {"x": -0.70, "y": -0.38, "z": -0.02}
    SWORD_POS_RH = {"x": -0.72, "y": 0.34, "z": 0.04}
    ident_pos = {"x": 0.0, "y": 0.0, "z": 0.0}
    ident_rot = {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
    ident_scale = {"x": 1.0, "y": 1.0, "z": 1.0}

    # Gun hierarchy (Showcase & Combat)
    for gun_go_pid, gun_tr_pid, gun_anim_pid, mesh_tr_pid, smr_pid, ref_tr_pid, cog_tr_pid in (
        (-7375623541015776277, 7260296377652267311, 8370979346696130251, 1812252406826165608, 7267330081541926865, 7862862741360663378, -3079300592525438635),
        (1109389691721735991, -5948861407170161750, -5080088347447896440, -8017017403795261197, -6758328762533593613, -2088557302007782971, -6244159580185277204),
    ):
        go = obj_map[gun_go_pid].read_typetree()
        go["m_Name"] = "gun"
        go["m_IsActive"] = True
        obj_map[gun_go_pid].save_typetree(go)

        anim = obj_map[gun_anim_pid].read_typetree()
        anim["m_Enabled"] = 0
        obj_map[gun_anim_pid].save_typetree(anim)

        tr = obj_map[gun_tr_pid].read_typetree()
        tr["m_LocalPosition"] = GUN_POS_LH
        tr["m_LocalRotation"] = ident_rot
        tr["m_LocalScale"] = ident_scale
        obj_map[gun_tr_pid].save_typetree(tr)

        for tid in (mesh_tr_pid, ref_tr_pid, cog_tr_pid):
            ct = obj_map[tid].read_typetree()
            ct["m_LocalPosition"] = ident_pos
            ct["m_LocalRotation"] = ident_rot
            ct["m_LocalScale"] = ident_scale
            obj_map[tid].save_typetree(ct)

        smr = obj_map[smr_pid].read_typetree()
        smr["m_Mesh"] = {"m_FileID": 0, "m_PathID": MESH_GUN_PID}
        smr["m_Materials"] = [{"m_FileID": 0, "m_PathID": MAT_WPNS_PID}]
        smr["m_RootBone"] = {"m_FileID": 0, "m_PathID": cog_tr_pid}
        smr["m_Bones"] = [{"m_FileID": 0, "m_PathID": cog_tr_pid}]
        smr["m_AABB"] = generous_aabb
        smr["m_UpdateWhenOffscreen"] = True
        smr["m_Enabled"] = False  # Toggled dynamically by PropsController
        obj_map[smr_pid].save_typetree(smr)

    # Sword hierarchy (reparent staticCannon RightForeArm -> RightHand in Showcase & Combat)
    for sw_go_pid, sw_tr_pid, rh_tr_pid, mesh_tr_pid, smr_pid, ref_tr_pid, cog_tr_pid in (
        (-6258551087734041547, 9120676652720332331, -8402135396370300167, 1565022929006569611, 4561093141354196631, 2580885263844408577, 1062937249083135075),
        (74419346676817846, -3428856548110063410, -4088132481749495149, -7648057942539388940, 8495398593779105175, -223780715342978427, -544788270524065047),
    ):
        go = obj_map[sw_go_pid].read_typetree()
        go["m_Name"] = "sword"
        go["m_IsActive"] = True
        obj_map[sw_go_pid].save_typetree(go)

        tr = obj_map[sw_tr_pid].read_typetree()
        old_father = tr["m_Father"]["m_PathID"]
        if old_father != rh_tr_pid and old_father in obj_map:
            old_f_tr = obj_map[old_father].read_typetree()
            old_f_tr["m_Children"] = [c for c in old_f_tr.get("m_Children", []) if c["m_PathID"] != sw_tr_pid]
            obj_map[old_father].save_typetree(old_f_tr)
        rh_tr = obj_map[rh_tr_pid].read_typetree()
        if not any(c["m_PathID"] == sw_tr_pid for c in rh_tr.get("m_Children", [])):
            rh_tr["m_Children"].append({"m_FileID": 0, "m_PathID": sw_tr_pid})
            obj_map[rh_tr_pid].save_typetree(rh_tr)

        tr["m_Father"] = {"m_FileID": 0, "m_PathID": rh_tr_pid}
        tr["m_LocalPosition"] = SWORD_POS_RH
        tr["m_LocalRotation"] = ident_rot
        tr["m_LocalScale"] = ident_scale
        obj_map[sw_tr_pid].save_typetree(tr)

        for tid in (mesh_tr_pid, ref_tr_pid, cog_tr_pid):
            ct = obj_map[tid].read_typetree()
            ct["m_LocalPosition"] = ident_pos
            ct["m_LocalRotation"] = ident_rot
            ct["m_LocalScale"] = ident_scale
            obj_map[tid].save_typetree(ct)

        smr = obj_map[smr_pid].read_typetree()
        smr["m_Mesh"] = {"m_FileID": 0, "m_PathID": MESH_SWORD_PID}
        smr["m_Materials"] = [{"m_FileID": 0, "m_PathID": MAT_WPNS_PID}]
        smr["m_RootBone"] = {"m_FileID": 0, "m_PathID": cog_tr_pid}
        smr["m_Bones"] = [{"m_FileID": 0, "m_PathID": cog_tr_pid}]
        smr["m_AABB"] = generous_aabb
        smr["m_UpdateWhenOffscreen"] = True
        smr["m_Enabled"] = False  # Toggled dynamically during Tank S2 & Jet S1
        obj_map[smr_pid].save_typetree(smr)
    print("  [Weapons Rig] Configured dynamic 'gun' (LeftHand) & 'sword' (RightHand) in Showcase + Combat")

    # 6b. Neutralize Jet Reference Transform rotation and position offset
    # PIDs -8160233092164819743 (Showcase) and -8081113419723769434 (Combat)
    for ref_pid in (-8160233092164819743, -8081113419723769434):
        if ref_pid in obj_map:
            ref_tr = obj_map[ref_pid].read_typetree()
            ref_tr["m_LocalPosition"] = {"x": 0.0, "y": 0.0, "z": 0.0}
            ref_tr["m_LocalRotation"] = {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
            ref_tr["m_LocalScale"] = {"x": 1.0, "y": 1.0, "z": 1.0}
            obj_map[ref_pid].save_typetree(ref_tr)
            print(f"  [Transform Jet Reference] Neutralized {ref_pid} -> Pos=(0,0,0) Rot=identity")

    # 6c. Align all 4 Tank & Jet COG transforms to animated rest pose q=(0.5, 0.5, -0.5, -0.5)
    # and zero out SMR GameObject local positions so SMR bounds are centered at (0,0,0)
    for cog_pid in (SHOWCASE_TANK_COG_PID, COMBAT_TANK_COG_PID, SHOWCASE_JET_COG_PID, COMBAT_JET_COG_PID):
        if cog_pid in obj_map:
            cog_tr = obj_map[cog_pid].read_typetree()
            cog_tr["m_LocalPosition"] = {"x": 0.0, "y": 0.0, "z": 0.0}
            cog_tr["m_LocalRotation"] = {"x": 0.5, "y": 0.5, "z": -0.5, "w": -0.5}
            cog_tr["m_LocalScale"] = {"x": 1.0, "y": 1.0, "z": 1.0}
            obj_map[cog_pid].save_typetree(cog_tr)
            print(f"  [Transform COG] Aligned {cog_pid} -> Pos=(0,0,0) Rot=(0.5, 0.5, -0.5, -0.5)")

    for smr_tr_pid in (
        -4070916873066828308, -3207237225000537856,
        -8637124854016160271, 7273197848394815578,
        -5727109540658706581, 8905508169500533586,
    ):
        if smr_tr_pid in obj_map:
            smr_tr = obj_map[smr_tr_pid].read_typetree()
            smr_tr["m_LocalPosition"] = {"x": 0.0, "y": 0.0, "z": 0.0}
            smr_tr["m_LocalRotation"] = {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
            smr_tr["m_LocalScale"] = {"x": 1.0, "y": 1.0, "z": 1.0}
            obj_map[smr_tr_pid].save_typetree(smr_tr)

    # Reparent Jet prop 'cannon' (transformed_2) from Reference -> Hips and match Ramjet's
    # (-0.5, -0.5, 0.5, 0.5) local rotation. PropData.RootPath / RotationOffset are Editor-only
    # and ignored at runtime (PropData.cs only applies PositionOffset).
    for label, ref_pid, hips_pid, cannon_pid in [
        ("Combat", -6028308954984925732, -2150442408177557830, -1893245760279338324),
        ("Showcase", -6848276043409792716, -820080875074696244, -464464231220373427),
    ]:
        if ref_pid in obj_map and hips_pid in obj_map and cannon_pid in obj_map:
            ref_tr = obj_map[ref_pid].read_typetree()
            hips_tr = obj_map[hips_pid].read_typetree()
            cannon_tr = obj_map[cannon_pid].read_typetree()

            ref_tr["m_Children"] = [c for c in ref_tr["m_Children"] if c.get("m_PathID") != cannon_pid]
            if not any(c.get("m_PathID") == cannon_pid for c in hips_tr["m_Children"]):
                hips_tr["m_Children"].append({"m_FileID": 0, "m_PathID": cannon_pid})

            cannon_tr["m_Father"] = {"m_FileID": 0, "m_PathID": hips_pid}
            cannon_tr["m_LocalPosition"] = {"x": 0.0, "y": 0.0, "z": 0.0}
            cannon_tr["m_LocalRotation"] = {"x": -0.5, "y": -0.5, "z": 0.5, "w": 0.5}
            cannon_tr["m_LocalScale"] = {"x": 1.0, "y": 1.0, "z": 1.0}

            obj_map[ref_pid].save_typetree(ref_tr)
            obj_map[hips_pid].save_typetree(hips_tr)
            obj_map[cannon_pid].save_typetree(cannon_tr)
            print(f"  [Jet Parent {label}] Reparented cannon({cannon_pid}) Reference({ref_pid}) -> Hips({hips_pid}) rot=(-0.5,-0.5,0.5,0.5)")

    # 6d. Configure Jet Prop Animator Override Controller with Ramjet Jet clips
    # BaseController MUST be animator_prop_gameplay (PID 341294063036995988), NOT animator_weapons_gameplay!
    JET_AOC_PID = -4914847298671604126
    if JET_AOC_PID in obj_map:
        jet_aoc = obj_map[JET_AOC_PID].read_typetree()
        jet_aoc["m_Name"] = "override_Blitzwing_GS_jet"
        jet_aoc["m_Controller"] = {"m_FileID": 0, "m_PathID": 341294063036995988}  # animator_prop_gameplay
        jet_aoc["m_Clips"] = [
            {"m_OriginalClip": {"m_FileID": 0, "m_PathID": 0}, "m_OverrideClip": {"m_FileID": 0, "m_PathID": 0}},
            {"m_OriginalClip": {"m_FileID": 0, "m_PathID": 0}, "m_OverrideClip": {"m_FileID": 0, "m_PathID": 0}},
            {"m_OriginalClip": {"m_FileID": 0, "m_PathID": 0}, "m_OverrideClip": {"m_FileID": 0, "m_PathID": 0}},
            {"m_OriginalClip": {"m_FileID": 0, "m_PathID": 0}, "m_OverrideClip": {"m_FileID": 0, "m_PathID": 0}},
            {"m_OriginalClip": {"m_FileID": 5, "m_PathID": 5620803938405291589}, "m_OverrideClip": {"m_FileID": 5, "m_PathID": 8156662034948264509}},
            {"m_OriginalClip": {"m_FileID": 5, "m_PathID": 3658090888164254241}, "m_OverrideClip": {"m_FileID": 5, "m_PathID": 3658090888164254241}},
            {"m_OriginalClip": {"m_FileID": 5, "m_PathID": 1661097116018184003}, "m_OverrideClip": {"m_FileID": 5, "m_PathID": 1661097116018184003}},
            {"m_OriginalClip": {"m_FileID": 5, "m_PathID": -131870695485524161}, "m_OverrideClip": {"m_FileID": 5, "m_PathID": -131870695485524161}},
            {"m_OriginalClip": {"m_FileID": 0, "m_PathID": 0}, "m_OverrideClip": {"m_FileID": 0, "m_PathID": 0}},
            {"m_OriginalClip": {"m_FileID": 0, "m_PathID": 0}, "m_OverrideClip": {"m_FileID": 0, "m_PathID": 0}},
            {"m_OriginalClip": {"m_FileID": 5, "m_PathID": 5051485932175143884}, "m_OverrideClip": {"m_FileID": 5, "m_PathID": -8977399132283187477}},
            {"m_OriginalClip": {"m_FileID": 5, "m_PathID": -8575900432944827290}, "m_OverrideClip": {"m_FileID": 5, "m_PathID": 6003597289559234958}},
            {"m_OriginalClip": {"m_FileID": 5, "m_PathID": -7632205551962568777}, "m_OverrideClip": {"m_FileID": 5, "m_PathID": 2235498278053343569}},
            {"m_OriginalClip": {"m_FileID": 5, "m_PathID": 6372851878398872443}, "m_OverrideClip": {"m_FileID": 5, "m_PathID": 7862591952412139551}},
            {"m_OriginalClip": {"m_FileID": 5, "m_PathID": -2012374896484064676}, "m_OverrideClip": {"m_FileID": 5, "m_PathID": -3119635653397265966}},
            {"m_OriginalClip": {"m_FileID": 5, "m_PathID": 6073306910817336135}, "m_OverrideClip": {"m_FileID": 5, "m_PathID": 7218399588967537672}},
            {"m_OriginalClip": {"m_FileID": 5, "m_PathID": -8823098701810809179}, "m_OverrideClip": {"m_FileID": 5, "m_PathID": -4633680087473212482}},
            {"m_OriginalClip": {"m_FileID": 5, "m_PathID": 8516921728443142186}, "m_OverrideClip": {"m_FileID": 5, "m_PathID": -2236987077198429143}},
        ]
        obj_map[JET_AOC_PID].save_typetree(jet_aoc)
        print(f"  [Jet AOC] Configured {JET_AOC_PID} with BaseController=animator_prop_gameplay & 18 Ramjet clips (HeavyAttack -> 2235498278053343569)")

    # 6e. Graft 8 Local Donor AnimationClips (Cheetor L2, Rhinox L3/M2, Wheeljack M1, Kickback M2, Mixmaster S1, Bludgeon S2, Windblade S1)
    # onto unused Megatron local clip PathIDs, and bind procedural clips in Fight AOC (-7755666207738536548)
    CLIP_GRAFTS = [
        ("cheetor_bw_transmetal_odr/cheetor_bw_transmetal.assetbundle", -486271743690878734, 3447898299160786076, "blitzwing_attackLight_02"),
        ("rhinox_gs_voyager2014_odr/rhinox_gs_voyager2014.assetbundle", 93276785253583668, 80445849579449578, "blitzwing_attackLight_03"),
        ("rhinox_gs_voyager2014_odr/rhinox_gs_voyager2014.assetbundle", -6442010242213229130, 7166247695725661904, "blitzwing_attackLight_04"),
        ("wheeljack_gs_mp20_odr/wheeljack_gs_mp20.assetbundle", 7265497203347661852, 5574244196002706121, "blitzwing_attackMedium_01"),
        ("kickback_gs_kabam_odr/kickback_gs_kabam.assetbundle", 221766495520085048, 3299789870907881362, "blitzwing_attackMedium_02"),
        ("mixmaster_cin_rotf_odr/mixmaster_cin_rotf.assetbundle", -7921770726548403079, -7039854538955176447, "blitzwing_tank_special_01"),
        ("bludgeon_gs_rd20_odr/bludgeon_gs_rd20.assetbundle", -5815229600094096883, 93796867180898313, "blitzwing_tank_special_02"),
        ("windblade_gs_odr/windblade_gs.assetbundle", 4130864494046913653, -4759913177061412663, "blitzwing_jet_special_01"),
    ]
    donor_envs = {}
    for rel, src_clip_pid, dst_clip_pid, clip_alias in CLIP_GRAFTS:
        bp = ROOT_GM / "extracted_apk" / "assets" / "assetpack" / rel
        if rel not in donor_envs:
            d_env = UnityPy.load(str(bp))
            donor_envs[rel] = {o.path_id: o for o in d_env.objects}
        src_clip_tt = copy.deepcopy(donor_envs[rel][src_clip_pid].read_typetree())
        src_clip_tt["m_Name"] = clip_alias
        obj_map[dst_clip_pid].save_typetree(src_clip_tt)
        print(f"  [Clip Graft] {clip_alias:<26} -> PID {dst_clip_pid} (len={src_clip_tt['m_MuscleClip']['m_StopTime']:.3f}s)")

    CHAR_FIGHT_AOC_PID = -7755666207738536548
    aoc_overrides = {
        3149807030316843707: {"m_FileID": 5, "m_PathID": -5567779559826134777},   # L1 Prowl
        2881204487098155940: {"m_FileID": 5, "m_PathID": -3948795660449728024},   # Ranged01 Motormaster
        -5971837772429318172: {"m_FileID": 5, "m_PathID": 6078334979657561662},   # Ranged02 Motormaster
        5250436936531843304: {"m_FileID": 5, "m_PathID": 8599663582438923052},    # Ranged03 Motormaster
        4070315435280742960: {"m_FileID": 5, "m_PathID": -8287216037977883126},   # Misc01 Ramjet Jet Heavy
        2052977056553896436: {"m_FileID": 0, "m_PathID": -4759913177061412663},   # Misc02 Windblade Jet S1 (local)
        6055683287690994375: {"m_FileID": 5, "m_PathID": -8047270946990567681},   # Misc03 Sideswipe Jet S2
    }
    if CHAR_FIGHT_AOC_PID in obj_map:
        char_aoc = obj_map[CHAR_FIGHT_AOC_PID].read_typetree()
        for clip_pair in char_aoc.get("m_Clips", []):
            orig_pid = clip_pair.get("m_OriginalClip", {}).get("m_PathID")
            if orig_pid in aoc_overrides:
                clip_pair["m_OverrideClip"] = dict(aoc_overrides[orig_pid])
        obj_map[CHAR_FIGHT_AOC_PID].save_typetree(char_aoc)
        print(f"  [Char Fight AOC] Bound L1/Ranged01..03/Misc01..03 overrides on {CHAR_FIGHT_AOC_PID}")

    # Sync Base.Misc01 <- HeavyAttack, Base.Misc02 <- SpecialAttack01, Base.Misc03 <- SpecialAttack02
    CHAR_FIGHT_AC_PID = -6923321525341018075
    if CHAR_FIGHT_AC_PID in obj_map:
        ac = obj_map[CHAR_FIGHT_AC_PID].read_typetree()
        SYNC_PAIRS = [
            (2579208148, 732291567, "HeavyAttack->Misc01"),
            (1809527195, 2997661781, "SpecialAttack01->Misc02"),
            (4073873441, 3316351171, "SpecialAttack02->Misc03"),
        ]
        for sm in ac.get("m_Controller", {}).get("m_StateMachineArray", []):
            sm_data = sm.get("data", sm)
            states = sm_data.get("m_StateConstantArray", [])
            by_id = {st.get("data", st).get("m_NameID"): st.get("data", st) for st in states}
            for src_id, dst_id, lbl in SYNC_PAIRS:
                if src_id in by_id and dst_id in by_id:
                    s_st, d_st = by_id[src_id], by_id[dst_id]
                    d_st["m_TransitionConstantArray"] = copy.deepcopy(s_st.get("m_TransitionConstantArray", []))
                    d_st["m_IKOnFeet"] = s_st.get("m_IKOnFeet", False)
                    d_st["m_TagID"] = s_st.get("m_TagID", 1080829965)
                    print(f"  [Char Fight AC] Synced {lbl} (ik={d_st['m_IKOnFeet']}, tag={d_st['m_TagID']}, trans={len(d_st['m_TransitionConstantArray'])})")
        obj_map[CHAR_FIGHT_AC_PID].save_typetree(ac)

    # 6f. Update Combat MoveSet (L1..L4, M1..M2, Ranged01..03, S1/S2 Tank, Misc01/02/03 Jet)
    MOVESET_COMBAT_PID = 5996528693102170603
    MOVESET_UPDATES = {
        "Base.LightAttack01": ("move_tactical_attack_light_01", 3602276196112243781),
        "Base.LightAttack02": ("move_cheetor_attack_light_02", 2021038327158097554),
        "Base.LightAttack03": ("move_military_attack_light_03", 2319864737932337275),
        "Base.LightAttack04": ("move_military_attack_medium_02", 2010545634273341510),
        "Base.MediumAttack01": ("move_wheeljack_attack_medium_01", 4749294833821550488),
        "Base.MediumAttack02": ("move_kickback_attack_medium_02", 5005615225158410510),
        "Base.RangedAttack01": ("move_attackRanged_handGun_left_XL_01", 6811001981586741581),
        "Base.RangedAttack02": ("move_attackRanged_handGun_left_XL_02", 4776763212269214863),
        "Base.RangedAttack03": ("move_attackRanged_handGun_left_XL_03B", -4795991277224341066),
        "Base.SpecialAttack01": ("move_blitzwing_tank_s1", -8888888888888888901),
        "Base.SpecialAttack02": ("move_blitzwing_tank_s2", -8888888888888888902),
        "Base.Misc01": ("move_heavy_ramjet_donut", -8528702938335562906),
        "Base.Misc02": ("move_blitzwing_jet_s1", -8888888888888888903),
        "Base.Misc03": ("move_blitzwing_jet_s2", -8888888888888888904),
    }
    if MOVESET_COMBAT_PID in obj_map:
        ms_obj = obj_map[MOVESET_COMBAT_PID]
        ms_tt = ms_obj.read_typetree()
        seen_states = set()
        for m in ms_tt["_moves"]:
            sname = m.get("_animStateName", "")
            if sname in MOVESET_UPDATES:
                mv_nm, mv_pid = MOVESET_UPDATES[sname]
                m["_name"] = mv_nm
                m["_asset"] = {"m_FileID": 7, "m_PathID": mv_pid}
                seen_states.add(sname)
        for sname, (mv_nm, mv_pid) in MOVESET_UPDATES.items():
            if sname not in seen_states:
                ms_tt["_moves"].append({
                    "_name": mv_nm,
                    "_animStateName": sname,
                    "_asset": {"m_FileID": 7, "m_PathID": mv_pid},
                })
        ms_obj.save_typetree(ms_tt)
        print(f"  [MoveSet] Wired {len(MOVESET_UPDATES)} moves (L1-L4, M1-M2, Ranged01-03, S1/S2, Misc01-03) on {MOVESET_COMBAT_PID}")

    # 6g. Convert Ranged/S2 Projectile Prefabs & Clone Dedicated 4th Projectile Prefab (keeping Tank Heavy projectile_megatron_gs_bullet intact!)
    # - projectile_megatron_gs_bullet (9003878510878022874) -> KEPT INTACT for Tank Heavy (move_heavy_megatron_gs_shoot)!
    # - projectile_megatron_gs_ranged (4196009027374098921) -> projectile_optimus_bullet (Ranged Gun)
    # - projectile_megatron_gs_sp2_shot (2836027833803039595) -> projectile_sideswipe_missile (Jet S2)
    # - CLONED -8888888888888888920..-925 from 9003878510878022874 -> projectile_special_bullet (Tank S1)
    PROJ_SP_GO_PID = -8888888888888888920
    PROJ_SP_TR_PID = -8888888888888888921
    PROJ_SP_PR_PID = -8888888888888888922
    PROJ_SP_MS_PID = -8888888888888888923
    PROJ_SP_PL_PID = -8888888888888888924
    PROJ_SP_SQ_PID = -8888888888888888925
    clone_pairs = [
        (9003878510878022874, PROJ_SP_GO_PID),
        (-3703404665488950760, PROJ_SP_TR_PID),
        (7614484081745325141, PROJ_SP_PR_PID),
        (-2714705455090383668, PROJ_SP_MS_PID),
        (-4642064524079818382, PROJ_SP_PL_PID),
        (5864972968936471992, PROJ_SP_SQ_PID),
    ]
    for src_pid, dst_pid in clone_pairs:
        clone_object(src_pid, dst_pid)
    sp_comp_override = [
        {"component": {"m_FileID": 0, "m_PathID": cpid}}
        for cpid in (PROJ_SP_TR_PID, PROJ_SP_PR_PID, PROJ_SP_MS_PID, PROJ_SP_PL_PID, PROJ_SP_SQ_PID)
    ]
    # Save Transform & MoveSequencer once with cloned m_GameObject; Projectile/MoveSet/PrefabLib are saved once in PROJ_SPECS below!
    for src_pid, dst_pid in ((clone_pairs[1]), (clone_pairs[5])):
        ct = copy.deepcopy(obj_map[src_pid].read_typetree())
        ct["m_GameObject"] = {"m_FileID": 0, "m_PathID": PROJ_SP_GO_PID}
        obj_map[dst_pid].save_typetree(ct)

    PROJ_SPECS = [
        (
            4196009027374098921, "projectile_optimus_bullet",
            3454257687435078087, {"x": 0.0, "y": 0.0, "z": 3.0},
            7895226901659888460, [
                ("fire", 6337232768847846927),
                ("explode", 98785653677070406),
                ("explode_special", 182607865359928388),
            ],
            7216954881528309562, [
                (9, -6715103446334267986, 1),   # fx_p_red_projectile
                (9, -8062247508178286595, 1),   # fx_p_red_projectile_impact
                (3, 8149109851183567790, 1),    # fx_l_hit_small_perceptual
            ],
        ),
        (
            PROJ_SP_GO_PID, "projectile_special_bullet",
            PROJ_SP_PR_PID, {"x": 0.0, "y": 0.0, "z": 3.0},
            PROJ_SP_MS_PID, [
                ("fire", 7275783511033908245),
                ("explode", -7662765974118130433),
                ("explode_special", -4298719180494269477),
            ],
            PROJ_SP_PL_PID, [
                (9, 8511802164836736004, 1),    # fx_p_special_projectile
                (9, -5217152577278538804, 1),   # fx_p_special_projectile_impact
                (3, 8149109851183567790, 1),    # fx_l_hit_small_perceptual
            ],
        ),
        (
            2836027833803039595, "projectile_sideswipe_missile",
            3123025766236356518, {"x": 0.0, "y": 0.0, "z": 1.75},
            7434203789647441331, [
                ("fire", 5165820106613088172),
                ("explode", -8854555575616973088),
                ("explode_special", -8854555575616973088),
            ],
            -5508172462261296737, [
                (3, -6669518461038752398, 1),   # fx_p_rocket_fire
                (3, -7647804967815127805, 1),   # fx_p_projectile_blur
                (3, 5903881485512555851, 1),    # fx_p_scorponok_missile_small_fire
                (3, -7712769467675272952, 1),   # fx_l_hit_small_perceptual_orange
                (3, 8149109851183567790, 1),    # fx_l_hit_small_perceptual
                (9, 4126027868378667098, 1),    # fx_p_missile_projectile_impact
            ],
        ),
    ]
    all_ext_refs = set()
    for _, (_, mv_pid) in MOVESET_UPDATES.items():
        all_ext_refs.add((7, mv_pid))
    for _, ext_p in aoc_overrides.items():
        if ext_p["m_FileID"] != 0:
            all_ext_refs.add((ext_p["m_FileID"], ext_p["m_PathID"]))

    for go_pid, new_name, proj_pid, col_off, ms_pid, mv_list, plist_pid, fx_entries in PROJ_SPECS:
        go_tt = copy.deepcopy(obj_map[go_pid].read_typetree())
        go_tt["m_Name"] = new_name
        if go_pid == PROJ_SP_GO_PID:
            go_tt["m_Component"] = sp_comp_override
        obj_map[go_pid].save_typetree(go_tt)

        pr_tt = copy.deepcopy(obj_map[proj_pid].read_typetree())
        if go_pid == PROJ_SP_GO_PID:
            pr_tt["m_GameObject"] = {"m_FileID": 0, "m_PathID": PROJ_SP_GO_PID}
        pr_tt["CollisionPointOffset"] = col_off
        obj_map[proj_pid].save_typetree(pr_tt)

        pms_tt = copy.deepcopy(obj_map[ms_pid].read_typetree())
        if go_pid == PROJ_SP_GO_PID:
            pms_tt["m_GameObject"] = {"m_FileID": 0, "m_PathID": PROJ_SP_GO_PID}
        pms_tt["_moves"] = [
            {"_name": k, "_animStateName": "", "_asset": {"m_FileID": 7, "m_PathID": pid}}
            for k, pid in mv_list
        ]
        obj_map[ms_pid].save_typetree(pms_tt)
        for _, pid in mv_list:
            all_ext_refs.add((7, pid))

        pl_tt = copy.deepcopy(obj_map[plist_pid].read_typetree())
        if go_pid == PROJ_SP_GO_PID:
            pl_tt["m_GameObject"] = {"m_FileID": 0, "m_PathID": PROJ_SP_GO_PID}
        pl_tt["PrefabList"] = [
            {"Prefab": {"m_FileID": fid, "m_PathID": pid}, "Amount": amt}
            for fid, pid, amt in fx_entries
        ]
        obj_map[plist_pid].save_typetree(pl_tt)
        for fid, pid, _ in fx_entries:
            all_ext_refs.add((fid, pid))
        print(f"  [Projectile] {go_pid} -> '{new_name}' ({len(fx_entries)} FX prefabs)")

    # Register all projectiles + FX prefabs on Bot Root PrefabList (6775277914025461342)
    ROOT_PLIST_PID = 6775277914025461342
    root_pl = obj_map[ROOT_PLIST_PID].read_typetree()
    existing_pl = {(e["Prefab"]["m_FileID"], e["Prefab"]["m_PathID"]): e for e in root_pl.get("PrefabList", [])}
    BOT_REQUIRED_PREFABS = [
        (0, 4196009027374098921, 3),    # projectile_optimus_bullet (Ranged Gun)
        (0, 9003878510878022874, 2),    # projectile_megatron_gs_bullet (Tank Heavy!)
        (0, PROJ_SP_GO_PID, 2),         # projectile_special_bullet (Tank S1 Mixmaster)
        (0, 2836027833803039595, 2),    # projectile_sideswipe_missile (Jet S2 Sideswipe)
        (9, -6715103446334267986, 2),   # fx_p_red_projectile
        (9, -8062247508178286595, 2),   # fx_p_red_projectile_impact
        (9, 3861076792284877566, 2),    # fx_p_optimus_muzzle_flash (assets_redeco/character_fx.assetbundle)
        (9, 8511802164836736004, 2),    # fx_p_special_projectile
        (9, -5217152577278538804, 2),   # fx_p_special_projectile_impact
        (9, 4126027868378667098, 2),    # fx_p_missile_projectile_impact
        (9, 4559125710772694424, 2),    # fx_p_hit_large_no_local
        (9, -1685458833540413680, 2),   # fx_p_hit_punch_sparks_special
        (9, 559077676669210412, 2),     # fx_p_hit_small
        (9, 7466776119533748616, 2),    # fx_p_hit_medium
        (3, 8149109851183567790, 2),    # fx_l_hit_small_perceptual
        (3, -7712769467675272952, 2),   # fx_l_hit_small_perceptual_orange
        (3, -1485215930116935678, 2),   # fx_p_tank_muzzle_small
        (3, 3368064902973313242, 2),    # fx_p_grimlock_scrape_sparks
        (3, -3356717583303236785, 2),   # fx_p_acid_spray
        (3, -6686556082729464964, 2),   # fx_p_scrape_sparks
        (3, -6669518461038752398, 2),   # fx_p_rocket_fire
        (3, 5903881485512555851, 2),    # fx_p_scorponok_missile_small_fire
        (3, -7647804967815127805, 2),   # fx_p_projectile_blur
        (3, 3464383390465328844, 2),    # fx_p_land_dust
        (3, -811174631493111739, 6),    # fx_p_foot_drag_sparks
    ]
    for fid, pid, amt in BOT_REQUIRED_PREFABS:
        if (fid, pid) not in existing_pl:
            root_pl["PrefabList"].append({"Prefab": {"m_FileID": fid, "m_PathID": pid}, "Amount": amt})
        else:
            existing_pl[(fid, pid)]["Amount"] = max(existing_pl[(fid, pid)].get("Amount", 1), amt)
        if fid != 0:
            all_ext_refs.add((fid, pid))
    obj_map[ROOT_PLIST_PID].save_typetree(root_pl)
    print(f"  [Root PrefabList] {ROOT_PLIST_PID} now has {len(root_pl['PrefabList'])} pre-warmed prefabs")

    # Sync AssetBundle m_PreloadTable & Container preloadSize with all external references added
    preload = ab_tt.get("m_PreloadTable", [])
    old_preload_len = len(preload)
    existing_preload = {(p["m_FileID"], p["m_PathID"]) for p in preload}
    added_preloads = 0
    for fid, pid in sorted(all_ext_refs):
        if fid != 0 and (fid, pid) not in existing_preload:
            preload.append({"m_FileID": fid, "m_PathID": pid})
            existing_preload.add((fid, pid))
            added_preloads += 1
    ab_tt["m_PreloadTable"] = preload
    if added_preloads > 0:
        for k, v in ab_tt["m_Container"]:
            if v.get("preloadIndex", 0) + v.get("preloadSize", 0) == old_preload_len:
                v["preloadSize"] += added_preloads
                print(f"  [Container] Updated '{k}' preloadSize -> {v['preloadSize']}")
    ab_objs[0].save_typetree(ab_tt)
    print(f"  [PreloadTable] Added {added_preloads} external refs (total={len(preload)})")

    # 7. Configure PropsController in Showcase and Combat LW
    # - Repurpose 'mace' -> 'gun' under LeftHand (InitFlags=0, hidden at idle, drawn on Ranged)
    # - Repurpose 'staticCannon' -> 'sword' under RightHand (InitFlags=0, hidden at idle, drawn on Tank S2 & Jet S1)
    # - Attach BOTH 'transformed' (Tank) and 'transformed_2' (Jet) to Hips
    for pc_pid, jet_smr_pid, gun_smr_pid, sword_smr_pid in [
        (PROPS_SHOWCASE_PID, -7481134504555158405, 7267330081541926865, 4561093141354196631),
        (PROPS_COMBAT_PID, 3992037002325232027, -6758328762533593613, 8495398593779105175),
    ]:
        if pc_pid in obj_map:
            pc = obj_map[pc_pid].read_typetree()
            keys = pc["_props"]["_serializedKeys"]
            vals = pc["_props"]["_serializedValues"]
            new_keys = []
            new_vals = []
            for k, v in zip(keys, vals):
                if k in ("mace", "gun"):
                    k = "gun"
                    v["Name"] = "gun"
                    v["InitFlags"] = 0
                    v["_startActive"] = False
                    v["RootPath"] = "character_model/Reference/Hips/Spine/Spine1/LeftShoulder/LeftArm/LeftArmRoll/LeftForeArm/LeftForeArmRoll/LeftHand"
                    v["OverrideController"] = {"m_FileID": 0, "m_PathID": 0}
                    v["PositionOffset"] = GUN_POS_LH
                    v["RotationOffset"] = {"x": 0.0, "y": 0.0, "z": 0.0}
                    v["Scale"] = {"x": 1.0, "y": 1.0, "z": 1.0}
                    v["_animator"] = {"m_FileID": 0, "m_PathID": 0}
                    v["_renderers"] = [{"m_FileID": 0, "m_PathID": gun_smr_pid}]
                elif k in ("staticCannon", "sword"):
                    k = "sword"
                    v["Name"] = "sword"
                    v["InitFlags"] = 0
                    v["_startActive"] = False
                    v["RootPath"] = "character_model/Reference/Hips/Spine/Spine1/RightShoulder/RightArm/RightArmRoll/RightForeArm/RightForeArmRoll/RightHand"
                    v["OverrideController"] = {"m_FileID": 0, "m_PathID": 0}
                    v["PositionOffset"] = SWORD_POS_RH
                    v["RotationOffset"] = {"x": 0.0, "y": 0.0, "z": 0.0}
                    v["Scale"] = {"x": 1.0, "y": 1.0, "z": 1.0}
                    v["_animator"] = {"m_FileID": 0, "m_PathID": 0}
                    v["_renderers"] = [{"m_FileID": 0, "m_PathID": sword_smr_pid}]
                elif k in ("cannon", "transformed_2"):
                    k = "transformed_2"
                    v["Name"] = "transformed_2"
                    v["InitFlags"] = 0
                    v["RootPath"] = "character_model/Reference/Hips"
                    v["OverrideController"] = {"m_FileID": 0, "m_PathID": JET_AOC_PID}
                    v["PositionOffset"] = {"x": 0.0, "y": 0.0, "z": 0.0}
                    v["RotationOffset"] = {"x": 0.0, "y": -90.0, "z": 90.0}
                    v["_renderers"] = [{"m_FileID": 0, "m_PathID": jet_smr_pid}]
                elif k == "transformed":
                    v["InitFlags"] = 8
                    v["RootPath"] = "character_model/Reference/Hips"
                    v["PositionOffset"] = {"x": 0.0, "y": 0.0, "z": 0.0}
                    v["RotationOffset"] = {"x": 0.0, "y": -90.0, "z": 90.0}
                new_keys.append(k)
                new_vals.append(v)
            pc["_props"]["_serializedKeys"] = new_keys
            pc["_props"]["_serializedValues"] = new_vals
            obj_map[pc_pid].save_typetree(pc)
            print(f"  [PropsController] {pc_pid}: keys={new_keys} ('gun'@LeftHand, 'sword'@RightHand, 'transformed'/'transformed_2'@Hips)")

    # 8. Replace Atlased Textures + Standalone Weapons Textures
    print("[*] Replacing atlased & weapon textures (RGBA32 format)...")
    set_texture(obj_map[TEX_ROBOT_DIFF_PID], TEX_DIR / "cha_blitzwing_main_Diffuse.png", "cha_blitzwing_main_Diffuse", is_raoe=False)
    set_texture(obj_map[TEX_ROBOT_NM_PID], TEX_DIR / "cha_blitzwing_main_Normal.png", "cha_blitzwing_main_Normal", is_raoe=False)
    set_texture(obj_map[TEX_ROBOT_RAOE_PID], TEX_DIR / "cha_blitzwing_main_RAOE.png", "cha_blitzwing_main_RAOE", is_raoe=True)

    set_texture(obj_map[TEX_VEH_DIFF_PID], TEX_DIR / "cha_blitzwing_tform_misc_Diffuse.png", "cha_blitzwing_tform_misc_Diffuse", is_raoe=False)
    set_texture(obj_map[TEX_VEH_NM_PID], TEX_DIR / "cha_blitzwing_tform_misc_Normal.png", "cha_blitzwing_tform_misc_Normal", is_raoe=False)
    set_texture(obj_map[TEX_VEH_RAOE_PID], TEX_DIR / "cha_blitzwing_tform_misc_RAOE.png", "cha_blitzwing_tform_misc_RAOE", is_raoe=True)

    set_texture(obj_map[TEX_WPNS_DIFF_PID], TEX_DIR / "cha_blitzwing_wpns_Diffuse.png", "cha_blitzwing_wpns_Diffuse", is_raoe=False)
    set_texture(obj_map[TEX_WPNS_NM_PID], TEX_DIR / "cha_blitzwing_wpns_Normal.png", "cha_blitzwing_wpns_Normal", is_raoe=False)
    set_texture(obj_map[TEX_WPNS_RAOE_PID], TEX_DIR / "cha_blitzwing_wpns_RAOE.png", "cha_blitzwing_wpns_RAOE", is_raoe=True)

    # 9. Configure Kabam PBR Materials
    for mat_pid in (MAT_ROBOT_PID, MAT_VEHICLE_PID, MAT_SECONDARY_PID, MAT_WPNS_PID):
        if mat_pid in obj_map:
            mat = obj_map[mat_pid].read_typetree()
            is_wpn = (mat_pid == MAT_WPNS_PID)
            if is_wpn:
                diff_id, nm_id, raoe_id = TEX_WPNS_DIFF_PID, TEX_WPNS_NM_PID, TEX_WPNS_RAOE_PID
            elif mat_pid == MAT_ROBOT_PID:
                diff_id, nm_id, raoe_id = TEX_ROBOT_DIFF_PID, TEX_ROBOT_NM_PID, TEX_ROBOT_RAOE_PID
            else:
                diff_id, nm_id, raoe_id = TEX_VEH_DIFF_PID, TEX_VEH_NM_PID, TEX_VEH_RAOE_PID
            patch_kabam_character_mat(mat, diff_id, nm_id, raoe_id, metallic=0.65, is_wpn=is_wpn)
            obj_map[mat_pid].save_typetree(mat)
            if is_wpn:
                print(f"  [Material] Patched PID {mat_pid} ('{mat['m_Name']}'): diff_tex={diff_id}, GLOWING ENERGON SWORD (emissive_none=0.0, overbright=35.0, col=onslaught neon purple)")
            else:
                print(f"  [Material] Patched PID {mat_pid} ('{mat['m_Name']}'): diff_tex={diff_id}, emissive_none=1.0, emissive_overbright=0.0")

    # General safeguard: neutralize emissive on ALL non-FX materials in the bundle WITHOUT touching textures
    exempt_pids = {MAT_ROBOT_PID, MAT_VEHICLE_PID, MAT_SECONDARY_PID, -9117353815363826346}
    for o in env.objects:
        if o.type.name == "Material" and o.path_id not in exempt_pids:
            mat = o.read_typetree()
            mname = mat.get("m_Name", "")
            if not mname.startswith("fx_m_"):
                floats = mat["m_SavedProperties"]["m_Floats"]
                f_dict = dict(floats)
                if f_dict.get("_emissive_overbright_range", 0.0) > 0.0 or f_dict.get("_emissive_none", 1.0) != 1.0:
                    neutralize_emissive_only(mat)
                    o.save_typetree(mat)
                    print(f"  [Material Safeguard] Neutralized emissive on {o.path_id} ('{mname}')")

    # 9b. Inject Custom Triple-Changer SP3 AnimationClips & MatineeData if compiled bundle exists
    sp3_clips_path = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "bw_sp3_clips.assetbundle"
    if sp3_clips_path.exists():
        import patch_sp3_matinee
        print("[*] Applying Phase 3C Triple-Changer SP3 clips & MatineeData patch...")
        patch_sp3_matinee.apply_sp3_matinee(env, sp3_clips_path=sp3_clips_path)

    # 10. Rename CAB file entries right before saving
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

    OUT_BUNDLE.parent.mkdir(parents=True, exist_ok=True)
    OUT_BUNDLE.write_bytes(env.file.save(packer="lz4"))
    size_mb = OUT_BUNDLE.stat().st_size / (1024 * 1024)
    print(f"[✓] Saved {OUT_BUNDLE} ({size_mb:.2f} MB, packer='lz4', CAB={NEW_CAB})")

    # 11. Verify Persisted Bundle
    verify_env = UnityPy.load(str(OUT_BUNDLE))
    v_map = {o.path_id: o for o in verify_env.objects}
    print(f"[*] Verified reloaded CAB files: {list(verify_env.file.files.keys())}")
    for pid in (TEX_ROBOT_DIFF_PID, TEX_ROBOT_NM_PID, TEX_ROBOT_RAOE_PID, TEX_VEH_DIFF_PID, TEX_VEH_NM_PID, TEX_VEH_RAOE_PID):
        vt = v_map[pid].read()
        img = vt.image
        extrema = img.getextrema() if img else "N/A"
        print(f"    [Persisted Tex] {pid}: '{vt.m_Name}' {vt.m_Width}x{vt.m_Height} fmt={vt.m_TextureFormat} extrema={extrema}")
    for pid in (MESH_ROBOT_PID, MESH_VEHICLE_PID, MESH_JET_PID):
        vm = v_map[pid].read_typetree()
        print(f"    [Persisted Mesh] {pid}: '{vm['m_Name']}' verts={vm['m_VertexData']['m_VertexCount']} bones={len(vm['m_BoneNameHashes'])} submeshes={len(vm['m_SubMeshes'])}")

    # Verify material textures
    v_veh_mat = v_map[MAT_VEHICLE_PID].read_typetree()
    v_veh_tex = dict(v_veh_mat["m_SavedProperties"]["m_TexEnvs"])
    veh_base_pid = v_veh_tex["_base_tex"]["m_Texture"]["m_PathID"]
    assert veh_base_pid == TEX_VEH_DIFF_PID, f"MAT_VEHICLE_PID has wrong _base_tex: {veh_base_pid} (expected {TEX_VEH_DIFF_PID})"
    print(f"    [Verified Vehicle Mat] PID {MAT_VEHICLE_PID} ('{v_veh_mat['m_Name']}'): _base_tex={veh_base_pid} [OK]")


if __name__ == "__main__":
    main()
