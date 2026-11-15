#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_tarn_bundle.py
Builds assets_redeco/tarn_gs.assetbundle by grafting Tarn's baked Robot/Vehicle meshes,
3-map Kabam PBR textures, Galvatron projectiles & shooting actions, and Shockwave's S2
onto Ultra Magnus (ultramagnus_gs_leader) donor bundle:
  - 1.2x vehicle scaling with strict ground-contact preservation (no sinking into ground)
  - Galvatron ranged shooting from right arm cannon + projectiles
  - S1 changed to Galvatron's S2 (move_galvatron_special_02)
  - S2 changed to Shockwave's S2 (move_shockwave_special_02)
  - Decepticon purple/magenta FX recoloring
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import copy
import io
import struct
from collections import deque
from pathlib import Path
from PIL import Image
import UnityPy
from UnityPy.enums import TextureFormat
from UnityPy.files import ObjectReader
from UnityPy.files.SerializedFile import LocalSerializedObjectIdentifier
from UnityPy.streams import EndianBinaryReader

ROOT = Path(r"E:\Agent\TFTF-blender")
DONOR_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "ultramagnus_gs_leader_odr" / "ultramagnus_gs_leader.assetbundle"
TARN_MESH_BUNDLE = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "tarn_mesh.assetbundle"
GAL_BUNDLE = ROOT / "tools" / "tarn" / "donor_sources" / "galvatron_gs_voyager2016.assetbundle"
ANIM_BUNDLE = ROOT / "assets_netflix" / "character_anim_procedural.assetbundle"
TEX_DIR = ROOT / "3rd-party-models" / "Tarn" / "06_working" / "unified_textures"
OUT_BUNDLE = ROOT / "assets_redeco" / "tarn_gs.assetbundle"

NEW_CAB = "CAB-7a4900007a4900007a4900007a490001"  # 32 lowercase hex digits

# Exact donor PIDs verified from ultramagnus_gs_leader.assetbundle
MESH_ROBOT_PID = -3677919709812409737
MESH_VEHICLE_PID = 1965915829973675685

SMR_ROBOT_PIDS = (-4497864873147514607, -5669485655896040359)
SMR_VEHICLE_PIDS = (6374655313817044002, 7769099272486437918)
SMR_WEAPON_PIDS = (
    -6929876573960912518, 8776407398459535180,  # axe_right
    -3806277267122844283, 5537406516109862368,  # gun_right
    -3099658301619870697, 4543470380929569169,  # pistol_left
)

MAT_ROBOT_PID = 5520268204611603145
MAT_VEHICLE_PID = 5691636987978222339

TEX_ROBOT_DIFF_PID = -6970767896792368081
TEX_ROBOT_NM_PID = 5841746967496826142
TEX_ROBOT_RAOE_PID = -7076967624015231670

TEX_VEH_DIFF_PID = -695917625355825749
TEX_VEH_NM_PID = -3742620179713543448
TEX_VEH_RAOE_PID = -8868189788918103369

FX_MAT_PIDS = (
    -8252988663645228829,  # fx_m_energy_wave_a
    147355351511293498,    # fx_m_energy_shockwave_a
    -5813945392773663879,  # fx_m_tiled_crack_rock_hot
    -487659167540195070,   # fx_m_tiled_crack_rock
    982866352748045095,    # fx_m_axe_glow_ultramagnus_a
)

# Key Component PIDs on Ultra Magnus
MOVESET_PID = -3211011380908751738
PREFABLIB_PID = -1092944810220189528
FIGHT_AOC_PID = 784857089895726382
RFARM_TR_PID = -7764485098169793919


def is_chromatic(c: dict, threshold: float = 0.12) -> bool:
    r, g, b = float(c.get("r", 1.0)), float(c.get("g", 1.0)), float(c.get("b", 1.0))
    return (max(r, g, b) - min(r, g, b)) > threshold


def to_purple_color(c: dict, lum_floor: float = 0.35) -> dict:
    r, g, b = float(c.get("r", 1.0)), float(c.get("g", 1.0)), float(c.get("b", 1.0))
    lum = max(lum_floor, min(1.0, 0.299 * r + 0.587 * g + 0.114 * b))
    return {
        "r": round(0.92 * lum, 4),
        "g": round(0.14 * lum, 4),
        "b": round(1.00 * lum, 4),
        "a": float(c.get("a", 1.0)),
    }


def remap_gradient(grad: dict) -> int:
    changed = 0
    if not isinstance(grad, dict):
        return 0
    nkeys = int(grad.get("m_NumColorKeys", 0))
    for i in range(max(nkeys, 2)):
        kname = f"key{i}"
        k = grad.get(kname)
        if isinstance(k, dict) and is_chromatic(k):
            nk = to_purple_color(k)
            k["r"], k["g"], k["b"] = nk["r"], nk["g"], nk["b"]
            changed += 1
    return changed


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
        "_roughness_range": 0.88,
        "_emissive_range": 0.0,
        "_emissive_none": 0.0,
        "_emissive_overbright_range": 36.0,
    }
    floats = mat["m_SavedProperties"]["m_Floats"]
    existing_keys = {k for k, _ in floats}
    new_floats = [(k, float_overrides[k] if k in float_overrides else v) for k, v in floats]
    for k, v in float_overrides.items():
        if k not in existing_keys:
            new_floats.append((k, v))
    mat["m_SavedProperties"]["m_Floats"] = new_floats

    purple_emissive = {"r": 0.90, "g": 0.14, "b": 1.0, "a": 0.0}
    white = {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}
    color_overrides = {
        "_Color": white,
        "_base_col": white,
        "_emissive_intensity_col": purple_emissive,
    }
    colors = mat["m_SavedProperties"]["m_Colors"]
    mat["m_SavedProperties"]["m_Colors"] = [
        (k, dict(color_overrides[k]) if k in color_overrides else v) for k, v in colors
    ]


