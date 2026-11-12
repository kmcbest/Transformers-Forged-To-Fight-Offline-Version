#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_bugbite_assets.py

Custom composite grafting pipeline for Mercenary Bug Bite (杀人蜂).
Faction: Mercenary (佣兵, PUA: E99F)
Class: Brawler (braw)

1. Base Body & Vehicle Mode:
   - Cloned from Bumblebee (bumblebee_gs_kabam.assetbundle)
2. Combat Animation & Moveset Grafting:
   - S1: Jazz S1 (Jazz_GS_attackSpecial_01 / move_jazz_special_01)
   - S2: Waspinator S2 (waspinator_bw_attackSpecial_02 / move_bugbite_special_02)
   - S3: Cliffjumper S3 (cliffjumper_gs_attackSpecial_03 / native Beetle stage)
   - L1: Tantrum L1 (brute_tantrum_attackLight_01_jab / move_tantrum_attack_light_01)
   - L2: Tantrum L2 (brute_tantrum_attackLight_02_jab / move_tantrum_attack_light_02)
   - L3: Tantrum L3 (brute_tantrum_attackLight_03_frontkick / move_tantrum_attack_light_03)
   - L4: Tantrum L4 (brute_tantrum_attackLight_04_uppcut / move_tantrum_attack_light_04)
   - M1: Movie Ironhide M1 (brawler_normal_attackMedium_02_shouldercharge / move_brawler_attack_medium_02)
   - M2: Megatronus M2 (Brute02_normal_attackMedium_02_L_push / move_megatronus_attack_medium_02)
   - Other moves: Preserved from Bumblebee
3. Visuals & Recolor:
   - Pearl white armor with silver metallic shading
   - Crimson / Ruby red eye optics (glowing emissive)
   - Deep violet / tinted windows
   - Mercenary insignia on chest
4. Deep CAB Isolation:
   - CAB-bugbite2026kabam0001122334455
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import copy
import json
import os
import shutil
import sys
from collections import deque
from pathlib import Path
from PIL import Image
from UnityPy.files import ObjectReader
from UnityPy.streams import EndianBinaryReader

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

try:
    import UnityPy
except ImportError:
    print("Error: UnityPy is required. Install it using: pip install UnityPy lz4 pillow numpy")
    sys.exit(1)

BUGBITE_S2_PID = -8888888888888888884


def replace_str_in_tree(tree_obj, old_s, new_s):
    if isinstance(tree_obj, dict):
        for k, v in list(tree_obj.items()):
            if isinstance(v, str):
                if old_s in v:
                    tree_obj[k] = v.replace(old_s, new_s)
            elif isinstance(v, tuple):
                tree_obj[k] = replace_str_in_tree(v, old_s, new_s)
            else:
                replace_str_in_tree(v, old_s, new_s)
        return tree_obj
    elif isinstance(tree_obj, list):
        for idx, item in enumerate(tree_obj):
            if isinstance(item, str):
                if old_s in item:
                    tree_obj[idx] = item.replace(old_s, new_s)
            elif isinstance(item, tuple):
                tree_obj[idx] = replace_str_in_tree(item, old_s, new_s)
            else:
                replace_str_in_tree(item, old_s, new_s)
        return tree_obj
    elif isinstance(tree_obj, tuple):
        out = []
        changed = False
        for item in tree_obj:
            if isinstance(item, str):
                if old_s in item:
                    out.append(item.replace(old_s, new_s))
                    changed = True
                else:
                    out.append(item)
            elif isinstance(item, tuple):
                new_item = replace_str_in_tree(item, old_s, new_s)
                if new_item is not item:
                    changed = True
                out.append(new_item)
            else:
                replace_str_in_tree(item, old_s, new_s)
                out.append(item)
        return tuple(out) if changed else tree_obj
    return tree_obj


def commit_obj_typetree(obj, tree):
    """Persist typetree into obj.data AND update obj.reader/byte_start/byte_size
    so subsequent in-memory read_typetree()/collect_closure() calls observe mutations."""
    data = obj.save_typetree(tree)
    obj.reader = EndianBinaryReader(data, endian=obj.reader.endian)
    obj.byte_start = 0
    obj.byte_size = len(data)
    return data


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


def collect_closure(sf, root_pids):
    """Collect reachable local PIDs and all non-null (m_FileID, m_PathID) PPtrs from root_pids."""
    visited_local = set()
    all_pptrs = set()
    queue = deque()

    for pid in root_pids:
        if pid and pid in sf.objects and pid not in visited_local:
            visited_local.add(pid)
            all_pptrs.add((0, pid))
            queue.append(pid)

    while queue:
        pid = queue.popleft()
        obj = sf.objects[pid]
        tree = obj.read_typetree()
        for pptr in iter_pptrs_in_tree(tree):
            fid = pptr.get("m_FileID", 0)
            target_pid = pptr.get("m_PathID", 0)
            if not target_pid:
                continue
            all_pptrs.add((fid, target_pid))
            if fid == 0 and target_pid not in visited_local:
                if target_pid not in sf.objects:
                    raise RuntimeError(
                        f"Dangling local PPtr in closure from {pid} ({obj.type.name}): m_PathID={target_pid}"
                    )
                visited_local.add(target_pid)
                queue.append(target_pid)

    return visited_local, all_pptrs


def _build_ext_file_id_map(src_sf, dst_sf):
    dst_by_path = {}
    for idx, ext in enumerate(dst_sf.externals, start=1):
        dst_by_path[ext.path] = idx

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


