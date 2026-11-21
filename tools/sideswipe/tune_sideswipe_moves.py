import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import copy
import io
import shutil
from pathlib import Path
from collections import deque
import UnityPy
from UnityPy.files import ObjectReader
from UnityPy.streams import EndianBinaryReader

ROOT = Path(r"E:\Agent\TFTF-blender")
SS_BUNDLE_PATH = ROOT / "assets_redeco" / "sideswipe_cin_rotf.assetbundle"
SS_BACKUP_PATH = ROOT / "assets_redeco" / "sideswipe_cin_rotf.assetbundle.bak_before_tune"

CHEETOR_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "cheetor_bw_transmetal_odr" / "cheetor_bw_transmetal.assetbundle"
OPTIMUS_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "optimusprime_cin_tf_odr" / "optimusprime_cin_tf.assetbundle"

OP_STAGE_ROOT = 3256447252977910551
CHEETOR_M2_CLIP_PID = -1929738649458782990
CHEETOR_S1_CLIP_PID = 868105726138923071

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
    print("=== [Sideswipe] Tuning Moves & Stages ===")
    assert SS_BUNDLE_PATH.is_file(), f"Missing {SS_BUNDLE_PATH}"
    if not SS_BACKUP_PATH.is_file():
        shutil.copy2(SS_BUNDLE_PATH, SS_BACKUP_PATH)
        print(f"[+] Created backup: {SS_BACKUP_PATH.name}")

    env_ss = UnityPy.load(str(SS_BUNDLE_PATH))
    sf_ss = list(env_ss.assets)[0]

    # 1. Clone Optimus Prime SP3 Stage
    print(f"[*] Cloning Optimus Prime SP3 Stage ({OP_STAGE_ROOT}) into Sideswipe...")
    env_op = UnityPy.load(str(OPTIMUS_BUNDLE))
    sf_op = list(env_op.assets)[0]
    cloned_stage = clone_closure_into_sf(sf_op, sf_ss, [OP_STAGE_ROOT])
    print(f"[✓] Cloned {len(cloned_stage)} objects from Optimus Prime SP3 Stage!")

    # 2. Clone Cheetor M2 & S1 AnimationClips
    print("[*] Cloning Cheetor M2 and S1 AnimationClips into Sideswipe...")
    env_ch = UnityPy.load(str(CHEETOR_BUNDLE))
    sf_ch = list(env_ch.assets)[0]
    cloned_cheetor = clone_closure_into_sf(sf_ch, sf_ss, [CHEETOR_M2_CLIP_PID, CHEETOR_S1_CLIP_PID])
    print(f"[✓] Cloned {len(cloned_cheetor)} AnimationClips from Cheetor (M2={CHEETOR_M2_CLIP_PID}, S1={CHEETOR_S1_CLIP_PID})!")

    # 3. Update PlayerReferences
    # Find PlayerReferences
    pref_obj = None
    for o in sf_ss.objects.values():
        if o.type.name == "MonoBehaviour":
            tt = o.read_typetree()
            if "SpecialStagePrefab" in tt or "VictoryStagePrefab" in tt:
                pref_obj = o
                break
    assert pref_obj is not None, "PlayerReferences MonoBehaviour not found!"
    pref_tree = pref_obj.read_typetree()
    old_ssp = pref_tree.get("SpecialStagePrefab")
    old_vsp = pref_tree.get("VictoryStagePrefab")
    # Borrow Optimus S3 Stage (local cloned PID 3256447252977910551)
    pref_tree["SpecialStagePrefab"] = {"m_FileID": 0, "m_PathID": OP_STAGE_ROOT}
    # Borrow Drift Victory Stage (external FileID 8, PID 1484321543804849475)
    pref_tree["VictoryStagePrefab"] = {"m_FileID": 8, "m_PathID": 1484321543804849475}
    commit_obj_typetree(pref_obj, pref_tree)
    print(f"[✓] PlayerReferences updated:\n    SpecialStagePrefab: {old_ssp} -> {pref_tree['SpecialStagePrefab']}\n    VictoryStagePrefab: {old_vsp} -> {pref_tree['VictoryStagePrefab']}")

    # 4. Update Fight AOC (override_Barricade_Cin_DOTM_fight, PID -2047393535863576714)
    FIGHT_AOC_PID = -2047393535863576714
    fight_aoc_obj = sf_ss.objects[FIGHT_AOC_PID]
    fight_aoc_tree = fight_aoc_obj.read_typetree()

    slot_updates = {
        # S1 -> Drift S1 (FileID 5, PID -3664095140934993801)
        4: (6889857548200950017, {"m_FileID": 5, "m_PathID": -3664095140934993801}, "S1 -> Drift S1"),
        # S2 -> Cheetor S1 (FileID 0, PID 868105726138923071)
        5: (4730099292729452391, {"m_FileID": 0, "m_PathID": CHEETOR_S1_CLIP_PID}, "S2 -> Cheetor S1"),
        # S3 -> Optimus S3 (FileID 5, PID -4693390210307202245)
        31: (1238132665975540792, {"m_FileID": 5, "m_PathID": -4693390210307202245}, "S3 -> Optimus S3"),
        # S3 HitReaction -> Optimus S3 HitReaction (FileID 5, PID -7999335457178782659)
        32: (-1754835243131194270, {"m_FileID": 5, "m_PathID": -7999335457178782659}, "S3 React -> Optimus S3 HitReact"),
        # Victory -> Drift Sword Victory (FileID 5, PID -3196363985734342445)
        39: (3642901185112467297, {"m_FileID": 5, "m_PathID": -3196363985734342445}, "Victory -> Drift Victory"),
        # Victory Idle -> Drift Sword Victory Idle (FileID 5, PID 3303065432090877960)
        40: (-4048722777385356729, {"m_FileID": 5, "m_PathID": 3303065432090877960}, "Victory Idle -> Drift Victory Idle"),
        # M2 -> Cheetor M2 (FileID 0, PID -1929738649458782990)
        44: (1189595235236326705, {"m_FileID": 0, "m_PathID": CHEETOR_M2_CLIP_PID}, "M2 -> Cheetor M2"),
        # Heavy -> Sideswipe Car Heavy (FileID 5, PID -4177997624914663523)
        58: (-643812257501667161, {"m_FileID": 5, "m_PathID": -4177997624914663523}, "Heavy -> Sideswipe Car Heavy"),
    }

    clips = fight_aoc_tree.get("m_Clips", [])
    for slot_idx, (expected_orig, new_over, desc) in slot_updates.items():
        cl = clips[slot_idx]
        actual_orig = cl.get("m_OriginalClip", {}).get("m_PathID")
        assert actual_orig == expected_orig, f"Slot {slot_idx} orig PID mismatch: {actual_orig} != {expected_orig}"
        old_over = cl.get("m_OverrideClip")
        cl["m_OverrideClip"] = new_over
        print(f"  [Fight AOC Slot {slot_idx:02d}] {desc}: {old_over} -> {new_over}")

    commit_obj_typetree(fight_aoc_obj, fight_aoc_tree)
    print("[✓] Fight AOC updated!")

    # 5. Update MatineeAOC (PID -2768898539375720182)
    MATINEE_AOC_PID = -2768898539375720182
    mat_aoc_obj = sf_ss.objects[MATINEE_AOC_PID]
    mat_aoc_tree = mat_aoc_obj.read_typetree()

    hash_updates = {
        1671240305: ("drift_cin_attackSpecial_01", "S1"),
        -90944565: ("Cheetor_BW_attackSpecial_01", "S2"),
        297974710: ("Cheetor_BW_attackMedium_02_doubleHand", "M2"),
        -1919714467: ("optimus_prime_attackSpecial_03", "S3"),
        966217297: ("optimus_prime_attackSpecial_03_hitReaction", "S3 HitReact"),
        -204748204: ("sword_male_victory", "Victory"),
        -1459930005: ("sword_male_victory_idle", "Victory Idle"),
        944691146: ("Car_Normal_attackHeavy", "Heavy"),
    }

    matched_hashes = set()
    for item in mat_aoc_tree.get("_overrideControllerList", []):
        sh = item.get("StateHash")
        if sh in hash_updates:
            new_clip_name, desc = hash_updates[sh]
            old_clip_name = item.get("OverrideClipName")
            item["OverrideClipName"] = new_clip_name
            matched_hashes.add(sh)
            print(f"  [MatineeAOC StateHash={sh}] {desc}: '{old_clip_name}' -> '{new_clip_name}'")

    assert matched_hashes == set(hash_updates.keys()), f"Missing StateHashes in MatineeAOC: {set(hash_updates.keys()) - matched_hashes}"
    commit_obj_typetree(mat_aoc_obj, mat_aoc_tree)
    print("[✓] MatineeAOC updated!")

    # 6. Update MoveSet (PID -5126079019749064592)
    MOVESET_PID = -5126079019749064592
    moveset_obj = sf_ss.objects[MOVESET_PID]
    moveset_tree = moveset_obj.read_typetree()
    moves = moveset_tree.get("_moves", [])

    moveset_updates = {
        # Move 05: Cheetor M2
        5: ("move_cheetor_attack_medium_02", {"m_FileID": 4, "m_PathID": -8892327269443784769}),
        # Move 06: Drift S1
        6: ("move_drift_special_01", {"m_FileID": 4, "m_PathID": -6173328959056132852}),
        # Move 07: Cheetor S1
        7: ("move_cheetor_special_01", {"m_FileID": 4, "m_PathID": 7655358371711847767}),
        # Move 43: Sideswipe Heavy Donut
        43: ("move_heavy_car_donut", {"m_FileID": 4, "m_PathID": -6072851833384157097}),
    }

    for midx, (new_name, new_asset) in moveset_updates.items():
        old_m = moves[midx]
        print(f"  [MoveSet Move {midx:02d}] '{old_m.get('_name')}' -> '{new_name}' ({new_asset})")
        old_m["_name"] = new_name
        old_m["_asset"] = new_asset

    commit_obj_typetree(moveset_obj, moveset_tree)
    print("[✓] MoveSet updated!")

    # 7. Clean up dead unreachable old Barricade SP3 objects to prevent bloat
    print("[*] Checking for unreachable dead objects...")
    ab_obj = next(o for o in sf_ss.objects.values() if o.type.name == "AssetBundle")
    ab_tree = ab_obj.read_typetree()

    live_pids = set()
    for cname, cinfo in ab_tree.get("m_Container", []):
        rpid = int(cinfo["asset"]["m_PathID"])
        loc, _ = collect_closure(sf_ss, [rpid])
        live_pids |= loc

    all_monoscripts = {pid for pid, o in sf_ss.objects.items() if o.class_id == 115}
    dead_pids = set(sf_ss.objects.keys()) - live_pids - all_monoscripts - {ab_obj.path_id}
    print(f"  Found {len(dead_pids)} unreachable dead objects. Cleaning them up...")
    for dpid in dead_pids:
        del sf_ss.objects[dpid]
    print(f"[✓] Deleted {len(dead_pids)} dead objects!")

    # 8. Rebuild exact AssetBundle m_PreloadTable from live closures
    print("[*] Rebuilding AssetBundle m_PreloadTable...")
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

    # 9. Save bundle with packer="lz4"
    print(f"[*] Saving tuned bundle to {SS_BUNDLE_PATH} (packer='lz4')...")
    raw_saved = env_ss.file.save(packer="none")
    env_reload = UnityPy.load(io.BytesIO(raw_saved))
    with open(SS_BUNDLE_PATH, "wb") as f:
        f.write(env_reload.file.save(packer="lz4"))
    
    size_mb = SS_BUNDLE_PATH.stat().st_size / (1024 * 1024)
    print(f"[✓] Successfully saved {SS_BUNDLE_PATH.name} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    main()