def set_texture(obj, img_path: Path, name: str, is_raoe: bool = False):
    t = obj.read()
    img = Image.open(img_path)
    if is_raoe:
        img = img.convert("RGB")
        target_fmt = TextureFormat.RGB24
    else:
        img = img.convert("RGBA")
        if img_path.name.endswith("_a.png") or img_path.name.endswith("_A.png"):
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


def iter_pptrs_in_tree(node):
    if isinstance(node, dict):
        if "m_FileID" in node and "m_PathID" in node:
            yield node
        else:
            for v in node.values():
                yield from iter_pptrs_in_tree(v)
    elif isinstance(node, (list, tuple)):
        for item in node:
            yield from iter_pptrs_in_tree(item)


def commit_obj_typetree(obj, tree):
    data = obj.save_typetree(tree)
    obj.reader = EndianBinaryReader(data, endian=obj.reader.endian)
    obj.byte_start = 0
    obj.byte_size = len(data)
    return data


def collect_closure(sf, root_pids, skip_pids=None):
    skip_pids = set(skip_pids or ())
    visited_local = set()
    all_pptrs = set()
    queue = deque()

    for pid in root_pids:
        if pid and pid not in skip_pids and pid in sf.objects and pid not in visited_local:
            visited_local.add(pid)
            all_pptrs.add((0, pid))
            queue.append(pid)

    while queue:
        pid = queue.popleft()
        obj = sf.objects[pid]
        tree = obj.read_typetree()
        for pptr in iter_pptrs_in_tree(tree):
            fid = int(pptr.get("m_FileID", 0))
            target_pid = int(pptr.get("m_PathID", 0))
            if not target_pid:
                continue
            if fid == 0 and target_pid in skip_pids:
                continue
            all_pptrs.add((fid, target_pid))
            if fid == 0 and target_pid not in visited_local:
                if target_pid not in sf.objects:
                    raise RuntimeError(f"Dangling local PPtr in closure from {pid} ({obj.type.name}): m_PathID={target_pid}")
                visited_local.add(target_pid)
                queue.append(target_pid)
    return visited_local, all_pptrs


def _build_ext_file_id_map(src_sf, dst_sf):
    dst_by_path = {ext.path: idx for idx, ext in enumerate(dst_sf.externals, start=1)}
    ext_map = {}
    for idx, ext in enumerate(src_sf.externals, start=1):
        if ext.path in dst_by_path:
            ext_map[idx] = dst_by_path[ext.path]
    return ext_map


def _find_matching_dst_type_id(dst_sf, src_tp, remapped_script_key):
    if src_tp.class_id != 114:
        for idx, tp in enumerate(dst_sf.types):
            if tp.class_id == src_tp.class_id and tp.is_stripped_type == src_tp.is_stripped_type:
                return idx
        return None
    for idx, tp in enumerate(dst_sf.types):
        if tp.class_id == 114 and tp.script_type_index >= 0:
            sref = dst_sf.script_types[tp.script_type_index]
            if (sref.local_serialized_file_index, sref.local_identifier_in_file) == remapped_script_key:
                return idx
    return None