def clone_closure_into_sf(src_sf, dst_sf, root_pids):
    """Clone reachable local objects (excluding existing MonoScripts) from src_sf into dst_sf,
    safely remapping externals, registering missing SerializedTypes/MonoScripts, and sorting script_types."""
    local_pids, _ = collect_closure(src_sf, root_pids)
    ext_map = _build_ext_file_id_map(src_sf, dst_sf)

    # Snapshot existing script_types key for every MonoBehaviour SerializedType before mutating/sorting
    existing_tp_script_keys = {}
    for idx, tp in enumerate(dst_sf.types):
        if tp.script_type_index >= 0:
            sref = dst_sf.script_types[tp.script_type_index]
            existing_tp_script_keys[idx] = (
                sref.local_serialized_file_index,
                sref.local_identifier_in_file,
            )

    existing_script_keys = {
        (sref.local_serialized_file_index, sref.local_identifier_in_file)
        for sref in dst_sf.script_types
    }

    # First ensure all missing MonoScripts and SerializedTypes exist in dst_sf
    pending_new_tp_keys = {}
    src_obj_to_dst_type_id = {}

    for pid in sorted(local_pids):
        src_obj = src_sf.objects[pid]
        src_tp = src_obj.serialized_type
        if src_tp is None:
            raise RuntimeError(f"Source object {pid} ({src_obj.type.name}) has serialized_type=None")

        if src_tp.class_id == 115:
            # Shared MonoScript: skip if already present in dst_sf
            if pid in dst_sf.objects:
                if dst_sf.objects[pid].class_id != 115:
                    raise RuntimeError(f"MonoScript PID collision at {pid}: dst class_id={dst_sf.objects[pid].class_id}")
                continue
        elif pid in dst_sf.objects:
            raise RuntimeError(f"Non-MonoScript PID collision at {pid}: src={src_obj.type.name}, dst={dst_sf.objects[pid].type.name}")

        remapped_script_key = None
        if src_tp.class_id == 114:
            if src_tp.script_type_index < 0:
                raise RuntimeError(f"MonoBehaviour {pid} has script_type_index={src_tp.script_type_index}")
            src_sref = src_sf.script_types[src_tp.script_type_index]
            orig_fid = src_sref.local_serialized_file_index
            if orig_fid == 0:
                remapped_fid = 0
            else:
                if orig_fid not in ext_map:
                    raise RuntimeError(f"Missing external mapping for MonoScript FileID {orig_fid}")
                remapped_fid = ext_map[orig_fid]
            remapped_script_key = (remapped_fid, src_sref.local_identifier_in_file)

            if remapped_script_key not in existing_script_keys:
                new_sref = copy.copy(src_sref)
                new_sref.local_serialized_file_index = remapped_script_key[0]
                new_sref.local_identifier_in_file = remapped_script_key[1]
                dst_sf.script_types.append(new_sref)
                existing_script_keys.add(remapped_script_key)

        dst_type_id = _find_matching_dst_type_id(dst_sf, src_tp, remapped_script_key)
        if dst_type_id is None:
            new_tp = copy.copy(src_tp)
            dst_type_id = len(dst_sf.types)
            dst_sf.types.append(new_tp)
            if remapped_script_key is not None:
                pending_new_tp_keys[dst_type_id] = remapped_script_key
                existing_tp_script_keys[dst_type_id] = remapped_script_key
        elif remapped_script_key is not None:
            existing_tp_script_keys[dst_type_id] = remapped_script_key

        src_obj_to_dst_type_id[pid] = dst_type_id

    # Sort dst_sf.script_types ascending and remap ALL tp.script_type_index across dst_sf.types
    dst_sf.script_types.sort(key=lambda s: (s.local_serialized_file_index, s.local_identifier_in_file))
    script_key_to_idx = {
        (sref.local_serialized_file_index, sref.local_identifier_in_file): idx
        for idx, sref in enumerate(dst_sf.script_types)
    }
    for tp_idx, key in existing_tp_script_keys.items():
        dst_sf.types[tp_idx].script_type_index = script_key_to_idx[key]

    # Clone objects into dst_sf
    cloned_pids = []
    for pid in sorted(local_pids):
        if pid in dst_sf.objects:
            continue  # existing MonoScript kept as-is
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

        # Remap any external PPtrs in the cloned object's typetree
        tree = src_obj.read_typetree()
        changed = False
        for pptr in iter_pptrs_in_tree(tree):
            fid = pptr.get("m_FileID", 0)
            target_pid = pptr.get("m_PathID", 0)
            if fid > 0 and target_pid != 0:
                if fid not in ext_map:
                    src_ext_path = (
                        src_sf.externals[fid - 1].path
                        if 1 <= fid <= len(src_sf.externals)
                        else "<out-of-range>"
                    )
                    raise RuntimeError(
                        f"Object {pid} ({src_obj.type.name}) references unmapped external FileID={fid} ({src_ext_path})"
                    )
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

    return cloned_pids


