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
                 _Color=0.68, _base_col=0.68 (prevent specular clipping on cartoon paint)
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

import struct
from pathlib import Path
from PIL import Image
import UnityPy
from UnityPy.enums import TextureFormat

ROOT = Path(r"E:\Agent\TFTF-blender")
DONOR_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_gs_leader2015_odr" / "megatron_gs_leader2015.assetbundle"
MESH_BUNDLE = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "blitzwing_mesh.assetbundle"
TEX_DIR = ROOT / "tools" / "blitzwing" / "atlased_textures"
OUT_BUNDLE = ROOT / "assets_redeco" / "blitzwing_gs.assetbundle"

NEW_CAB = "CAB-7b4900007b4900007b4900007b490001"

# Exact donor PIDs from megatron_gs_leader2015.assetbundle
MESH_ROBOT_PID = 3463271531423751283
MESH_VEHICLE_PID = 8396146535644667895
MESH_JET_PID = -6391917038499381755

SMR_ROBOT_PIDS = (-8610528988658655013, -4173104293130818967)
SMR_VEHICLE_PIDS = (2138194849323017337, 4626197738286450028)
SMR_JET_PIDS = (-7481134504555158405, 3992037002325232027)
SMR_WEAPON_PIDS = (
    4561093141354196631, 8495398593779105175,  # staticCannon
    7267330081541926865, -6758328762533593613,  # mace
)

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

TEX_ROBOT_DIFF_PID = 1215366976128313824
TEX_ROBOT_NM_PID = 3871664243983383179
TEX_ROBOT_RAOE_PID = 4263548866435318379

TEX_VEH_DIFF_PID = -1301823324166226518
TEX_VEH_NM_PID = -3812894415876002048
TEX_VEH_RAOE_PID = -8835585150668275629


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