def clone_closure_into_sf(src_sf, dst_sf, root_pids, skip_pids=None, inline_tex_images=None):
    """Clone reachable local objects safely following Chapter 9.2 contract."""
    local_pids, _ = collect_closure(src_sf, root_pids, skip_pids=skip_pids)
    ext_map = _build_ext_file_id_map(src_sf, dst_sf)
    inline_tex_images = inline_tex_images or {}

    # Snapshot existing script_types key for every MonoBehaviour SerializedType before mutating/sorting
    existing_tp_script_keys = {}
    for idx, tp in enumerate(dst_sf.types):
        if getattr(tp, "script_type_index", -1) >= 0:
            sref = dst_sf.script_types[tp.script_type_index]
            existing_tp_script_keys[idx] = (sref.local_serialized_file_index, sref.local_identifier_in_file)

    existing_script_keys = {
        (sref.local_serialized_file_index, sref.local_identifier_in_file)
        for sref in dst_sf.script_types
    }

    src_obj_to_dst_type_id = {}
    for pid in sorted(local_pids):
        src_obj = src_sf.objects[pid]
        src_tp = src_obj.serialized_type
        if src_tp is None:
            raise RuntimeError(f"Source object {pid} ({src_obj.type.name}) has serialized_type=None")

        if pid in dst_sf.objects:
            # Verify shared singleton resource (MonoScript / Shader / AnimatorController)
            dst_obj = dst_sf.objects[pid]
            if dst_obj.class_id != src_obj.class_id:
                raise RuntimeError(f"PID collision at {pid}: src={src_obj.type.name}, dst={dst_obj.type.name}")
            if src_tp.class_id == 115:
                st = src_obj.read_typetree()
                dt = dst_obj.read_typetree()
                assert (st.get("m_ClassName"), st.get("m_Namespace"), st.get("m_AssemblyName")) == (
                    dt.get("m_ClassName"), dt.get("m_Namespace"), dt.get("m_AssemblyName")
                ), f"MonoScript signature mismatch at {pid}"
            elif src_tp.class_id in (48, 91):  # Shader, AnimatorController
                assert src_obj.read_typetree().get("m_Name") == dst_obj.read_typetree().get("m_Name"), f"Name mismatch at {pid}"
            else:
                raise RuntimeError(f"Unexpected PID collision at {pid} ({src_obj.type.name})")
            continue

        remapped_script_key = None
        if src_tp.class_id == 114:
            if src_tp.script_type_index < 0:
                raise RuntimeError(f"MonoBehaviour {pid} has invalid script_type_index={src_tp.script_type_index}")
            src_sref = src_sf.script_types[src_tp.script_type_index]
            orig_fid = src_sref.local_serialized_file_index
            remapped_fid = 0 if orig_fid == 0 else ext_map[orig_fid]
            remapped_script_key = (remapped_fid, src_sref.local_identifier_in_file)

            if remapped_script_key not in existing_script_keys:
                new_sref = LocalSerializedObjectIdentifier.__new__(LocalSerializedObjectIdentifier)
                new_sref.local_serialized_file_index = remapped_script_key[0]
                new_sref.local_identifier_in_file = remapped_script_key[1]
                dst_sf.script_types.append(new_sref)
                existing_script_keys.add(remapped_script_key)

        dst_type_id = _find_matching_dst_type_id(dst_sf, src_tp, remapped_script_key)
        if dst_type_id is None:
            new_tp = copy.copy(src_tp)
            if getattr(new_tp, "type_dependencies", None):
                new_tp.type_dependencies = ()
            dst_type_id = len(dst_sf.types)
            dst_sf.types.append(new_tp)
            if remapped_script_key is not None:
                existing_tp_script_keys[dst_type_id] = remapped_script_key
        elif remapped_script_key is not None:
            existing_tp_script_keys[dst_type_id] = remapped_script_key

        src_obj_to_dst_type_id[pid] = dst_type_id

    # Sort dst_sf.script_types ascending & remap ALL script_type_index values across dst_sf.types
    dst_sf.script_types.sort(key=lambda s: (s.local_serialized_file_index, s.local_identifier_in_file))
    script_key_to_idx = {
        (sref.local_serialized_file_index, sref.local_identifier_in_file): idx
        for idx, sref in enumerate(dst_sf.script_types)
    }
    for tp_idx, key in existing_tp_script_keys.items():
        dst_sf.types[tp_idx].script_type_index = script_key_to_idx[key]

    cloned_pids = []
    for pid in sorted(local_pids):
        if pid in dst_sf.objects:
            continue
        src_obj = src_sf.objects[pid]
        dst_type_id = src_obj_to_dst_type_id[pid]
        dst_tp = dst_sf.types[dst_type_id]

        raw_bytes = src_obj.get_raw_data()
        reader = EndianBinaryReader(raw_bytes, endian=dst_sf.header.endian)
        new_obj = ObjectReader(
            assets_file=dst_sf,
            reader=reader,
            path_id=pid,
            type_id=dst_type_id,
            serialized_type=dst_tp,
            class_id=src_obj.class_id,
            type=src_obj.type,
            byte_start=0,
            byte_size=len(raw_bytes),
            is_destroyed=src_obj.is_destroyed,
            is_stripped=src_obj.is_stripped,
        )

        if pid in inline_tex_images:
            # Avoid external .resS stream reference by baking Texture2D inline
            img, name = inline_tex_images[pid]
            new_obj.set_raw_data(raw_bytes)
            dst_sf.objects[pid] = new_obj
            tex = new_obj.read()
            tex.m_Name = name
            tex.m_StreamData.offset = 0
            tex.m_StreamData.size = 0
            tex.m_StreamData.path = ""
            tex.set_image(img, target_format=TextureFormat.RGBA32, mipmap_count=1)
            tex.save()
            cloned_pids.append(pid)
            continue

        tree = src_obj.read_typetree()
        changed = False
        for pptr in iter_pptrs_in_tree(tree):
            fid = int(pptr.get("m_FileID", 0))
            target_pid = int(pptr.get("m_PathID", 0))
            if fid > 0 and target_pid != 0:
                if fid not in ext_map:
                    src_path = src_sf.externals[fid - 1].path if 1 <= fid <= len(src_sf.externals) else "<OOR>"
                    raise RuntimeError(f"Unmapped external fid={fid} ({src_path}) in object {pid}")
                new_fid = ext_map[fid]
                if new_fid != fid:
                    pptr["m_FileID"] = new_fid
                    changed = True

        if changed:
            commit_obj_typetree(new_obj, tree)
        else:
            new_obj.set_raw_data(raw_bytes)

        dst_sf.objects[pid] = new_obj
        cloned_pids.append(pid)

    dst_sf.mark_changed()
    return cloned_pids