def verify_bugbite_bundle_integrity(target_bundle, new_cab, forbidden_pids):
    """Strict Reload Integrity Gate: validate rebuilt bundle on disk with UnityPy."""
    env = UnityPy.load(str(target_bundle))
    bf = list(env.files.values())[0]
    sf = list(env.assets)[0]

    res_name = f"{new_cab}.resource"
    assert res_name in bf.files, f"Missing resource stream {res_name} in bundle"
    res_bytes = bytes(bf.files[res_name].bytes)

    # 1. Verify forbidden dead BB objects were removed
    remaining_forbidden = [pid for pid in forbidden_pids if pid in sf.objects]
    assert not remaining_forbidden, f"Forbidden dead BB objects still present: {remaining_forbidden}"

    # 2. Verify required CJ-cloned & BugBite core objects exist
    required_pids = [
        -4178259269510828426,  # main GO
        5495859601297396382,   # _lw GO
        1157624665093363023,   # PlayerReferences
        -3364085224588132041,  # MatineeAnimatorOverrideController
        -135521353996395750,   # CharacterAudio
        4786041819736037741,   # Fight AOC
        -5475676132653162908,  # Car AOC
        -513981948225030119,   # Cloned CJ Stage GO -> TFormStage_BugBite_GS_Special03
        -3164215817585307476,  # Cloned CJ Matinee GO -> Matinee_BugBite_GS_Special03
        4051884971414969356,   # Cloned CJ TFormMatineeStage
        -8867447285746891126,  # Cloned CJ MatineeData
        -4808014442274116898,  # Cloned CJ Audio root GO -> bugbite_gs_special_3
        8019343707475621852,   # Cloned CJ Audio child GO -> bugbite_gs_special_3
        1281847170586998338,   # Cloned CJ Audio RandomComponent
        5829207288378332728,   # Cloned CJ AudioClip -> bugbite_gs_special_3
        992031, 992032, 992033,
    ]
    missing_req = [pid for pid in required_pids if pid not in sf.objects]
    assert not missing_req, f"Missing required objects in reloaded bundle: {missing_req}"

    # 3. Verify script_types ordering and MonoBehaviour type consistency
    skeys = [(s.local_serialized_file_index, s.local_identifier_in_file) for s in sf.script_types]
    assert skeys == sorted(skeys), "sf.script_types is not sorted ascending!"
    for tp in sf.types:
        if tp.script_type_index >= 0:
            assert tp.script_type_index < len(sf.script_types), f"Out of range script_type_index {tp.script_type_index}"
            sref = sf.script_types[tp.script_type_index]
            if sref.local_serialized_file_index == 0:
                assert sref.local_identifier_in_file in sf.objects, (
                    f"Missing local MonoScript {sref.local_identifier_in_file} referenced by sf.types"
                )

    # 4. Read EVERY object typetree & check all PPtrs, AudioClips, and forbidden strings
    expected_source = f"archive:/{new_cab}/{new_cab}.resource"
    asset_bundle_obj = None
    for pid, obj in sf.objects.items():
        tree = obj.read_typetree()
        if obj.type.name == "AssetBundle":
            asset_bundle_obj = tree
        if obj.type.name == "MonoBehaviour":
            assert obj.serialized_type is sf.types[obj.type_id], f"Type mismatch on MonoBehaviour {pid}"
            m_script = tree.get("m_Script", {})
            if m_script.get("m_FileID", 0) == 0:
                spid = m_script.get("m_PathID", 0)
                sref = sf.script_types[obj.serialized_type.script_type_index]
                assert (sref.local_serialized_file_index, sref.local_identifier_in_file) == (0, spid), (
                    f"MonoBehaviour {pid} script mismatch: type={(sref.local_serialized_file_index, sref.local_identifier_in_file)} vs m_Script=(0, {spid})"
                )
        for pptr in iter_pptrs_in_tree(tree):
            fid = pptr.get("m_FileID", 0)
            target_pid = pptr.get("m_PathID", 0)
            if not target_pid:
                continue
            if fid == 0:
                assert target_pid in sf.objects, f"Dangling local PPtr in {pid} ({obj.type.name}): {target_pid}"
            else:
                assert 1 <= fid <= len(sf.externals), f"Out-of-range external m_FileID={fid} in {pid} ({obj.type.name})"
        if obj.type.name == "AudioClip":
            res_info = tree.get("m_Resource", {})
            src = res_info.get("m_Source", "")
            off = res_info.get("m_Offset", 0)
            sz = res_info.get("m_Size", 0)
            if sz > 0:
                assert src == expected_source, f"AudioClip {pid} ({tree.get('m_Name')}) bad m_Source={src}"
                assert off + sz <= len(res_bytes), (
                    f"AudioClip {pid} out of bounds: {off}+{sz} > {len(res_bytes)}"
                )

    # 5. Targeted SP3 clean-state checks (no BB SP3 or raw CJ/Ratchet remnants)
    forbidden_sp3_strs = [
        "bumblebee_gs_attackSpecial_03",
        "cliffjumper_gs_attackSpecial_03",
        "bumblebee_gs_special_3",
        "ratchet_special_3",
        "Cliffjumper_GS_Kabam",
        "f48ebf5cf07fc99194be43e86f34ac74",
    ]
    check_pids = [
        1157624665093363023,
        -3364085224588132041,
        -135521353996395750,
        -513981948225030119,
        -3164215817585307476,
        4051884971414969356,
        -8867447285746891126,
        -4808014442274116898,
        8019343707475621852,
        1281847170586998338,
        5829207288378332728,
        992031, 992032, 992033,
    ]
    for cpid in check_pids:
        blob = json.dumps(sf.objects[cpid].read_typetree(), ensure_ascii=False)
        for bad in forbidden_sp3_strs:
            assert bad not in blob, f"Forbidden string {bad!r} found in object {cpid}"

    # Verify MatineeAOC SP3 slots (_overrideControllerList MonoBehaviour)
    maoc = sf.objects[-3364085224588132041].read_typetree()
    maoc_map = {e["StateHash"]: e["OverrideClipName"] for e in maoc.get("_overrideControllerList", [])}
    assert maoc_map.get(-1919714467) == "bugbite_gs_attackSpecial_03", (
        f"MatineeAOC SP3 fight slot wrong: {maoc_map.get(-1919714467)}"
    )
    assert maoc_map.get(966217297) == "bugbite_gs_attackSpecial_03_hitReaction", (
        f"MatineeAOC SP3 hit slot wrong: {maoc_map.get(966217297)}"
    )

    # Verify Fight AOC & Car AOC SP3 clip bindings
    fight_aoc = sf.objects[4786041819736037741].read_typetree()
    fclips = fight_aoc.get("m_Clips", [])
    assert fclips[31]["m_OverrideClip"] == {"m_FileID": 0, "m_PathID": 992031}, f"FightAOC slot 31 wrong: {fclips[31]}"
    assert fclips[32]["m_OverrideClip"] == {"m_FileID": 0, "m_PathID": 992032}, f"FightAOC slot 32 wrong: {fclips[32]}"
    car_aoc = sf.objects[-5475676132653162908].read_typetree()
    cclips = car_aoc.get("m_Clips", [])
    assert cclips[63]["m_OverrideClip"] == {"m_FileID": 0, "m_PathID": 992033}, f"CarAOC slot 63 wrong: {cclips[63]}"

    # Verify MatineeData tracks & teoacn
    md_tree = sf.objects[-8867447285746891126].read_typetree()
    mtracks = json.loads(md_tree["jSONData"])["TRACKS"]
    assert mtracks["track_5"]["enp"] == "rightgun", f"track_5 enp wrong: {mtracks['track_5']}"
    assert mtracks["track_8"]["enp"] == "transformed", f"track_8 enp wrong: {mtracks['track_8']}"
    assert mtracks["track_1_econtainer_0"]["e_0"]["ad"]["teoacn"] == "bugbite_gs_attackSpecial_03"
    assert mtracks["track_2_econtainer_0"]["e_0"]["ad"]["teoacn"] == "bugbite_gs_attackSpecial_03_hitReaction"
    assert mtracks["track_6_econtainer_0"]["e_0"]["ad"]["teoacn"] == "bugbite_gs_attackSpecial_03_transformed"

    # Verify PlayerReferences SpecialStagePrefab
    pref = sf.objects[1157624665093363023].read_typetree()
    assert pref["SpecialStagePrefab"]["m_PathID"] == -513981948225030119, "PlayerReferences.SpecialStagePrefab wrong"

    # Verify CharacterAudio SP3 wiring
    caudio = sf.objects[-135521353996395750].read_typetree()
    ev_map = {e["_genEvent"]: e["_override"] for e in caudio.get("_events", [])}
    assert ev_map.get("gen_special_3") == "bugbite_gs_special_3", f"CharacterAudio gen_special_3={ev_map.get('gen_special_3')}"
    spec_pids = [x["m_PathID"] for x in caudio.get("_specialCharacterAudio", [])]
    assert 1281847170586998338 in spec_pids and -3561701419133919622 not in spec_pids, (
        f"CharacterAudio _specialCharacterAudio wrong: {spec_pids}"
    )

    # 6. Verify m_PreloadTable slices exactly match BFS closures of container roots
    assert asset_bundle_obj is not None, "Missing AssetBundle object"
    preload_list = [(p["m_FileID"], p["m_PathID"]) for p in asset_bundle_obj["m_PreloadTable"]]
    for cname, cinfo in asset_bundle_obj["m_Container"]:
        root_pid = cinfo["asset"]["m_PathID"]
        idx = cinfo["preloadIndex"]
        sz = cinfo["preloadSize"]
        slice_set = set(preload_list[idx : idx + sz])
        _, expected_set = collect_closure(sf, [root_pid])
        missing = expected_set - slice_set
        extra = slice_set - expected_set
        assert not missing and not extra, (
            f"Preload mismatch for {cname}: missing={len(missing)} extra={len(extra)}"
        )

    print(
        f"[+] Reload Integrity Gate PASSED! objects={len(sf.objects)}, "
        f"types={len(sf.types)}, script_types={len(sf.script_types)}, "
        f"preload={len(preload_list)}, resource_bytes={len(res_bytes)}"
    )


