import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import copy
import io
import json
import shutil
from pathlib import Path
from collections import deque
import UnityPy
from UnityPy.files import ObjectReader
from UnityPy.streams import EndianBinaryReader

ROOT = Path(r"E:\Agent\TFTF-blender")
SS_BUNDLE_PATH = ROOT / "assets_redeco" / "sideswipe_cin_rotf.assetbundle"
NECRO_BUNDLE_PATH = ROOT / "extracted_apk" / "assets" / "assetpack" / "necrotronus_gs_kabam_odr" / "necrotronus_gs_kabam.assetbundle"

# PIDs
FIGHT_AOC_PID = -2047393535863576714
CAR_AOC_PID = 9188181967379678347
MATINEE_AOC_PID = -2768898539375720182
MATINEE_DATA_PID = 8781936353626196161
NECRO_IDLE_CLIP_PID = -8455018533602519118

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
        try:
            tree = obj.read_typetree()
        except Exception:
            continue
        for pptr in iter_pptrs_in_tree(tree):
            fid = pptr.get("m_FileID", 0)
            target_pid = pptr.get("m_PathID", 0)
            if not target_pid:
                continue
            all_pptrs.add((fid, target_pid))
            if fid == 0 and target_pid not in visited_local:
                if target_pid in sf.objects:
                    visited_local.add(target_pid)
                    queue.append(target_pid)
    return visited_local, all_pptrs

def commit_obj_typetree(obj, tree):
    data = obj.save_typetree(tree)
    obj.reader = EndianBinaryReader(data, endian=obj.reader.endian)
    obj.byte_start = 0
    obj.byte_size = len(data)
    return data

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
    local_pids, _ = collect_closure(src_sf, root_pids)
    ext_map = _build_ext_file_id_map(src_sf, dst_sf)

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

    pending_new_tp_keys = {}
    src_obj_to_dst_type_id = {}

    for pid in sorted(local_pids):
        src_obj = src_sf.objects[pid]
        src_tp = src_obj.serialized_type
        if src_tp is None:
            raise RuntimeError(f"Source object {pid} ({src_obj.type.name}) has serialized_type=None")

        if src_tp.class_id == 115:
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