def patch_kabam_character_mat(mat: dict, diff_pid: int, nm_pid: int, raoe_pid: int, metallic: float):
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

    float_overrides = {
        "_Mode": 3.0,
        "_ZWrite": 1.0,
        "_metallic_range": metallic,
        "_roughness_range": 0.78,
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

    # Section 11.9 item 4: 0.68 prevents specular clipping/white blowout on cartoon paint
    tint_color = {"r": 0.68, "g": 0.68, "b": 0.68, "a": 1.0}
    zero_emissive = {"r": 0.0, "g": 0.0, "b": 0.0, "a": 0.0}
    color_overrides = {
        "_Color": tint_color,
        "_base_col": tint_color,
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

    print(f"[*] Loading Megatron donor bundle: {DONOR_BUNDLE}")
    env = UnityPy.load(str(DONOR_BUNDLE))

    cab_files = [k for k in env.file.files.keys() if k.lower().startswith("cab-") and "." not in k]
    assert cab_files, f"Could not detect CAB inside donor bundle: {list(env.file.files.keys())}"
    old_cab = cab_files[0]
    old_cab_low = old_cab.lower()
    new_cab_low = NEW_CAB.lower()
    print(f"[*] Remapping CAB: {old_cab} -> {NEW_CAB}")

    obj_map = {o.path_id: o for o in env.objects}

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
        MESH_ROBOT_PID, MESH_VEHICLE_PID, MESH_JET_PID,
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
    # Transform vertices from Blender: (x, y, z) -> (x, z, -y)
    # Ground at z=0 becomes Unity y=0. Cannon tip at -y=-(-5.368)=+5.368 facing +Z forward.
    # Bind 100% to COG bone (Identity bindpose)
    src_t_tt = bw_meshes[tank_mesh_name]
    dst_t_obj = obj_map[MESH_VEHICLE_PID]
    dst_t_tt = dst_t_obj.read_typetree()

    vd_t = src_t_tt["m_VertexData"]
    vcount_t = vd_t["m_VertexCount"]
    data_t = bytearray(vd_t["m_DataSize"])
    xs, ys, zs = [], [], []
    for i in range(vcount_t):
        off = i * 40
        x, y, z = struct.unpack_from("<fff", data_t, off)
        nx, ny, nz = struct.unpack_from("<fff", data_t, off + 12)
        tx, ty, tz, tw = struct.unpack_from("<ffff", data_t, off + 24)

        new_x = x
        new_y = z          # Ground at y=0.0
        new_z = -y         # Cannon forward at +Z

        new_nx = nx
        new_ny = nz
        new_nz = -ny

        new_tx = tx
        new_ty = tz
        new_tz = -ty

        struct.pack_into("<fff", data_t, off, new_x, new_y, new_z)
        struct.pack_into("<fff", data_t, off + 12, new_nx, new_ny, new_nz)
        struct.pack_into("<ffff", data_t, off + 24, new_tx, new_ty, new_tz, tw)

        xs.append(new_x); ys.append(new_y); zs.append(new_z)

    # Bind 100% to bone index 0 (COG) in stream 2 (format 10)
    # CRITICAL: Unity 16-byte aligns each vertex stream! For vcount_t=6645 (odd):
    # Stream 0 = (6645*40 + 15) & ~15 = 265808; Stream 1 = (6645*8 + 15) & ~15 = 53168; Stream 2 = 318976
    s0_t_bytes = (vcount_t * 40 + 15) & ~15
    s1_t_bytes = (vcount_t * 8 + 15) & ~15
    stream2_t_off = s0_t_bytes + s1_t_bytes
    for i in range(vcount_t):
        off = stream2_t_off + i * 4
        data_t[off] = 0    # bone 0 = COG
        data_t[off+1] = 0
        data_t[off+2] = 0
        data_t[off+3] = 0

    src_t_tt["m_VertexData"]["m_DataSize"] = bytes(data_t)

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
    dst_t_tt["m_LocalAABB"] = {
        "m_Center": {"x": 0.0, "y": (min(ys) + max(ys)) / 2.0, "z": (min(zs) + max(zs)) / 2.0},
        "m_Extent": {"x": 10.0, "y": 10.0, "z": 10.0},
    }
    for sm in dst_t_tt.get("m_SubMeshes", []):
        sm["localAABB"] = dict(dst_t_tt["m_LocalAABB"])
    dst_t_tt["m_IsReadable"] = True
    dst_t_tt["m_KeepVertices"] = True
    dst_t_tt["m_KeepIndices"] = True
    dst_t_tt["m_MeshUsageFlags"] = 1
    dst_t_obj.save_typetree(dst_t_tt)
    print(f"  [Mesh Tank] {MESH_VEHICLE_PID} -> 'cha_blitzwing_gs_01' verts={vcount_t} stream2_off={stream2_t_off} bounds: X=[{min(xs):.2f}, {max(xs):.2f}] Y=[{min(ys):.2f}, {max(ys):.2f}] Z=[{min(zs):.2f}, {max(zs):.2f}]")

    # 5. Graft Jet Mesh
    # Transform vertices from Blender: (x, y, z) -> (x, z + 0.30, -y)
    # Nosecone at -y=-(-6.436)=+6.436 facing +Z forward.
    # Bind 100% to COG bone (cog_inverse_matrix bindpose)
    src_j_tt = bw_meshes[jet_mesh_name]
    dst_j_obj = obj_map[MESH_JET_PID]
    dst_j_tt = dst_j_obj.read_typetree()

    vd_j = src_j_tt["m_VertexData"]
    vcount_j = vd_j["m_VertexCount"]
    data_j = bytearray(vd_j["m_DataSize"])
    j_xs, j_ys, j_zs = [], [], []
    for i in range(vcount_j):
        off = i * 40
        x, y, z = struct.unpack_from("<fff", data_j, off)
        nx, ny, nz = struct.unpack_from("<fff", data_j, off + 12)
        tx, ty, tz, tw = struct.unpack_from("<ffff", data_j, off + 24)

        new_x = x
        new_y = z + 0.30   # Hovering slightly above ground
        new_z = -y         # Nosecone forward at +Z

        new_nx = nx
        new_ny = nz
        new_nz = -ny

        new_tx = tx
        new_ty = tz
        new_tz = -ty

        struct.pack_into("<fff", data_j, off, new_x, new_y, new_z)
        struct.pack_into("<fff", data_j, off + 12, new_nx, new_ny, new_nz)
        struct.pack_into("<ffff", data_j, off + 24, new_tx, new_ty, new_tz, tw)

        j_xs.append(new_x); j_ys.append(new_y); j_zs.append(new_z)

    # Normalize negative UVs in stream 1 (16-byte aligned stream offset)
    stream1_off = (vcount_j * 40 + 15) & ~15
    stream1_j_bytes = (vcount_j * 8 + 15) & ~15
    for i in range(vcount_j):
        off = stream1_off + i * 8
        u, v = struct.unpack_from("<ff", data_j, off)
        if v < 0:
            v += 0.5
            struct.pack_into("<ff", data_j, off, u, v)

    # Bind 100% to bone index 0 (COG) in stream 2 (format 10)
    stream2_j_off = stream1_off + stream1_j_bytes
    for i in range(vcount_j):
        off = stream2_j_off + i * 4
        data_j[off] = 0    # bone 0 = COG
        data_j[off+1] = 0
        data_j[off+2] = 0
        data_j[off+3] = 0

    src_j_tt["m_VertexData"]["m_DataSize"] = bytes(data_j)

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
    dst_j_tt["m_LocalAABB"] = {
        "m_Center": {"x": 0.0, "y": (min(j_ys) + max(j_ys)) / 2.0, "z": (min(j_zs) + max(j_zs)) / 2.0},
        "m_Extent": {"x": 10.0, "y": 10.0, "z": 10.0},
    }
    for sm in dst_j_tt.get("m_SubMeshes", []):
        sm["localAABB"] = dict(dst_j_tt["m_LocalAABB"])
    dst_j_tt["m_IsReadable"] = True
    dst_j_tt["m_KeepVertices"] = True
    dst_j_tt["m_KeepIndices"] = True
    dst_j_tt["m_MeshUsageFlags"] = 1
    dst_j_obj.save_typetree(dst_j_tt)
    print(f"  [Mesh Jet] {MESH_JET_PID} -> 'cha_blitzwing_gs_02' verts={vcount_j} bounds: X=[{min(j_xs):.2f}, {max(j_xs):.2f}] Y=[{min(j_ys):.2f}, {max(j_ys):.2f}] Z=[{min(j_zs):.2f}, {max(j_zs):.2f}]")

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

    # Disable unused weapon SMRs
    for pid in SMR_WEAPON_PIDS:
        smr = obj_map[pid].read_typetree()
        smr["m_Enabled"] = False
        # Note: keep smr["m_Mesh"] pointing to original mesh so Unity won't throw 'Bone weights do not match bones'
        obj_map[pid].save_typetree(smr)
        go_pid = smr["m_GameObject"]["m_PathID"]
        if go_pid in obj_map:
            go = obj_map[go_pid].read_typetree()
            go["m_IsActive"] = False
            obj_map[go_pid].save_typetree(go)
    print(f"  [SMR Weapons] Disabled {len(SMR_WEAPON_PIDS)} weapon SMRs and GameObjects")

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

    # 6e. Bind Character Fight AOC's char_misc_01 (4070315435280742960) to Ramjet_Normal_attackHeavy (-8287216037977883126)
    # and match Base.Misc01 transition in animator_char_fight (-6923321525341018075) to Base.HeavyAttack!
    CHAR_FIGHT_AOC_PID = -7755666207738536548
    if CHAR_FIGHT_AOC_PID in obj_map:
        char_aoc = obj_map[CHAR_FIGHT_AOC_PID].read_typetree()
        for clip_pair in char_aoc.get("m_Clips", []):
            orig = clip_pair.get("m_OriginalClip", {})
            if orig.get("m_PathID") == 4070315435280742960:  # char_misc_01
                clip_pair["m_OverrideClip"] = {"m_FileID": 5, "m_PathID": -8287216037977883126}  # Ramjet_Normal_attackHeavy
        obj_map[CHAR_FIGHT_AOC_PID].save_typetree(char_aoc)
        print(f"  [Char Fight AOC] Bound char_misc_01 -> Ramjet_Normal_attackHeavy (-8287216037977883126) on {CHAR_FIGHT_AOC_PID}")

    CHAR_FIGHT_AC_PID = -6923321525341018075
    if CHAR_FIGHT_AC_PID in obj_map:
        ac = obj_map[CHAR_FIGHT_AC_PID].read_typetree()
        for sm in ac.get("m_Controller", {}).get("m_StateMachineArray", []):
            sm_data = sm.get("data", sm)
            states = sm_data.get("m_StateConstantArray", [])
            ha_transitions = None
            ha_ik_on_feet = False
            ha_tag_id = 1080829965
            for st in states:
                d = st.get("data", st)
                if d.get("m_NameID") == 2579208148:  # HeavyAttack
                    ha_transitions = list(d.get("m_TransitionConstantArray", []))
                    ha_ik_on_feet = d.get("m_IKOnFeet", False)
                    ha_tag_id = d.get("m_TagID", 1080829965)
            if ha_transitions:
                for st in states:
                    d = st.get("data", st)
                    if d.get("m_NameID") == 732291567:  # Misc01
                        d["m_TransitionConstantArray"] = ha_transitions
                        d["m_IKOnFeet"] = ha_ik_on_feet
                        d["m_TagID"] = ha_tag_id
        obj_map[CHAR_FIGHT_AC_PID].save_typetree(ac)
        print(f"  [Char Fight AC] Synced Base.Misc01 transitions, m_IKOnFeet={ha_ik_on_feet}, m_TagID={ha_tag_id} with Base.HeavyAttack on {CHAR_FIGHT_AC_PID}")

    # 6f. Register move_heavy_ramjet_donut in MoveSet with _animStateName = "Base.Misc01"
    # so Base.HeavyAttack (Tank: move_heavy_megatron_gs_shoot) and Base.Misc01 (Jet: move_heavy_ramjet_donut)
    # coexist in MoveSet._moveHashDictionary without clobbering each other!
    MOVESET_COMBAT_PID = 5996528693102170603
    if MOVESET_COMBAT_PID in obj_map:
        ms_obj = obj_map[MOVESET_COMBAT_PID]
        ms_tt = ms_obj.read_typetree()
        for m in ms_tt["_moves"]:
            if m.get("_name") == "move_heavy_ramjet_donut":
                m["_animStateName"] = "Base.Misc01"
        has_jet_move = any(m.get("_name") == "move_heavy_ramjet_donut" for m in ms_tt["_moves"])
        if not has_jet_move:
            ms_tt["_moves"].append({
                "_name": "move_heavy_ramjet_donut",
                "_animStateName": "Base.Misc01",
                "_asset": {"m_FileID": 7, "m_PathID": -8528702938335562906},
            })
        ms_obj.save_typetree(ms_tt)
        print(f"  [MoveSet] Registered 'move_heavy_ramjet_donut' as 'Base.Misc01' in MoveSet {MOVESET_COMBAT_PID}")

    # 7. Configure PropsController in Showcase and Combat LW
    # - Remove unused 'staticCannon' and 'mace' props so staticCannon (InitFlags=7, 3 bones) never conflicts with MESH_JET_PID
    # - Attach BOTH 'transformed' (Tank) and 'transformed_2' (Jet) to 'character_model/Reference/Hips' with Rot=(0, -90, 90)
    #   so 'transformed_2' follows Hips along the 3D banking loop in Ramjet_Normal_attackHeavy!
    for pc_pid, jet_smr_pid in [
        (PROPS_SHOWCASE_PID, -7481134504555158405),
        (PROPS_COMBAT_PID, 3992037002325232027),
    ]:
        if pc_pid in obj_map:
            pc = obj_map[pc_pid].read_typetree()
            keys = pc["_props"]["_serializedKeys"]
            vals = pc["_props"]["_serializedValues"]
            new_keys = []
            new_vals = []
            for k, v in zip(keys, vals):
                if k in ("staticCannon", "mace"):
                    continue
                if k in ("cannon", "transformed_2"):
                    k = "transformed_2"
                    v["Name"] = "transformed_2"
                    v["InitFlags"] = 0  # Hidden in showcase, enabled dynamically in combat Jet mode
                    v["RootPath"] = "character_model/Reference/Hips"
                    v["OverrideController"] = {"m_FileID": 0, "m_PathID": JET_AOC_PID}
                    v["PositionOffset"] = {"x": 0.0, "y": 0.0, "z": 0.0}
                    v["RotationOffset"] = {"x": 0.0, "y": -90.0, "z": 90.0}
                    v["_renderers"] = [{"m_FileID": 0, "m_PathID": jet_smr_pid}]
                elif k == "transformed":
                    v["InitFlags"] = 8  # Shown in showcase transformed mode (Tank only)
                    v["RootPath"] = "character_model/Reference/Hips"
                    v["PositionOffset"] = {"x": 0.0, "y": 0.0, "z": 0.0}
                    v["RotationOffset"] = {"x": 0.0, "y": -90.0, "z": 90.0}
                new_keys.append(k)
                new_vals.append(v)
            pc["_props"]["_serializedKeys"] = new_keys
            pc["_props"]["_serializedValues"] = new_vals
            obj_map[pc_pid].save_typetree(pc)
            print(f"  [PropsController] {pc_pid}: keys={new_keys} ('transformed' & 'transformed_2' both on Hips with Rot=(0,-90,90))")

    # 8. Replace Atlased Textures (Strict Section 11.9: zero emissive, metallic in NM.B)
    print("[*] Replacing atlased textures (RGBA32 format, zero emissive in RAOE.B)...")
    set_texture(obj_map[TEX_ROBOT_DIFF_PID], TEX_DIR / "cha_blitzwing_main_Diffuse.png", "cha_blitzwing_main_Diffuse", is_raoe=False)
    set_texture(obj_map[TEX_ROBOT_NM_PID], TEX_DIR / "cha_blitzwing_main_Normal.png", "cha_blitzwing_main_Normal", is_raoe=False)
    set_texture(obj_map[TEX_ROBOT_RAOE_PID], TEX_DIR / "cha_blitzwing_main_RAOE.png", "cha_blitzwing_main_RAOE", is_raoe=True)

    set_texture(obj_map[TEX_VEH_DIFF_PID], TEX_DIR / "cha_blitzwing_tform_misc_Diffuse.png", "cha_blitzwing_tform_misc_Diffuse", is_raoe=False)
    set_texture(obj_map[TEX_VEH_NM_PID], TEX_DIR / "cha_blitzwing_tform_misc_Normal.png", "cha_blitzwing_tform_misc_Normal", is_raoe=False)
    set_texture(obj_map[TEX_VEH_RAOE_PID], TEX_DIR / "cha_blitzwing_tform_misc_RAOE.png", "cha_blitzwing_tform_misc_RAOE", is_raoe=True)

    # 9. Configure Kabam PBR Materials (Zero emissive blowout, anti-clipping tint)
    for mat_pid in (MAT_ROBOT_PID, MAT_VEHICLE_PID, MAT_SECONDARY_PID, -9117353815363826346):
        if mat_pid in obj_map:
            mat = obj_map[mat_pid].read_typetree()
            diff_id = TEX_ROBOT_DIFF_PID if mat_pid in (MAT_ROBOT_PID, -9117353815363826346) else TEX_VEH_DIFF_PID
            nm_id = TEX_ROBOT_NM_PID if mat_pid in (MAT_ROBOT_PID, -9117353815363826346) else TEX_VEH_NM_PID
            raoe_id = TEX_ROBOT_RAOE_PID if mat_pid in (MAT_ROBOT_PID, -9117353815363826346) else TEX_VEH_RAOE_PID
            patch_kabam_character_mat(mat, diff_id, nm_id, raoe_id, metallic=0.65)
            obj_map[mat_pid].save_typetree(mat)
            print(f"  [Material] Patched PID {mat_pid} ('{mat['m_Name']}'): emissive_none=1.0, emissive_overbright=0.0")

    # General safeguard: neutralize emissive on ALL non-FX materials in the bundle
    for o in env.objects:
        if o.type.name == "Material":
            mat = o.read_typetree()
            mname = mat.get("m_Name", "")
            if not mname.startswith("fx_m_"):
                floats = mat["m_SavedProperties"]["m_Floats"]
                f_dict = dict(floats)
                if f_dict.get("_emissive_overbright_range", 0.0) > 0.0 or f_dict.get("_emissive_none", 1.0) != 1.0:
                    patch_kabam_character_mat(mat, TEX_ROBOT_DIFF_PID, TEX_ROBOT_NM_PID, TEX_ROBOT_RAOE_PID, metallic=0.65)
                    o.save_typetree(mat)
                    print(f"  [Material Safeguard] Patched {o.path_id} ('{mname}')")

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


if __name__ == "__main__":
    main()