def patch_bugbite_move_s2():
    """Create dedicated move_bugbite_special_02 inside moves.assetbundle."""
    moves_path = Path("assets_redeco/moves.assetbundle")
    if not moves_path.exists():
        moves_path = Path("assets_netflix/moves.assetbundle")

    print(f"[*] Patching moves bundle from {moves_path}...")
    env = UnityPy.load(str(moves_path))
    bf = list(env.files.values())[0]
    moves_asset = list(env.assets)[0]

    wasp_reader = None
    ab_obj = None

    for obj in env.objects:
        if obj.path_id == 1005920638777440556:
            wasp_reader = obj
        elif obj.type.name == "AssetBundle":
            ab_obj = obj

    assert wasp_reader is not None, "Failed to find move_waspinator_special_02!"
    assert ab_obj is not None, "Failed to find AssetBundle object in moves!"

    # Clone move_waspinator_special_02 to move_bugbite_special_02
    s2_move = copy.deepcopy(wasp_reader.read_typetree())
    s2_move["m_Name"] = "move_bugbite_special_02"
    s2_data = json.loads(s2_move["m_Script"])

    move_def = s2_data.get("moves", {})
    move_def["id"] = "move_bugbite_special_02"
    move_def["m_Name"] = "move_bugbite_special_02"

    events = []
    for ev in move_def.get("events", []):
        ev_type = ev.get("type", "")
        
        # 1. Drop wings prop animation and charge up particle
        if ev_type == "PlayPropAnimatorStateMoveEvent" and ev.get("pn") == "wings":
            print("  - Dropped wings PlayPropAnimatorStateMoveEvent")
            continue
        if ev_type == "ParticleMoveEvent" and "charge_up" in ev.get("pn", ""):
            print("  - Dropped charge_up ParticleMoveEvent")
            continue
            
        # 2. Retarget gunright to rightgun
        ev_str = json.dumps(ev)
        if "gunright" in ev_str:
            ev_str = ev_str.replace("gunright", "rightgun")
            ev = json.loads(ev_str)
            print(f"  - Replaced gunright with rightgun in {ev_type}")
            
        # 3. Specific adjustments
        if ev_type == "PropMoveEvent" and ev.get("p") in ("gunright", "rightgun"):
            ev["p"] = "rightgun"
            ev["d"] = 35
            
        if ev_type == "ParticleMoveEvent" and "muzzle_flash" in ev.get("pn", ""):
            ev["pn"] = "fx_p_optimus_muzzle_flash"
            ev["dn"] = "muzzle_flash"
            ev["ref"]["r"] = "character_model/Reference/Hips/Spine/Spine1/RightShoulder/RightArm/RightArmRoll/RightForeArm/RightForeArmRoll/RightHand/rightgun/Reference/COG/FX"
            ev["po"] = {"o": {"y": 0, "z": 0, "x": 0}, "s": 1}
            print("  - Configured fx_p_optimus_muzzle_flash for rightgun")
            
        if ev_type == "LightMoveEvent" and "muzzle_light" in ev.get("dn", ""):
            ev["ref"]["r"] = "character_model/Reference/Hips/Spine/Spine1/RightShoulder/RightArm/RightArmRoll/RightForeArm/RightForeArmRoll/RightHand/rightgun/Reference/COG/FX"
            
        if ev_type == "ProjectileMoveEvent":
            print(f"  - Retargeting projectile {ev.get('pn')} -> projectile_special_bullet")
            ev["pn"] = "projectile_special_bullet"
            ev["dn"] = "projectile_special_bullet"
            ev["po"] = {"o": {"y": 4.61, "z": 6.5, "x": 0}, "s": 1}
            ev["oe"] = "explode_special"
            ev["spd"] = 120
            ev["hd"] = {
                "db": True, "fd": False, "al": 32,
                "hr": "HitReactionHeavyBack", "hs": 21, "kb": 25,
                "at": 2, "u": False, "ft": 0, "dam": 0.6,
                "bft": 0, "bhs": 12, "bkb": 15, "idx": 100, "m": 0.6
            }
            
        # 4. Set move name in event
        ev["mn"] = "move_bugbite_special_02"
        events.append(ev)

    move_def["events"] = events
    s2_data["moves"] = move_def
    s2_move["m_Script"] = json.dumps(s2_data)

    # Register new object in moves bundle
    s2_reader = copy.copy(wasp_reader)
    s2_reader.path_id = BUGBITE_S2_PID
    moves_asset.objects[BUGBITE_S2_PID] = s2_reader
    s2_reader.save_typetree(s2_move)

    # Update AssetBundle container
    ab_tree = ab_obj.read_typetree()
    container = [c for c in ab_tree.get("m_Container", []) if "move_bugbite_special_02" not in c[0]]
    container.append([
        "assets/bundles/movedata/move_bugbite_special_02.txt",
        {"preloadIndex": 0, "preloadSize": 0, "asset": {"m_FileID": 0, "m_PathID": BUGBITE_S2_PID}}
    ])
    ab_tree["m_Container"] = container
    ab_obj.save_typetree(ab_tree)

    # Save to assets_redeco/moves.assetbundle
    out_moves = Path("assets_redeco/moves.assetbundle")
    out_moves.write_bytes(bf.save(packer="lz4"))
    print(f"[+] Saved {out_moves} ({out_moves.stat().st_size:,} bytes)")

    # Verify
    check_env = UnityPy.load(str(out_moves))
    total_count = len(check_env.objects)
    assert total_count >= 945, f"Moves count {total_count} < 945!"
    print(f"[+] Successfully patched moves.assetbundle with move_bugbite_special_02! (Total {total_count} objects)")