def verify_tarn_bundle_integrity(bundle_path: Path, anim_names: dict):
    """Full Chapter 9.2 Reload Integrity Gate for tarn_gs.assetbundle."""
    env = UnityPy.load(str(bundle_path))
    sf = list(env.assets)[0]

    # 1. SerializedFile.script_types strictly ascending
    st_keys = [(s.local_serialized_file_index, s.local_identifier_in_file) for s in sf.script_types]
    assert st_keys == sorted(st_keys), "sf.script_types is not sorted ascending!"

    for tp in sf.types:
        if tp.class_id == 114:
            assert 0 <= tp.script_type_index < len(sf.script_types), f"Out of range script_type_index {tp.script_type_index}"
            sref = sf.script_types[tp.script_type_index]
            if sref.local_serialized_file_index == 0:
                assert sref.local_identifier_in_file in sf.objects, f"Missing local MonoScript {sref.local_identifier_in_file}"

    # 2. Every object readable, every MonoBehaviour m_Script matches script_types, 0 dangling local PPtrs, 0 bad streams
    new_cab_low = NEW_CAB.lower()
    ab_tree = None
    for pid, obj in sf.objects.items():
        tree = obj.read_typetree()
        if obj.type.name == "AssetBundle":
            ab_tree = tree
        if obj.type.name == "MonoBehaviour":
            assert obj.serialized_type is sf.types[obj.type_id], f"Type mismatch on MonoBehaviour {pid}"
            ms = tree.get("m_Script", {})
            sti = obj.serialized_type.script_type_index
            sref = sf.script_types[sti]
            assert (int(ms.get("m_FileID", 0)), int(ms.get("m_PathID", 0))) == (
                sref.local_serialized_file_index,
                sref.local_identifier_in_file,
            ), f"MonoBehaviour {pid} script mismatch: m_Script={ms} vs script_types[{sti}]={(sref.local_serialized_file_index, sref.local_identifier_in_file)}"

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

    # 3. Verify AssetBundle.m_PreloadTable & m_Container contiguous sorted slices match reachable closures
    assert ab_tree is not None
    preload = [(int(p["m_FileID"]), int(p["m_PathID"])) for p in ab_tree.get("m_PreloadTable", [])]
    cursor = 0
    for cname, cinfo in ab_tree.get("m_Container", []):
        pidx, psize = int(cinfo["preloadIndex"]), int(cinfo["preloadSize"])
        assert pidx == cursor, f"Non-contiguous slice on {cname}: {pidx} != {cursor}"
        cursor += psize
        sl = preload[pidx : pidx + psize]
        _, expected_set = collect_closure(sf, [int(cinfo["asset"]["m_PathID"])])
        sl_set = set(sl)
        missing = expected_set - sl_set
        extra = sl_set - expected_set
        assert not missing and not extra, f"Preload mismatch on {cname}: missing={len(missing)}, extra={len(extra)}"

    # 4. Verify Tarn meshes, moves, AOC, and projectiles
    for pid in (MESH_ROBOT_PID, MESH_VEHICLE_PID):
        vm = sf.objects[pid].read_typetree()
        c = vm["m_LocalAABB"]["m_Center"]
        e = vm["m_LocalAABB"]["m_Extent"]
        print(f"    [Persisted Mesh] {pid}: '{vm['m_Name']}' verts={vm['m_VertexData']['m_VertexCount']}, Y=[{c['y']-e['y']:.3f}, {c['y']+e['y']:.3f}]")

    v_ms = sf.objects[MOVESET_PID].read_typetree()
    for m in v_ms["_moves"]:
        if m["_animStateName"] in ("Base.RangedAttack01", "Base.SpecialAttack01", "Base.SpecialAttack02"):
            print(f"    [Persisted Move] {m['_animStateName']} -> {m['_name']} (asset: {m['_asset']})")

    v_aoc = sf.objects[FIGHT_AOC_PID].read_typetree()
    for pair in v_aoc["m_Clips"]:
        orig_name = anim_names.get(pair["m_OriginalClip"]["m_PathID"], "")
        if orig_name in ("char_attackRanged_01", "char_attackSpecial_01", "char_attackSpecial_02"):
            print(f"    [Persisted AOC] {orig_name} -> {pair['m_OverrideClip']}")

    for pid in (-145817218210720417, 7844017693230829075):
        vp = sf.objects[pid].read_typetree()
        print(f"    [Persisted Projectile] {pid}: '{vp['m_Name']}'")

    print(f"[PASS] Integrity Gate PASSED! objects={len(sf.objects)}, types={len(sf.types)}, script_types={len(st_keys)}, preload={len(preload)}")


def scale_vehicle_mesh(mesh_tt: dict, scale_factor: float = 1.2):
    vd = mesh_tt["m_VertexData"]
    vcount = vd["m_VertexCount"]
    data = bytearray(vd["m_DataSize"])

    ys = [struct.unpack_from("<fff", data, i * 40)[1] for i in range(vcount)]
    y_min = min(ys)

    xs_new, ys_new, zs_new = [], [], []
    for i in range(vcount):
        x, y, z = struct.unpack_from("<fff", data, i * 40)
        nx = x * scale_factor
        nz = z * scale_factor
        ny = y_min + (y - y_min) * scale_factor
        struct.pack_into("<fff", data, i * 40, nx, ny, nz)
        xs_new.append(nx)
        ys_new.append(ny)
        zs_new.append(nz)

    vd["m_DataSize"] = bytes(data)

    aabb = mesh_tt["m_LocalAABB"]
    c = aabb["m_Center"]
    e = aabb["m_Extent"]
    c["x"] *= scale_factor
    c["z"] *= scale_factor
    c["y"] = y_min + (c["y"] - y_min) * scale_factor
    e["x"] *= scale_factor
    e["z"] *= scale_factor
    e["y"] *= scale_factor

    for sm in mesh_tt.get("m_SubMeshes", []):
        sm_aabb = sm.get("localAABB", {})
        sc = sm_aabb.get("m_Center")
        se = sm_aabb.get("m_Extent")
        if sc and se:
            sc["x"] *= scale_factor
            sc["z"] *= scale_factor
            sc["y"] = y_min + (sc["y"] - y_min) * scale_factor
            se["x"] *= scale_factor
            se["z"] *= scale_factor
            se["y"] *= scale_factor

    print(
        f"  [Vehicle Scaled {scale_factor}x] Y_min locked at {y_min:.4f}! "
        f"X=[{min(xs_new):.2f}, {max(xs_new):.2f}], Y=[{min(ys_new):.2f}, {max(ys_new):.2f}], Z=[{min(zs_new):.2f}, {max(zs_new):.2f}]"
    )