def main():
    print("=== [Sideswipe] Patching SP3 Transformation & Necrotronus Standing Idle ===")
    assert SS_BUNDLE_PATH.is_file(), f"Missing {SS_BUNDLE_PATH}"
    assert NECRO_BUNDLE_PATH.is_file(), f"Missing {NECRO_BUNDLE_PATH}"

    env_ss = UnityPy.load(str(SS_BUNDLE_PATH))
    sf_ss = list(env_ss.assets)[0]

    # =========================================================================
    # 1. FIX ISSUE 1: SP3 Transformation Tracks & Car AOC
    # =========================================================================
    print("\n--- [Fix 1: SP3 Vehicle Transformation] ---")
    
    # 1.1 MatineeData.jSONData mesh node redirection
    mdata_obj = sf_ss.objects.get(MATINEE_DATA_PID)
    assert mdata_obj is not None, f"Missing MatineeData {MATINEE_DATA_PID}"
    mdata_tree = mdata_obj.read_typetree()
    jstr = mdata_tree.get("jSONData", "")

    # Check and replace
    assert "cha_optimus_cin_tf_00" in jstr, "cha_optimus_cin_tf_00 not found in MatineeData!"
    assert "cha_optimusprime_cin_tf_01" in jstr, "cha_optimusprime_cin_tf_01 not found in MatineeData!"

    jstr_fixed = jstr.replace("cha_optimus_cin_tf_00", "cha_barricade_cin_dotm_00")
    jstr_fixed = jstr_fixed.replace("cha_optimusprime_cin_tf_01", "cha_barricade_cin_dotm_01")
    
    mdata_tree["jSONData"] = jstr_fixed
    commit_obj_typetree(mdata_obj, mdata_tree)
    print("  [✓] Updated MatineeData tracks:")
    print("      Robot Mesh Track 29: 'cha_optimus_cin_tf_00' -> 'cha_barricade_cin_dotm_00'")
    print("      Vehicle Mesh Track 06: 'cha_optimusprime_cin_tf_01' -> 'cha_barricade_cin_dotm_01'")

    # 1.2 Car AOC Slot 63 (orig 5620803938405291589) -> optimus_prime_attackSpecial_03_transformed (FileID 5, PID -341215899653024)
    car_aoc_obj = sf_ss.objects.get(CAR_AOC_PID)
    assert car_aoc_obj is not None, f"Missing Car AOC {CAR_AOC_PID}"
    car_aoc_tree = car_aoc_obj.read_typetree()
    clips = car_aoc_tree.get("m_Clips", [])
    assert len(clips) > 63, "Car AOC does not have 64 clips!"
    slot63 = clips[63]
    orig_pid = slot63.get("m_OriginalClip", {}).get("m_PathID")
    assert orig_pid == 5620803938405291589, f"Slot 63 orig PID mismatch: {orig_pid}"
    old_over = slot63.get("m_OverrideClip")
    slot63["m_OverrideClip"] = {"m_FileID": 5, "m_PathID": -341215899653024}
    commit_obj_typetree(car_aoc_obj, car_aoc_tree)
    print(f"  [✓] Updated Car AOC Slot 63 (Base.SpecialAttack03): {old_over} -> {slot63['m_OverrideClip']} ('optimus_prime_attackSpecial_03_transformed')")

    # =========================================================================
    # 2. FIX ISSUE 2: Borrow Necrotronus Standing Idle
    # =========================================================================
    print("\n--- [Fix 2: Borrow Necrotronus Standing Combat Idle] ---")

    # 2.1 Clone Prefight_Brawler_idle_Megatron from Necrotronus bundle
    env_necro = UnityPy.load(str(NECRO_BUNDLE_PATH))
    sf_necro = list(env_necro.assets)[0]
    cloned_idle = clone_closure_into_sf(sf_necro, sf_ss, [NECRO_IDLE_CLIP_PID])
    print(f"  [✓] Cloned AnimationClip 'Prefight_Brawler_idle_Megatron' (PID {NECRO_IDLE_CLIP_PID}) from Necrotronus into Sideswipe bundle!")

    # 2.2 Wire Fight AOC Slot 00 (char_idle, orig -1862916429741742381)
    fight_aoc_obj = sf_ss.objects[FIGHT_AOC_PID]
    fight_aoc_tree = fight_aoc_obj.read_typetree()
    fclips = fight_aoc_tree.get("m_Clips", [])
    slot00 = fclips[0]
    orig00 = slot00.get("m_OriginalClip", {}).get("m_PathID")
    assert orig00 == -1862916429741742381, f"Slot 00 orig PID mismatch: {orig00}"
    old_idle_over = slot00.get("m_OverrideClip")
    slot00["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": NECRO_IDLE_CLIP_PID}
    commit_obj_typetree(fight_aoc_obj, fight_aoc_tree)
    print(f"  [✓] Updated Fight AOC Slot 00 (char_idle): {old_idle_over} -> {slot00['m_OverrideClip']} ('Prefight_Brawler_idle_Megatron')")

    # 2.3 Wire MatineeAOC StateHash -1405706489 (Base.Idle)
    mat_aoc_obj = sf_ss.objects[MATINEE_AOC_PID]
    mat_aoc_tree = mat_aoc_obj.read_typetree()
    found_idle_hash = False
    for item in mat_aoc_tree.get("_overrideControllerList", []):
        if item.get("StateHash") == -1405706489:
            old_name = item.get("OverrideClipName")
            item["OverrideClipName"] = "Prefight_Brawler_idle_Megatron"
            found_idle_hash = True
            print(f"  [✓] Updated MatineeAOC StateHash=-1405706489 (Base.Idle): '{old_name}' -> '{item['OverrideClipName']}'")
            break
    assert found_idle_hash, "StateHash -1405706489 not found in MatineeAOC!"
    commit_obj_typetree(mat_aoc_obj, mat_aoc_tree)

    # =========================================================================
    # 3. CLEANUP DEAD OBJECTS & REBUILD PRELOAD TABLE
    # =========================================================================
    print("\n--- [Cleanup & Preload Table Rebuild] ---")
    ab_obj = next(o for o in sf_ss.objects.values() if o.type.name == "AssetBundle")
    ab_tree = ab_obj.read_typetree()

    live_pids = set()
    for cname, cinfo in ab_tree.get("m_Container", []):
        rpid = int(cinfo["asset"]["m_PathID"])
        loc, _ = collect_closure(sf_ss, [rpid])
        live_pids |= loc

    all_monoscripts = {pid for pid, o in sf_ss.objects.items() if o.class_id == 115}
    dead_pids = set(sf_ss.objects.keys()) - live_pids - all_monoscripts - {ab_obj.path_id}
    print(f"  Found {len(dead_pids)} unreachable dead objects. Cleaning up...")
    for dpid in dead_pids:
        del sf_ss.objects[dpid]
    print(f"  [✓] Deleted {len(dead_pids)} dead objects!")

    # Rebuild m_PreloadTable
    new_preload = []
    for cname, cinfo in ab_tree.get("m_Container", []):
        rpid = int(cinfo["asset"]["m_PathID"])
        _, closure_pptrs = collect_closure(sf_ss, [rpid])
        sorted_pptrs = sorted(closure_pptrs)
        cinfo["preloadIndex"] = len(new_preload)
        cinfo["preloadSize"] = len(sorted_pptrs)
        for fid, pid in sorted_pptrs:
            new_preload.append({"m_FileID": fid, "m_PathID": pid})
        print(f"  [Preload Slice] {cname}: size={len(sorted_pptrs)} (index={cinfo['preloadIndex']})")
    ab_tree["m_PreloadTable"] = new_preload
    commit_obj_typetree(ab_obj, ab_tree)

    # Save bundle
    print(f"\n[*] Saving patched bundle to {SS_BUNDLE_PATH} (packer='lz4')...")
    raw_saved = env_ss.file.save(packer="none")
    env_reload = UnityPy.load(io.BytesIO(raw_saved))
    with open(SS_BUNDLE_PATH, "wb") as f:
        f.write(env_reload.file.save(packer="lz4"))
    size_mb = SS_BUNDLE_PATH.stat().st_size / (1024 * 1024)
    print(f"[✓] Successfully saved {SS_BUNDLE_PATH.name} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    main()