def generate_bugbite_assets(output_dir: str = "assets_redeco") -> None:
    # 0. Ensure moves.assetbundle contains move_bugbite_special_02
    patch_bugbite_move_s2()

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    extracted = Path("extracted_apk/assets/assetpack")

    def load_bundle(rel_path: str) -> bytes:
        p = extracted / rel_path
        if p.is_file():
            return p.read_bytes()
        raise FileNotFoundError(f"Cannot find {rel_path} in extracted_apk!")

    print("[*] Loading component assetbundles...")
    bb_bytes = load_bundle("bumblebee_gs_kabam_odr/bumblebee_gs_kabam.assetbundle")
    jazz_bytes = load_bundle("jazz_gs_twm05_odr/jazz_gs_twm05.assetbundle")
    wasp_bytes = load_bundle("waspinator_gs_deluxe_odr/waspinator_gs_deluxe.assetbundle")
    cj_bytes = load_bundle("cliffjumper_gs_kabam_odr/cliffjumper_gs_kabam.assetbundle")
    tan_bytes = load_bundle("tantrum_gs_kabam_odr/tantrum_gs_kabam.assetbundle")
    megatro_bytes = load_bundle("megatronus_gs_kabam_odr/megatronus_gs_kabam.assetbundle")
    anim_proc_bytes = load_bundle("characters_procedural_odr/character_anim_procedural.assetbundle")

    print("[*] Parsing source bundles...")
    bb_env = UnityPy.load(bb_bytes)
    jazz_env = UnityPy.load(jazz_bytes)
    wasp_env = UnityPy.load(wasp_bytes)
    cj_env = UnityPy.load(cj_bytes)
    tan_env = UnityPy.load(tan_bytes)
    meg_env = UnityPy.load(megatro_bytes)
    anim_proc_env = UnityPy.load(anim_proc_bytes)

    # 1. Extract required AnimationClips
    print("[*] Extracting external animation clips...")

    # S1: Jazz S1 (-1177978727659732769)
    clip_s1 = None
    for obj in jazz_env.objects:
        if obj.path_id == -1177978727659732769 and obj.type.name == "AnimationClip":
            clip_s1 = obj.read_typetree()
            clip_s1["m_Name"] = "bugbite_gs_attackSpecial_01"
            break
    assert clip_s1 is not None, "Failed to find Jazz S1 clip!"

    # S2: Waspinator S2 (-8086663017110078275)
    clip_s2 = None
    for obj in wasp_env.objects:
        if obj.path_id == -8086663017110078275 and obj.type.name == "AnimationClip":
            clip_s2 = obj.read_typetree()
            clip_s2["m_Name"] = "bugbite_gs_attackSpecial_02"
            break
    assert clip_s2 is not None, "Failed to find Waspinator S2 clip!"

    # L1: Tantrum L1 (4273516124016290571)
    clip_l1 = None
    for obj in tan_env.objects:
        if obj.path_id == 4273516124016290571 and obj.type.name == "AnimationClip":
            clip_l1 = obj.read_typetree()
            clip_l1["m_Name"] = "bugbite_gs_attackLight_01"
            break
    assert clip_l1 is not None, "Failed to find Tantrum L1 clip!"

    # L2: Tantrum L2 (4342173990092517894)
    clip_l2 = None
    for obj in tan_env.objects:
        if obj.path_id == 4342173990092517894 and obj.type.name == "AnimationClip":
            clip_l2 = obj.read_typetree()
            clip_l2["m_Name"] = "bugbite_gs_attackLight_02"
            break
    assert clip_l2 is not None, "Failed to find Tantrum L2 clip!"

    # L3: Tantrum L3 (1038656054960397805)
    clip_l3 = None
    for obj in tan_env.objects:
        if obj.path_id == 1038656054960397805 and obj.type.name == "AnimationClip":
            clip_l3 = obj.read_typetree()
            clip_l3["m_Name"] = "bugbite_gs_attackLight_03"
            break
    assert clip_l3 is not None, "Failed to find Tantrum L3 clip!"

    # L4: Tantrum L4 (-1232275642304231213)
    clip_l4 = None
    for obj in tan_env.objects:
        if obj.path_id == -1232275642304231213 and obj.type.name == "AnimationClip":
            clip_l4 = obj.read_typetree()
            clip_l4["m_Name"] = "bugbite_gs_attackLight_04"
            break
    assert clip_l4 is not None, "Failed to find Tantrum L4 clip!"

    # M1: Movie Ironhide M1 (-7925637137891657471)
    clip_m1 = None
    for obj in anim_proc_env.objects:
        if obj.path_id == -7925637137891657471 and obj.type.name == "AnimationClip":
            clip_m1 = obj.read_typetree()
            clip_m1["m_Name"] = "bugbite_gs_attackMedium_01"
            break
    assert clip_m1 is not None, "Failed to find Movie Ironhide M1 clip!"

    # M2: Megatronus M2 (-3651284692217483506)
    clip_m2 = None
    for obj in meg_env.objects:
        if obj.path_id == -3651284692217483506 and obj.type.name == "AnimationClip":
            clip_m2 = obj.read_typetree()
            clip_m2["m_Name"] = "bugbite_gs_attackMedium_02"
            break
    assert clip_m2 is not None, "Failed to find Megatronus M2 clip!"

    # S3: Cliffjumper S3 (Fight, HitReaction, Transformed car)
    clip_s3_fight = None
    clip_s3_hit = None
    clip_s3_car = None

    for obj in cj_env.objects:
        if obj.type.name == "AnimationClip":
            t = obj.read_typetree()
            name = t.get("m_Name", "")
            if name == "cliffjumper_gs_attackSpecial_03":
                clip_s3_fight = t
                clip_s3_fight["m_Name"] = "bugbite_gs_attackSpecial_03"
            elif name == "cliffjumper_gs_attackSpecial_03_hitReaction":
                clip_s3_hit = t
                clip_s3_hit["m_Name"] = "bugbite_gs_attackSpecial_03_hitReaction"
            elif name == "cliffjumper_gs_attackSpecial_03_transformed":
                clip_s3_car = t
                clip_s3_car["m_Name"] = "bugbite_gs_attackSpecial_03_transformed"

    assert clip_s3_fight is not None, "Failed to find Cliffjumper S3 fight clip!"
    assert clip_s3_hit is not None, "Failed to find Cliffjumper S3 hitReaction clip!"
    assert clip_s3_car is not None, "Failed to find Cliffjumper S3 transformed car clip!"

    print("[+] Successfully extracted all external clips (Jazz S1, Waspinator S2, Tantrum L1..L4, Ironhide M1, Megatronus M2, Cliffjumper S3)!")

    # 2. Prepare Bumblebee base asset
    print("[*] Grafting Bug Bite into Bumblebee physical rig...")
    bf = list(bb_env.files.values())[0]
    bb_asset = list(bb_env.assets)[0]

    old_cab = "CAB-f48eb1f9fe83a540c77c339585eedaa4"
    for subfname in bf.files.keys():
        if subfname.startswith("CAB-") and not subfname.endswith((".resS", ".resource")):
            old_cab = subfname
            break

    new_cab = "CAB-bugbite2026kabam0001122334455"
    print(f"[*] Remapping CAB: {old_cab} -> {new_cab}")

    PID_S1 = 992001
    PID_S2 = 992002
    PID_L1 = 992011
    PID_L2 = 992012
    PID_L3 = 992013
    PID_L4 = 992014
    PID_M1 = 992021
    PID_M2 = 992022
    PID_S3_FIGHT = 992031
    PID_S3_HIT = 992032
    PID_S3_CAR = 992033

    new_clips = [
        (PID_S1, clip_s1),
        (PID_S2, clip_s2),
        (PID_L1, clip_l1),
        (PID_L2, clip_l2),
        (PID_L3, clip_l3),
        (PID_L4, clip_l4),
        (PID_M1, clip_m1),
        (PID_M2, clip_m2),
        (PID_S3_FIGHT, clip_s3_fight),
        (PID_S3_HIT, clip_s3_hit),
        (PID_S3_CAR, clip_s3_car),
    ]

    template_clip = [o for o in bb_asset.objects.values() if o.type.name == "AnimationClip"][0]

    for pid, ctree in new_clips:
        new_obj = copy.copy(template_clip)
        new_obj.path_id = pid
        replace_str_in_tree(ctree, old_cab, new_cab)
        commit_obj_typetree(new_obj, ctree)
        bb_asset.objects[pid] = new_obj
    print(f"[+] Injected {len(new_clips)} new self-contained AnimationClips into Bug Bite asset!")

    # Load custom recolored textures
    user_main_path = out_dir / "cha_bugbite_gs_main_a.png"
    user_misc_path = out_dir / "cha_bugbite_gs_tform_misc_a.png"
    user_wpns_path = out_dir / "cha_bugbite_gs_wpns_a.png"
    user_raoe_path = out_dir / "cha_bugbite_gs_raoe.png"

    # Snapshot old Bumblebee SP3 Stage & Audio closures before rewiring
    BB_SP3_STAGE_ROOT = 3762158464405546467
    BB_SP3_AUDIO_ROOT = -428821236856854288
    BB_SP3_OLD_CLIP_PIDS = {-9071274386392300993, 3809667128409547372, 1332696529797843162}
    old_bb_sp3_local_pids, _ = collect_closure(bb_asset, [BB_SP3_STAGE_ROOT, BB_SP3_AUDIO_ROOT])
    old_bb_sp3_candidates = old_bb_sp3_local_pids | BB_SP3_OLD_CLIP_PIDS

    # Clone Cliffjumper SP3 Stage & Audio closures and append .resource audio stream
    cj_bf = list(cj_env.files.values())[0]
    cj_asset = list(cj_env.assets)[0]

    cj_res_key = [k for k in cj_bf.files.keys() if k.endswith(".resource")][0]
    cj_res_bytes = bytes(cj_bf.files[cj_res_key].bytes)
    cj_audio_clip_tree = cj_asset.objects[5829207288378332728].read_typetree()
    cj_audio_off = cj_audio_clip_tree["m_Resource"]["m_Offset"]
    cj_audio_size = cj_audio_clip_tree["m_Resource"]["m_Size"]
    assert cj_audio_size > 0 and cj_audio_off + cj_audio_size <= len(cj_res_bytes), (
        f"Invalid CJ AudioClip resource slice: off={cj_audio_off}, size={cj_audio_size}, total={len(cj_res_bytes)}"
    )
    cj_audio_slice = cj_res_bytes[cj_audio_off : cj_audio_off + cj_audio_size]

    bb_res_key = [k for k in bf.files.keys() if k.endswith(".resource")][0]
    orig_bb_res_subf = bf.files[bb_res_key]
    orig_bb_res_bytes = bytes(orig_bb_res_subf.bytes)
    appended_audio_off = len(orig_bb_res_bytes)
    combined_res_bytes = orig_bb_res_bytes + cj_audio_slice
    new_bb_res_reader = EndianBinaryReader(combined_res_bytes, endian=orig_bb_res_subf.endian)
    new_bb_res_reader.flags = orig_bb_res_subf.flags
    new_bb_res_reader.name = bb_res_key
    bf.files[bb_res_key] = new_bb_res_reader
    print(
        f"[+] Appended Cliffjumper SP3 audio stream ({cj_audio_size} bytes) at offset {appended_audio_off} "
        f"(total resource={len(combined_res_bytes)} bytes)"
    )

    CJ_SP3_STAGE_ROOT = -513981948225030119
    CJ_SP3_AUDIO_ROOT = -4808014442274116898
    cloned_pids = clone_closure_into_sf(cj_asset, bb_asset, [CJ_SP3_STAGE_ROOT, CJ_SP3_AUDIO_ROOT])
    print(f"[+] Cloned {len(cloned_pids)} objects from Cliffjumper SP3 Stage & Audio closures into Bug Bite!")

    # Rewire explicit objects in Bug Bite asset
    # 1. Fight AOC: override_Bumblebee_GS_Kabam_fight (PathID=4786041819736037741)
    fight_aoc_obj = bb_asset.objects[4786041819736037741]
    tree = fight_aoc_obj.read_typetree()
    clips = tree.get("m_Clips", [])
    clips[2]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_L1}
    clips[3]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_L2}
    clips[4]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_S1}
    clips[5]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_S2}
    clips[31]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_S3_FIGHT}
    clips[32]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_S3_HIT}
    clips[41]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_L3}
    clips[42]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_M1}
    clips[43]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_L4}
    clips[44]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_M2}
    tree["m_Clips"] = clips
    replace_str_in_tree(tree, old_cab, new_cab)
    commit_obj_typetree(fight_aoc_obj, tree)
    print("[+] Configured Bug Bite Fight AOC with full stitched moveset (all clips FileID 0)!")

    # 2. Car AOC: override_Bumblebee_GS_Kabam_car (PathID=-5475676132653162908)
    car_aoc_obj = bb_asset.objects[-5475676132653162908]
    tree = car_aoc_obj.read_typetree()
    clips = tree.get("m_Clips", [])
    clips[63]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_S3_CAR}
    tree["m_Clips"] = clips
    replace_str_in_tree(tree, old_cab, new_cab)
    commit_obj_typetree(car_aoc_obj, tree)
    print("[+] Configured Bug Bite Car AOC slot 63 with Cliffjumper S3 transformed car animation!")

    # 3. MatineeAOC: PathID=-3364085224588132041 (MonoBehaviour _overrideControllerList; keep S1/S2/etc., update SP3)
    matinee_aoc_obj = bb_asset.objects[-3364085224588132041]
    tree = matinee_aoc_obj.read_typetree()
    updated_maoc = set()
    for ov in tree.get("_overrideControllerList", []):
        shash = ov.get("StateHash")
        if shash == -1919714467:
            ov["OverrideClipName"] = "bugbite_gs_attackSpecial_03"
            updated_maoc.add(-1919714467)
        elif shash == 966217297:
            ov["OverrideClipName"] = "bugbite_gs_attackSpecial_03_hitReaction"
            updated_maoc.add(966217297)
    assert updated_maoc == {-1919714467, 966217297}, f"Missing SP3 hashes in MatineeAOC: {updated_maoc}"
    replace_str_in_tree(tree, old_cab, new_cab)
    commit_obj_typetree(matinee_aoc_obj, tree)
    print("[+] Configured Bug Bite MatineeAOC Base.SpecialAttack03 & HitReaction to bugbite_gs_attackSpecial_03*!")

    # 4. MoveSet: PathID=-7496201166252604881
    moveset_obj = bb_asset.objects[-7496201166252604881]
    tree = moveset_obj.read_typetree()
    moves = tree.get("_moves", [])
    moves[0]["_name"] = "move_tantrum_attack_light_01"
    moves[0]["_asset"] = {"m_FileID": 4, "m_PathID": -2890002397111034488}
    moves[1]["_name"] = "move_tantrum_attack_light_02"
    moves[1]["_asset"] = {"m_FileID": 4, "m_PathID": -4825681619876116179}
    moves[2]["_name"] = "move_tantrum_attack_light_03"
    moves[2]["_asset"] = {"m_FileID": 4, "m_PathID": -8759699025821425951}
    moves[3]["_name"] = "move_tantrum_attack_light_04"
    moves[3]["_asset"] = {"m_FileID": 4, "m_PathID": -4208587366598665143}
    moves[4]["_name"] = "move_brawler_attack_medium_02"
    moves[4]["_asset"] = {"m_FileID": 4, "m_PathID": 8863364277361988242}
    moves[5]["_name"] = "move_megatronus_attack_medium_02"
    moves[5]["_asset"] = {"m_FileID": 4, "m_PathID": 5104354136730126689}
    moves[6]["_name"] = "move_jazz_special_01"
    moves[6]["_asset"] = {"m_FileID": 4, "m_PathID": -8221976179409562418}
    moves[7]["_name"] = "move_bugbite_special_02"
    moves[7]["_asset"] = {"m_FileID": 4, "m_PathID": BUGBITE_S2_PID}
    tree["_moves"] = moves
    replace_str_in_tree(tree, old_cab, new_cab)
    commit_obj_typetree(moveset_obj, tree)
    print("[+] Configured Bug Bite MoveSet (L1..L4=Tantrum, M1=Ironhide, M2=Megatronus, S1=Jazz, S2=BugBite)!")

    # 5. PlayerReferences: point SpecialStagePrefab to cloned Cliffjumper Stage (-513981948225030119)
    pref_obj = bb_asset.objects[1157624665093363023]
    tree = pref_obj.read_typetree()
    tree["SpecialStagePrefab"] = {"m_FileID": 0, "m_PathID": CJ_SP3_STAGE_ROOT}
    replace_str_in_tree(tree, old_cab, new_cab)
    commit_obj_typetree(pref_obj, tree)
    print(f"[+] Wired PlayerReferences.SpecialStagePrefab -> {CJ_SP3_STAGE_ROOT} (cloned Cliffjumper S3 Stage)!")

    # 6. CharacterAudio: point gen_special_3 & _specialCharacterAudio to cloned ratchet_special_3 -> bugbite_gs_special_3
    caudio_obj = bb_asset.objects[-135521353996395750]
    tree = caudio_obj.read_typetree()
    found_ev = False
    for ev in tree.get("_events", []):
        if ev.get("_genEvent") == "gen_special_3":
            ev["_override"] = "bugbite_gs_special_3"
            found_ev = True
    assert found_ev, "Failed to find gen_special_3 in CharacterAudio._events!"
    spec_audio = tree.get("_specialCharacterAudio", [])
    replaced_spec = False
    for item in spec_audio:
        if item.get("m_PathID") == -3561701419133919622:
            item["m_FileID"] = 0
            item["m_PathID"] = 1281847170586998338
            replaced_spec = True
    assert replaced_spec, "Failed to find BB special audio PID in CharacterAudio._specialCharacterAudio!"
    replace_str_in_tree(tree, old_cab, new_cab)
    commit_obj_typetree(caudio_obj, tree)
    print("[+] Rewired CharacterAudio gen_special_3 -> bugbite_gs_special_3 (PID 1281847170586998338)!")

    # 7. Rename cloned Stage, Matinee, Audio GOs and update AudioClip & TFormMatineeStage & MatineeData
    for go_pid, new_go_name in [
        (-513981948225030119, "TFormStage_BugBite_GS_Special03"),
        (-3164215817585307476, "Matinee_BugBite_GS_Special03"),
        (-4808014442274116898, "bugbite_gs_special_3"),
        (8019343707475621852, "bugbite_gs_special_3"),
    ]:
        go_obj = bb_asset.objects[go_pid]
        gtree = go_obj.read_typetree()
        gtree["m_Name"] = new_go_name
        replace_str_in_tree(gtree, old_cab, new_cab)
        commit_obj_typetree(go_obj, gtree)

    aclip_obj = bb_asset.objects[5829207288378332728]
    atree = aclip_obj.read_typetree()
    atree["m_Name"] = "bugbite_gs_special_3"
    atree["m_Resource"]["m_Offset"] = appended_audio_off
    atree["m_Resource"]["m_Size"] = cj_audio_size
    atree["m_Resource"]["m_Source"] = f"archive:/{new_cab}/{new_cab}.resource"
    commit_obj_typetree(aclip_obj, atree)

    stage_mb_obj = bb_asset.objects[4051884971414969356]
    stree = stage_mb_obj.read_typetree()
    if stree.get("actorInfoList"):
        stree["actorInfoList"][0]["actor_id"] = "BugBite_GS_Kabam"
    replace_str_in_tree(stree, old_cab, new_cab)
    commit_obj_typetree(stage_mb_obj, stree)

    matinee_obj = bb_asset.objects[-8867447285746891126]
    mtree = matinee_obj.read_typetree()
    json_str = mtree.get("jSONData", "")
    for old_s, new_s in [
        ("cha_cliffjumper_gs_kabam_01 1|cha_cliffjumper_gs_kabam_01|transformed", "cha_bugbite_gs_kabam_01|transformed"),
        ("cha_cliffjumper_gs_kabam_01|transformed", "cha_bugbite_gs_kabam_01|transformed"),
        ("cha_cliffjumper_gs_kabam_01 1", "cha_bugbite_gs_kabam_01"),
        ("cha_cliffjumper_gs_kabam_01", "cha_bugbite_gs_kabam_01"),
        ("cha_cliffjumper_gs_kabam_00 1", "cha_bugbite_gs_kabam_00"),
        ("cha_cliffjumper_gs_kabam_00", "cha_bugbite_gs_kabam_00"),
        ("cha_cliffjumper_gs_kabam_wpns_gun_right 1|gasgun", "cha_bugbite_gs_kabam_wpns_pistol_right|rightgun"),
        ("cha_cliffjumper_gs_kabam_wpns_gun_right|gasgun", "cha_bugbite_gs_kabam_wpns_pistol_right|rightgun"),
        ("cha_cliffjumper_gs_kabam_wpns_gun_right 1", "cha_bugbite_gs_kabam_wpns_pistol_right"),
        ("cha_cliffjumper_gs_kabam_wpns_gun_right", "cha_bugbite_gs_kabam_wpns_pistol_right"),
        ("Cliffjumper_GS_Kabam", "BugBite_GS_Kabam"),
        ("TFormStage_Cliffjumper_GS_Special03", "TFormStage_BugBite_GS_Special03"),
        ("cliffjumper_gs_attackSpecial_03_hitReaction", "bugbite_gs_attackSpecial_03_hitReaction"),
        ("cliffjumper_gs_attackSpecial_03_transformed", "bugbite_gs_attackSpecial_03_transformed"),
        ("cliffjumper_gs_attackSpecial_03", "bugbite_gs_attackSpecial_03"),
    ]:
        json_str = json_str.replace(old_s, new_s)

    mjson = json.loads(json_str)

    def _fix_matinee_json_nodes(node):
        if isinstance(node, dict):
            if node.get("enp") in ("gasgun", "rightGun") or node.get("en") == "cha_bugbite_gs_kabam_wpns_pistol_right":
                node["enp"] = "rightgun"
            if (
                node.get("en") == "cha_bugbite_gs_kabam_01"
                and node.get("enp") in ("cha_bugbite_gs_kabam_01", "character_model")
                and "|transformed|" in node.get("eid", "")
            ):
                node["enp"] = "transformed"
            for v in node.values():
                _fix_matinee_json_nodes(v)
        elif isinstance(node, list):
            for item in node:
                _fix_matinee_json_nodes(item)

    _fix_matinee_json_nodes(mjson)
    fixed_json_str = json.dumps(mjson, separators=(",", ":"))
    assert "cliffjumper" not in fixed_json_str.lower(), "Residual cliffjumper in MatineeData jSONData!"
    assert "bumblebee" not in fixed_json_str.lower(), "Residual bumblebee in MatineeData jSONData!"
    assert "gasgun" not in fixed_json_str.lower(), "Residual gasgun in MatineeData jSONData!"
    mtree["jSONData"] = fixed_json_str
    replace_str_in_tree(mtree, old_cab, new_cab)
    commit_obj_typetree(matinee_obj, mtree)
    print("[+] Configured cloned Cliffjumper TFormMatineeStage & MatineeData for Bug Bite!")

    explicit_handled_pids = {
        4786041819736037741,
        -5475676132653162908,
        -3364085224588132041,
        -7496201166252604881,
        1157624665093363023,
        -135521353996395750,
        -513981948225030119,
        -3164215817585307476,
        -4808014442274116898,
        8019343707475621852,
        5829207288378332728,
        4051884971414969356,
        -8867447285746891126,
    }

    # 8. Materials, Textures, GameObjects, and remaining CAB references
    for obj in list(bb_asset.objects.values()):
        if obj.path_id in explicit_handled_pids:
            continue
        # Materials: glowing crimson red eyes and headlights
        if obj.type.name == "Material":
            tree = obj.read_typetree()
            if obj.path_id in (3469483409826248538, -4405333283484697666):
                cols = tree.get("m_SavedProperties", {}).get("m_Colors", [])
                for c in cols:
                    if isinstance(c, tuple) and len(c) == 2:
                        k, v = c
                        if k == "_emissive_intensity_col":
                            v.update({"r": 0.297, "g": 0.005, "b": 0.005, "a": 0.0})
                        elif k == "_EmissionColor":
                            v.update({"r": 1.0, "g": 0.05, "b": 0.05, "a": 1.0})
                    elif isinstance(c, dict):
                        for k, v in c.items():
                            if k == "_emissive_intensity_col":
                                v.update({"r": 0.297, "g": 0.005, "b": 0.005, "a": 0.0})
                            elif k == "_EmissionColor":
                                v.update({"r": 1.0, "g": 0.05, "b": 0.05, "a": 1.0})
                print(f"[+] Set glowing RED emissive material on {tree.get('m_Name')} (PID {obj.path_id})")
            replace_str_in_tree(tree, old_cab, new_cab)
            commit_obj_typetree(obj, tree)

        # Texture2D: Load custom recolored textures
        elif obj.type.name == "Texture2D":
            tex_name = obj.read_typetree().get("m_Name", "")
            if tex_name == "cha_bumblebee_gs_kabam_main_a" and user_main_path.is_file():
                tex = obj.read()
                tex.image = Image.open(user_main_path).convert("RGBA")
                tex.save()
                print(f"[+] Injected custom Bug Bite main texture: {user_main_path}")
            elif tex_name in ["tform_misc_A", "tform_misc_a"] and user_misc_path.is_file():
                tex = obj.read()
                tex.image = Image.open(user_misc_path).convert("RGBA")
                tex.save()
                print(f"[+] Injected custom Bug Bite vehicle misc texture: {user_misc_path}")
            elif tex_name == "cha_bumblebee_gs_kabam_wpns_a" and user_wpns_path.is_file():
                tex = obj.read()
                tex.image = Image.open(user_wpns_path).convert("RGBA")
                tex.save()
                print(f"[+] Injected custom Bug Bite weapons texture: {user_wpns_path}")
            elif tex_name in ["main_tform_misc_RAOE", "main_tform_misc_raoe"] and user_raoe_path.is_file():
                tex = obj.read()
                tex.m_TextureFormat = 4  # RGBA32
                tex.image = Image.open(user_raoe_path).convert("RGBA")
                tex.save()
                print(f"[+] Injected custom Bug Bite emissive RAOE (RGBA32) texture: {user_raoe_path}")
            else:
                tree = obj.read_typetree()
                replace_str_in_tree(tree, old_cab, new_cab)
                commit_obj_typetree(obj, tree)

        # Root GameObjects: Rename (skip existing S1/S2/heavy audio GOs)
        elif obj.type.name == "GameObject":
            tree = obj.read_typetree()
            gname = tree.get("m_Name", "")
            is_audio_go = any(gname.startswith(p) for p in [
                "bumblebee_special_", "bumblebee_attack_heavy", "bumblebee_projectile_"
            ])
            if "bumblebee" in gname.lower() and not is_audio_go:
                tree["m_Name"] = gname.replace("Bumblebee", "BugBite").replace("bumblebee", "bugbite")
            replace_str_in_tree(tree, old_cab, new_cab)
            commit_obj_typetree(obj, tree)

        # All other MonoBehaviours / Controllers / AudioClips (includes existing AudioClips' m_Resource.m_Source!)
        elif obj.type.name in ["AnimatorOverrideController", "MonoBehaviour", "AnimatorController", "AudioClip"]:
            try:
                tree = obj.read_typetree()
                replace_str_in_tree(tree, old_cab, new_cab)
                commit_obj_typetree(obj, tree)
            except Exception:
                pass

    # 9. Compute live closures from AssetBundle container roots and delete dead old BB SP3 objects
    ab_objs = [o for o in bb_asset.objects.values() if o.type.name == "AssetBundle"]
    assert len(ab_objs) == 1, f"Expected 1 AssetBundle object, found {len(ab_objs)}"
    ab_obj = ab_objs[0]
    ab_tree = ab_obj.read_typetree()

    live_local_pids = set()
    for _, cinfo in ab_tree.get("m_Container", []):
        rpid = cinfo["asset"]["m_PathID"]
        loc, _ = collect_closure(bb_asset, [rpid])
        live_local_pids |= loc

    all_monoscript_pids = {pid for pid, o in bb_asset.objects.items() if o.class_id == 115}
    dead_pids = old_bb_sp3_candidates - live_local_pids - all_monoscript_pids - {ab_obj.path_id}
    for dpid in dead_pids:
        if dpid in bb_asset.objects:
            del bb_asset.objects[dpid]
    print(f"[+] Deleted {len(dead_pids)} dead Bumblebee SP3 objects (stage/audio/old clips)!")

    # Verify the core old BB SP3 objects are all among dead_pids (not held alive anywhere else)
    must_be_dead = BB_SP3_OLD_CLIP_PIDS | {BB_SP3_STAGE_ROOT, BB_SP3_AUDIO_ROOT}
    still_alive = must_be_dead & live_local_pids
    assert not still_alive, f"Old Bumblebee SP3 objects are still referenced by live prefab! {still_alive}"

    # 10. Rebuild AssetBundle container & exact m_PreloadTable slices from live closures
    ab_tree["m_Name"] = "data/bugbite_gs_kabam_odr/bugbite_gs_kabam.assetbundle"
    new_container = []
    new_preload = []
    for path_str, asset_info in ab_tree.get("m_Container", []):
        new_path_str = path_str.replace("bumblebee_gs_kabam", "bugbite_gs_kabam")
        rpid = asset_info["asset"]["m_PathID"]
        _, closure_pptrs = collect_closure(bb_asset, [rpid])
        sorted_pptrs = sorted(closure_pptrs)
        asset_info["preloadIndex"] = len(new_preload)
        asset_info["preloadSize"] = len(sorted_pptrs)
        for fid, pid in sorted_pptrs:
            new_preload.append({"m_FileID": fid, "m_PathID": pid})
        new_container.append([new_path_str, asset_info])
    ab_tree["m_Container"] = new_container
    ab_tree["m_PreloadTable"] = new_preload
    replace_str_in_tree(ab_tree, old_cab, new_cab)
    commit_obj_typetree(ab_obj, ab_tree)
    print(f"[+] Rebuilt exact AssetBundle container table and preload list! Preload size: {len(new_preload)}")

    # Save rebuilt AssetBundle
    new_files = {}
    for subfname, subf in bf.files.items():
        new_subfname = subfname.replace(old_cab, new_cab)
        if hasattr(subf, "name"):
            subf.name = new_subfname
        new_files[new_subfname] = subf

    bf.files = new_files
    bf.version = 7
    bf.version_engine = "2020.3.31f1"
    bf.version_player = "5.x.x"

    target_bundle = out_dir / "bugbite_gs_kabam.assetbundle"
    target_bundle.write_bytes(bf.save(packer="lz4"))
    print(f"[+] Rebuilt UnityFS AssetBundle -> {target_bundle} ({target_bundle.stat().st_size:,} bytes)")

    # Verify loaded bundle with UnityPy Reload Integrity Gate
    print("[*] Running Chapter 9 Reload Integrity Gate...")
    verify_bugbite_bundle_integrity(target_bundle, new_cab, must_be_dead)

    # Generate Manifest
    mf_text = f"""ManifestFileVersion: 0
CRC: 0
Hashes:
  AssetFileHash:
    serializedVersion: 2
    Hash: {new_cab[4:]}
  TypeTreeHash:
    serializedVersion: 2
    Hash: 76e93ef67dadb9a900b941c584b3142d
HashAppended: 0
ClassTypes:
- Class: 1
  Script: {{instanceID: 0}}
- Class: 4
  Script: {{instanceID: 0}}
- Class: 21
  Script: {{instanceID: 0}}
- Class: 28
  Script: {{instanceID: 0}}
- Class: 43
  Script: {{instanceID: 0}}
- Class: 48
  Script: {{instanceID: 0}}
- Class: 65
  Script: {{instanceID: 0}}
- Class: 74
  Script: {{instanceID: 0}}
- Class: 83
  Script: {{instanceID: 0}}
- Class: 90
  Script: {{instanceID: 0}}
- Class: 91
  Script: {{instanceID: 0}}
- Class: 95
  Script: {{instanceID: 0}}
- Class: 114
  Script: {{instanceID: 0}}
- Class: 115
  Script: {{instanceID: 0}}
- Class: 137
  Script: {{instanceID: 0}}
- Class: 198
  Script: {{instanceID: 0}}
- Class: 199
  Script: {{instanceID: 0}}
- Class: 221
  Script: {{instanceID: 0}}
Assets:
- Assets/Bundles/Characters/Merged/BugBite_GS_Kabam/BugBite_GS_Kabam.prefab
- Assets/Bundles/Characters/Merged/BugBite_GS_Kabam/BugBite_GS_Kabam_lw.prefab
Dependencies:
- characters/character_fx.assetbundle
- characters/character_audio.assetbundle
- characters/moves.assetbundle
"""
    (out_dir / "bugbite_gs_kabam.assetbundle.manifest").write_text(mf_text, encoding="utf-8")

    # Ensure all portrait naming conventions exist WITHOUT overwriting user's Photoshop portraits!
    p_large = out_dir / "portrait_bugbite_large.png"
    p_ps_large = out_dir / "portrait_bugbite_gs_large.png"
    if p_ps_large.is_file():
        shutil.copyfile(p_ps_large, p_large)
        print(f"[+] Synced user's Photoshop portrait {p_ps_large} -> {p_large}")
    p_small = out_dir / "portrait_bugbite_gs_small.jpg"
    if p_small.is_file() and not (out_dir / "portrait_bugbite_small.jpg").is_file():
        shutil.copyfile(p_small, out_dir / "portrait_bugbite_small.jpg")
    print("[+] Protected user's Photoshop portraits and verified naming conventions!")
    print("[+] Bug Bite assetbundle generation complete!")


if __name__ == "__main__":
    generate_bugbite_assets()