def main():
    assert DONOR_BUNDLE.is_file(), f"Missing donor bundle: {DONOR_BUNDLE}"
    assert TARN_MESH_BUNDLE.is_file(), f"Missing tarn mesh bundle: {TARN_MESH_BUNDLE}"
    assert GAL_BUNDLE.is_file(), f"Missing galvatron bundle: {GAL_BUNDLE}"

    print(f"[*] Loading tarn_mesh bundle: {TARN_MESH_BUNDLE}")
    env_m = UnityPy.load(str(TARN_MESH_BUNDLE))
    tarn_meshes = {}
    for o in env_m.objects:
        if o.type.name == "Mesh":
            tt = o.read_typetree()
            tarn_meshes[tt["m_Name"]] = tt
    assert "cha_tarn_gs_00" in tarn_meshes and "cha_tarn_gs_01" in tarn_meshes

    print(f"[*] Loading UM donor bundle: {DONOR_BUNDLE}")
    env = UnityPy.load(str(DONOR_BUNDLE))
    sf_um = [f for f in env.file.files.values() if hasattr(f, "objects")][0]

    # Detect existing CAB prefix
    cab_files = [k for k in env.file.files.keys() if k.lower().startswith("cab-") and "." not in k]
    assert cab_files
    old_cab = cab_files[0]
    old_cab_low = old_cab.lower()
    new_cab_low = NEW_CAB.lower()
    print(f"[*] Remapping CAB: {old_cab} -> {NEW_CAB}")

    # 1. Update AssetBundle container and name
    ab_objs = [o for o in env.objects if o.type.name == "AssetBundle"]
    assert len(ab_objs) == 1
    ab_tt = ab_objs[0].read_typetree()
    ab_tt["m_Name"] = "data/tarn_gs_odr/tarn_gs.assetbundle"
    ab_tt["m_AssetBundleName"] = "data/tarn_gs_odr/tarn_gs.assetbundle"
    new_container = []
    for k, v in ab_tt["m_Container"]:
        nk = k.replace("ultramagnus_gs_leader", "tarn_gs")
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

    # 3. Scale Vehicle Mesh by 1.2x with Ground Preservation (Locking Y_min = 0.0323)
    scale_vehicle_mesh(tarn_meshes["cha_tarn_gs_01"], scale_factor=1.2)

    # 4. Graft Robot & Vehicle Meshes while keeping UM donor bone hashes
    obj_map = {o.path_id: o for o in env.objects}
    for dst_pid, src_name in ((MESH_ROBOT_PID, "cha_tarn_gs_00"), (MESH_VEHICLE_PID, "cha_tarn_gs_01")):
        src_tt = tarn_meshes[src_name]
        dst_obj = obj_map[dst_pid]
        dst_tt = dst_obj.read_typetree()
        keep_hashes = list(dst_tt["m_BoneNameHashes"])
        keep_root_hash = int(dst_tt["m_RootBoneNameHash"])

        dst_tt["m_Name"] = src_name
        for field in (
            "m_SubMeshes",
            "m_Shapes",
            "m_BindPose",
            "m_BonesAABB",
            "m_VariableBoneCountWeights",
            "m_MeshCompression",
            "m_IndexFormat",
            "m_IndexBuffer",
            "m_VertexData",
            "m_CompressedMesh",
            "m_LocalAABB",
            "m_StreamData",
        ):
            dst_tt[field] = src_tt[field]
        dst_tt["m_BoneNameHashes"] = keep_hashes
        dst_tt["m_RootBoneNameHash"] = keep_root_hash
        dst_tt["m_IsReadable"] = True
        dst_tt["m_KeepVertices"] = True
        dst_tt["m_KeepIndices"] = True
        dst_tt["m_MeshUsageFlags"] = 1
        dst_obj.save_typetree(dst_tt)
        print(f"  [Mesh] {dst_pid} -> '{src_name}' verts={src_tt['m_VertexData']['m_VertexCount']}")

    # 5. Update SMRs
    generous_aabb = {
        "m_Center": {"x": 0.0, "y": 0.0, "z": 0.0},
        "m_Extent": {"x": 10.0, "y": 10.0, "z": 10.0},
    }
    for pid in SMR_ROBOT_PIDS:
        smr = obj_map[pid].read_typetree()
        smr["m_Materials"] = [{"m_FileID": 0, "m_PathID": MAT_ROBOT_PID}]
        smr["m_AABB"] = generous_aabb
        smr["m_UpdateWhenOffscreen"] = True
        obj_map[pid].save_typetree(smr)

    for pid in SMR_VEHICLE_PIDS:
        smr = obj_map[pid].read_typetree()
        smr["m_Materials"] = [{"m_FileID": 0, "m_PathID": MAT_VEHICLE_PID}]
        smr["m_AABB"] = generous_aabb
        smr["m_UpdateWhenOffscreen"] = True
        obj_map[pid].save_typetree(smr)

    for pid in SMR_WEAPON_PIDS:
        smr = obj_map[pid].read_typetree()
        smr["m_Enabled"] = False
        smr["m_Mesh"] = {"m_FileID": 0, "m_PathID": 0}
        obj_map[pid].save_typetree(smr)
        go_pid = smr["m_GameObject"]["m_PathID"]
        if go_pid in obj_map:
            go = obj_map[go_pid].read_typetree()
            go["m_IsActive"] = False
            obj_map[go_pid].save_typetree(go)
    print(f"  [SMR Weapons] Disabled {len(SMR_WEAPON_PIDS)} weapon SMRs + GameObjects")

    # 6. Replace Textures
    print("[*] Replacing character textures...")
    set_texture(obj_map[TEX_ROBOT_DIFF_PID], TEX_DIR / "cha_tarn_main_a.png", "cha_tarn_main_a", is_raoe=False)
    set_texture(obj_map[TEX_ROBOT_NM_PID], TEX_DIR / "cha_tarn_main_NM_kabam.png", "cha_tarn_main_NM", is_raoe=False)
    set_texture(obj_map[TEX_ROBOT_RAOE_PID], TEX_DIR / "cha_tarn_main_RAOE.png", "cha_tarn_main_RAOE", is_raoe=True)

    set_texture(obj_map[TEX_VEH_DIFF_PID], TEX_DIR / "cha_tarn_tform_misc_A.png", "cha_tarn_tform_misc_A", is_raoe=False)
    set_texture(obj_map[TEX_VEH_NM_PID], TEX_DIR / "cha_tarn_tform_misc_NM_kabam.png", "cha_tarn_tform_misc_NM", is_raoe=False)
    set_texture(obj_map[TEX_VEH_RAOE_PID], TEX_DIR / "cha_tarn_tform_misc_RAOE.png", "cha_tarn_tform_misc_RAOE", is_raoe=True)

    # 7. Configure Kabam PBR Materials
    mat_r = obj_map[MAT_ROBOT_PID].read_typetree()
    patch_kabam_character_mat(mat_r, TEX_ROBOT_DIFF_PID, TEX_ROBOT_NM_PID, TEX_ROBOT_RAOE_PID, metallic=0.25)
    obj_map[MAT_ROBOT_PID].save_typetree(mat_r)

    mat_v = obj_map[MAT_VEHICLE_PID].read_typetree()
    patch_kabam_character_mat(mat_v, TEX_VEH_DIFF_PID, TEX_VEH_NM_PID, TEX_VEH_RAOE_PID, metallic=0.22)
    obj_map[MAT_VEHICLE_PID].save_typetree(mat_v)
    print("[*] Patched Robot & Vehicle Kabam PBR materials")

    # 8. Purple FX Recoloring
    for pid in FX_MAT_PIDS:
        m = obj_map[pid].read_typetree()
        m["m_SavedProperties"]["m_Colors"] = [
            (k, {"r": 0.95, "g": 0.14, "b": 1.0, "a": 1.0} if k == "_emissive_intensity_col" else v)
            for k, v in m["m_SavedProperties"]["m_Colors"]
        ]
        obj_map[pid].save_typetree(m)

    ps_patched = 0
    light_patched = 0
    for o in env.objects:
        if o.type.name == "ParticleSystem":
            d = o.read_typetree()
            changes = 0
            sc = d.get("InitialModule", {}).get("startColor", {})
            for cname in ("minColor", "maxColor"):
                c = sc.get(cname)
                if isinstance(c, dict) and is_chromatic(c):
                    nk = to_purple_color(c)
                    c.update(nk)
                    changes += 1
            for gname in ("minGradient", "maxGradient"):
                changes += remap_gradient(sc.get(gname))
            for mod_name in ("ColorModule", "ColorBySpeedModule"):
                mod = d.get(mod_name, {})
                g = mod.get("gradient", {})
                changes += remap_gradient(g.get("minGradient"))
                changes += remap_gradient(g.get("maxGradient"))
            if changes > 0:
                o.save_typetree(d)
                ps_patched += 1
        elif o.type.name == "MonoBehaviour":
            try:
                d = o.read_typetree()
            except Exception:
                continue
            if "_Color" in d and "ColorGradient" in d:
                c = d["_Color"]
                if isinstance(c, dict):
                    d["_Color"] = {"r": 0.90, "g": 0.15, "b": 1.0, "a": float(c.get("a", 1.0))}
                remap_gradient(d.get("ColorGradient"))
                o.save_typetree(d)
                light_patched += 1
    print(f"[*] A3 FX recolor: {len(FX_MAT_PIDS)} mats, {ps_patched} PS, {light_patched} Lights")

    # 9. Graft Galvatron Projectiles, FX, Clips, and Cannon Node Branch (Chapter 9.2 compliant)
    print(f"[*] Grafting Galvatron projectiles & shooting assets from {GAL_BUNDLE}...")
    env_gal = UnityPy.load(str(GAL_BUNDLE))
    sf_gal = [f for f in env_gal.file.files.values() if hasattr(f, "objects")][0]

    # Decode streamed Texture2D (-1597607433780449570: fx_t_flare_hot) from Galvatron .resS so we inline it
    flare_tex_pid = -1597607433780449570
    flare_tex_obj = sf_gal.objects[flare_tex_pid].read()
    inline_tex_images = {
        flare_tex_pid: (flare_tex_obj.image.convert("RGBA"), flare_tex_obj.m_Name),
    }

    root_pids = [
        -145817218210720417,   # projectile_galvatron_ranged GO
        7844017693230829075,   # projectile_galvatron_heavy_bullet GO
        -1727565797039072282,  # fx_p_galvatron_muzzle_flash GO
        -8366828762139599875,  # fx_p_galvatron_muzzle_small GO
        2933117250835710792,   # fx_p_galvatron_blast GO
        2570907183088606735,   # fx_p_galvatron_energy_ball GO
        -7568857660993260739,  # fx_p_galvatron_large_blast GO
        6942792735420182761,   # Galvatron_GS_attackSpecial_02 Clip
        -7209639034736427881,  # galvatron_cin_attackHeavy Clip
        9097260308849304640,   # cannon GO (fight model muzzle hierarchy + Animator)
    ]
    # Prevent climbing m_Father out of cannon into Galvatron's body prefab & omit Galvatron's cannon weapon SMR
    skip_pids = {
        -6589749596925641085,  # Galvatron RightForeArm Transform
        5440676258909896739,   # cha_galvatron_gs_voyager2016_wpns_cannon Transform
        9014400966094672261,   # cha_galvatron_gs_voyager2016_wpns_cannon GameObject
    }

    cloned_pids = clone_closure_into_sf(
        sf_gal,
        sf_um,
        root_pids=root_pids,
        skip_pids=skip_pids,
        inline_tex_images=inline_tex_images,
    )
    print(f"  [Grafted] {len(cloned_pids)} clean objects from Galvatron (with sorted script_types)")

    # Connect cannon under RightForeArm on UltraMagnus_GS_Leader & remove skipped weapon child ref
    cannon_tr_pid = -3496058739791342707
    tr_cannon = sf_um.objects[cannon_tr_pid].read_typetree()
    tr_cannon["m_Father"] = {"m_FileID": 0, "m_PathID": RFARM_TR_PID}
    tr_cannon["m_Children"] = [
        c for c in tr_cannon.get("m_Children", [])
        if int(c.get("m_PathID", 0)) != 5440676258909896739
    ]
    tr_cannon["m_LocalPosition"] = {"x": 0.0, "y": 0.0, "z": 0.0}
    commit_obj_typetree(sf_um.objects[cannon_tr_pid], tr_cannon)

    tr_rfarm = sf_um.objects[RFARM_TR_PID].read_typetree()
    rfarm_children = tr_rfarm.get("m_Children", [])
    if not any(int(c.get("m_PathID", 0)) == cannon_tr_pid for c in rfarm_children):
        rfarm_children.append({"m_FileID": 0, "m_PathID": cannon_tr_pid})
        tr_rfarm["m_Children"] = rfarm_children
        commit_obj_typetree(sf_um.objects[RFARM_TR_PID], tr_rfarm)
    print("  [Attached] cannon muzzle node under RightForeArm")

    # Update PrefabLib on UltraMagnus_GS_Leader with all Galvatron & Shockwave projectiles + FX
    mb_prefablib = sf_um.objects[PREFABLIB_PID].read_typetree()
    plist = mb_prefablib.get("PrefabList", [])
    existing_refs = {
        (int(p.get("Prefab", {}).get("m_FileID", 0)), int(p.get("Prefab", {}).get("m_PathID", 0)))
        for p in plist
    }
    required_prefabs = [
        # Local cloned Galvatron projectiles & FX
        (0, -145817218210720417, 3),   # projectile_galvatron_ranged
        (0, 7844017693230829075, 1),   # projectile_galvatron_heavy_bullet
        (0, -1727565797039072282, 1),  # fx_p_galvatron_muzzle_flash
        (0, -8366828762139599875, 1),  # fx_p_galvatron_muzzle_small
        (0, 2933117250835710792, 1),   # fx_p_galvatron_blast
        (0, 2570907183088606735, 1),   # fx_p_galvatron_energy_ball
        (0, -7568857660993260739, 1),  # fx_p_galvatron_large_blast
        # External character_fx_procedural (fid=1 in UM)
        (1, 7891316674209186940, 1),   # fx_p_galvatron_blast_discharge
        (1, -2863196660049063168, 1),  # fx_p_galvatron_blast_streaks
        (1, 8437262811612867122, 1),   # fx_p_galvatron_charge_up
        (1, 2223755685215444488, 1),   # fx_l_hit_small_galvatron_perceptual
        (1, -603086765132360500, 1),   # fx_l_hit_special_perceptual_purple
        # External character_fx (fid=8 in UM)
        (8, 4246747886251243458, 2),   # fx_r_trail_galvatron
        (8, 5846517154461878008, 1),   # fx_p_hit_large_lite
        (8, -1685458833540413680, 1),  # fx_p_hit_punch_sparks_special
        (8, 8921219544835956990, 1),   # fx_p_shockwave_powerup
        (8, -3334049144611792424, 1),  # fx_p_shockwave_shockwave
        (8, -7386961155930458640, 1),  # fx_p_shockwave_muzzle_flash_beam
        (8, -5229988854594142530, 1),  # fx_p_shockwave_sp_projectile_impact
    ]
    added_pl = 0
    for fid, pid, amt in required_prefabs:
        if (fid, pid) not in existing_refs:
            plist.append({"Prefab": {"m_FileID": fid, "m_PathID": pid}, "Amount": amt})
            existing_refs.add((fid, pid))
            added_pl += 1
    mb_prefablib["PrefabList"] = plist
    commit_obj_typetree(sf_um.objects[PREFABLIB_PID], mb_prefablib)
    print(f"  [Updated] PrefabLib (+{added_pl} entries, total={len(plist)})")

    # 10. Update MoveSet on UltraMagnus_GS_Leader
    print("[*] Rewiring MoveSet actions...")
    mb_moveset = sf_um.objects[MOVESET_PID].read_typetree()
    for m in mb_moveset.get("_moves", []):
        state = m.get("_animStateName")
        if state == "Base.SpecialAttack01":
            m["_name"] = "move_galvatron_special_02"
            m["_asset"] = {"m_FileID": 2, "m_PathID": -5777576223989766411}
            print("  [MoveSet] Base.SpecialAttack01 -> move_galvatron_special_02")
        elif state == "Base.SpecialAttack02":
            m["_name"] = "move_shockwave_special_02"
            m["_asset"] = {"m_FileID": 2, "m_PathID": -124922282930918597}
            print("  [MoveSet] Base.SpecialAttack02 -> move_shockwave_special_02")
        elif state == "Base.HeavyAttack":
            m["_name"] = "move_heavy_galvatron_shoot"
            m["_asset"] = {"m_FileID": 2, "m_PathID": 1182165384359927366}
            print("  [MoveSet] Base.HeavyAttack -> move_heavy_galvatron_shoot")
        elif state == "Base.RangedAttack01":
            m["_name"] = "move_attackRanged_armMount_right_burst_galvatron_01"
            m["_asset"] = {"m_FileID": 2, "m_PathID": 1802417066317421562}
            print("  [MoveSet] Base.RangedAttack01 -> move_attackRanged_armMount_right_burst_galvatron_01")
        elif state == "Base.RangedAttack02":
            m["_name"] = "move_attackRanged_armMount_right_burst_galvatron_02"
            m["_asset"] = {"m_FileID": 2, "m_PathID": 6966870839203297162}
            print("  [MoveSet] Base.RangedAttack02 -> move_attackRanged_armMount_right_burst_galvatron_02")
        elif state == "Base.RangedAttack03":
            m["_name"] = "move_attackRanged_armMount_right_burst_galvatron_03"
            m["_asset"] = {"m_FileID": 2, "m_PathID": 3601832148149049516}
            print("  [MoveSet] Base.RangedAttack03 -> move_attackRanged_armMount_right_burst_galvatron_03")
    commit_obj_typetree(sf_um.objects[MOVESET_PID], mb_moveset)

    # 11. Update Fight AOC
    print("[*] Rewiring Fight AOC animation overrides...")
    anim_names = {}
    if ANIM_BUNDLE.is_file():
        env_anim = UnityPy.load(str(ANIM_BUNDLE))
        for o in env_anim.objects:
            if o.type.name == "AnimationClip":
                anim_names[o.path_id] = o.read_typetree().get("m_Name")

    aoc = sf_um.objects[FIGHT_AOC_PID].read_typetree()
    for pair in aoc.get("m_Clips", []):
        orig_pid = pair.get("m_OriginalClip", {}).get("m_PathID")
        orig_name = anim_names.get(orig_pid, "")
        if orig_name == "char_attackRanged_01":
            pair["m_OverrideClip"] = {"m_FileID": 4, "m_PathID": -7004446808630638293}
            print("  [AOC] char_attackRanged_01 -> armmount_R_attackRanged_burst_01 (fid=4)")
        elif orig_name == "char_attackRanged_02":
            pair["m_OverrideClip"] = {"m_FileID": 4, "m_PathID": 3493707848378459083}
            print("  [AOC] char_attackRanged_02 -> armmount_R_attackRanged_burst_02 (fid=4)")
        elif orig_name == "char_attackRanged_03":
            pair["m_OverrideClip"] = {"m_FileID": 4, "m_PathID": -5190350632979208739}
            print("  [AOC] char_attackRanged_03 -> armmount_R_attackRanged_burst_03 (fid=4)")
        elif orig_name == "char_attackHeavy":
            pair["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": -7209639034736427881}
            print("  [AOC] char_attackHeavy -> galvatron_cin_attackHeavy (local fid=0)")
        elif orig_name == "char_attackSpecial_01":
            pair["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": 6942792735420182761}
            print("  [AOC] char_attackSpecial_01 -> Galvatron_GS_attackSpecial_02 (local fid=0)")
        elif orig_name == "char_attackSpecial_02":
            pair["m_OverrideClip"] = {"m_FileID": 4, "m_PathID": 7142993212488886715}
            print("  [AOC] char_attackSpecial_02 -> shockwave_gs_attackSpecial_02 (fid=4)")
    commit_obj_typetree(sf_um.objects[FIGHT_AOC_PID], aoc)

    # 12. Flush serialized buffer in memory, rebuild exact AssetBundle.m_PreloadTable & m_Container, rename CAB
    print("[*] Rebuilding exact AssetBundle m_PreloadTable & m_Container slices...")
    env = UnityPy.load(io.BytesIO(env.file.save(packer="none")))
    sf_um = [f for f in env.file.files.values() if hasattr(f, "objects")][0]
    ab_obj = next(o for o in sf_um.objects.values() if o.type.name == "AssetBundle")
    ab_tree = ab_obj.read_typetree()

    new_preload = []
    for cname, cinfo in ab_tree.get("m_Container", []):
        rpid = int(cinfo["asset"]["m_PathID"])
        _, closure_pptrs = collect_closure(sf_um, [rpid])
        sorted_pptrs = sorted(closure_pptrs)
        cinfo["preloadIndex"] = len(new_preload)
        cinfo["preloadSize"] = len(sorted_pptrs)
        for fid, pid in sorted_pptrs:
            new_preload.append({"m_FileID": fid, "m_PathID": pid})
        print(f"  [Preload Slice] {cname}: size={len(sorted_pptrs)} (index={cinfo['preloadIndex']})")
    ab_tree["m_PreloadTable"] = new_preload
    commit_obj_typetree(ab_obj, ab_tree)

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

    # 13. Full Chapter 9 Reload Integrity Gate
    print("[*] Running Chapter 9 Reload Integrity Gate on saved bundle...")
    verify_tarn_bundle_integrity(OUT_BUNDLE, anim_names)
    print("[OK] Complete Tarn bundle generation and verification succeeded!")


if __name__ == "__main__":
    main()
