#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_vortex_melee.py

Rewire Vortex (`vortex_gs`) melee combo moveset & AnimationClips in `assets_redeco/vortex_gs.assetbundle`
and register `move_vortex_attack_light_04` inside `assets_redeco/moves.assetbundle`:

  - L1 (Base.LightAttack01)  <- G1 Optimus Prime L1 (OptimusPrime_GS_V / move_brawler_2_attack_light_01)
  - L2 (Base.LightAttack02)  <- G1 Optimus Prime L2 (OptimusPrime_GS_V / move_brawler_2_attack_light_02)
  - L3 (Base.LightAttack03)  <- Jazz L1 (jazz_gs_twm05 / move_jazz_attack_light_01)
  - L4 (Base.LightAttack04)  <- Hound L2 (hound_cin_tlk / move_vortex_attack_light_04 cloned w/ L4 ender window d=19)
  - M1 (Base.MediumAttack01) <- Optimus Primal M1 (optimusprimal_bw_mp32 / move_primal_attack_medium_01)
  - M2 (Base.MediumAttack02) <- Bonecrusher M2 (bonecrusher_cin_rotf / move_feral_attack_medium_02 + fx_r_dash_trail)

Enforces full Chapter 9 AssetBundle integrity checks (`packer="lz4"`, `script_types` sort order,
`MonoBehaviour` `m_Script` consistency, and contiguous sorted `m_PreloadTable` / `m_Container` slices).
"""

import copy
import io
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

try:
    import UnityPy
except ImportError:
    print("Error: UnityPy is required (pip install UnityPy lz4).")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent

# Dedicated unique PathID for Vortex L4 (cloned from move_hound_attack_light_02 with L4 combo-ender window)
VORTEX_L4_MOVE_PID = -8888888888888888885
HOUND_L2_MOVE_PID = 4630904994207091556

# Donor Move PathIDs inside moves.assetbundle (Vortex FileID = 5)
MOVE_G1_OP_L1_PID = 6034126977261442960   # move_brawler_2_attack_light_01
MOVE_G1_OP_L2_PID = 1957860170544410956   # move_brawler_2_attack_light_02
MOVE_JAZZ_L1_PID = 8466871985765689713    # move_jazz_attack_light_01
MOVE_PRIMAL_M1_PID = -6973531985879257707 # move_primal_attack_medium_01
MOVE_BONE_M2_PID = 5917300479849172794    # move_feral_attack_medium_02

# External FX needed by Bonecrusher M2 (move_feral_attack_medium_02 -> TrailMoveEvent fx_r_dash_trail)
# In vortex_gs.assetbundle: FileID 4 = character_fx.assetbundle (CAB-a742a3fff84aa604ba32daca2b1ea500)
FX_DASH_TRAIL_FID = 4
FX_DASH_TRAIL_PID = -7577462007175247289

# Vortex existing local melee AnimationClip PathIDs (currently referenced only by Fight AOC)
VORTEX_CLIP_SLOTS = {
    "L1": (-7330088452263216800, 2,  3149807030316843707, "Base.LightAttack01"),
    "L2": ( 5166650261907369174, 3,  1493990355315399625, "Base.LightAttack02"),
    "L3": (-3700407944767136193, 41, -8618744054794967589, "Base.LightAttack03"),
    "L4": (-3315683300663255893, 43, 7758611357151580349, "Base.LightAttack04"),
    "M1": (-5673422065606134363, 42, 424597727730099647,  "Base.MediumAttack01"),
    "M2": (-2629648800268115484, 44, 1189595235236326705, "Base.MediumAttack02"),
}

VORTEX_FIGHT_AOC_PID = 259380691726149969
VORTEX_MOVESET_PID = -2282744758651308026
VORTEX_PREFABLIB_PID = -5353390358171322875
VORTEX_AOC_META_PID = 4509828945994715609


def patch_moves_bundle() -> Path:
    """Ensure assets_redeco/moves.assetbundle contains move_vortex_attack_light_04 (Hound L2 tuned as L4 ender)."""
    moves_path = ROOT / "assets_redeco" / "moves.assetbundle"
    assert moves_path.exists(), f"Missing {moves_path}"

    print(f"[*] Loading moves bundle: {moves_path}")
    env = UnityPy.load(str(moves_path))
    sf = list(env.assets)[0]

    hound_reader = sf.objects.get(HOUND_L2_MOVE_PID)
    assert hound_reader is not None, "Failed to find move_hound_attack_light_02!"
    ab_obj = next((o for o in sf.objects.values() if o.type.name == "AssetBundle"), None)
    assert ab_obj is not None, "Failed to find AssetBundle object in moves!"

    l4_move = copy.deepcopy(hound_reader.read_typetree())
    assert l4_move.get("m_Name") == "move_hound_attack_light_02"
    l4_move["m_Name"] = "move_vortex_attack_light_04"

    script_data = json.loads(l4_move["m_Script"])
    move_def = script_data["moves"]
    move_def["id"] = "move_vortex_attack_light_04"
    if "m_Name" in move_def:
        move_def["m_Name"] = "move_vortex_attack_light_04"

    for ev in move_def.get("events", []):
        ev["mn"] = "move_vortex_attack_light_04"
        etype = ev.get("type")
        if etype == "AttackWindowMoveEvent":
            # Standard TFTF L4 combo ender recovery window (~19 frames = 0.63s, matching Hound L2 clip ~0.667s)
            ev["d"] = 19
        elif etype == "HitMoveEvent":
            hd = ev.get("hd", {})
            hd["hs"] = 12
            hd["bhs"] = 6
            di = ev.get("di", {})
            # Match Vortex's larger brute CapsuleCollider reach cleanly
            if float(di.get("r", 0)) < 8.5:
                di["r"] = 8.5

    l4_move["m_Script"] = json.dumps(script_data)

    existing = sf.objects.get(VORTEX_L4_MOVE_PID)
    if existing is not None:
        existing_name = existing.read_typetree().get("m_Name", "")
        assert existing_name == "move_vortex_attack_light_04", f"PID collision on {VORTEX_L4_MOVE_PID}: {existing_name}"
        existing.save_typetree(l4_move)
        print(f"  [~] Updated existing move_vortex_attack_light_04 (PID={VORTEX_L4_MOVE_PID})")
    else:
        new_reader = copy.copy(hound_reader)
        new_reader.path_id = VORTEX_L4_MOVE_PID
        sf.objects[VORTEX_L4_MOVE_PID] = new_reader
        new_reader.save_typetree(l4_move)
        print(f"  [+] Added move_vortex_attack_light_04 (PID={VORTEX_L4_MOVE_PID})")

    ab_tree = ab_obj.read_typetree()
    container = [c for c in ab_tree.get("m_Container", []) if "move_vortex_attack_light_04" not in c[0]]
    container.append([
        "assets/bundles/movedata/move_vortex_attack_light_04.txt",
        {"preloadIndex": 0, "preloadSize": 0, "asset": {"m_FileID": 0, "m_PathID": VORTEX_L4_MOVE_PID}},
    ])
    ab_tree["m_Container"] = container
    ab_obj.save_typetree(ab_tree)

    out_bytes = env.file.save(packer="lz4")
    moves_path.write_bytes(out_bytes)
    print(f"  [+] Saved {moves_path.name} ({len(out_bytes):,} bytes)")

    # Reload verification gate
    chk = UnityPy.load(str(moves_path))
    chk_sf = list(chk.assets)[0]
    text_names = set()
    for o in chk_sf.objects.values():
        if o.type.name == "TextAsset":
            text_names.add(o.read_typetree().get("m_Name", ""))
    assert len(chk_sf.objects) >= 945, f"Moves count {len(chk_sf.objects)} < 945!"
    chromia_cnt = sum(1 for n in text_names if "chromia" in n.lower())
    deadend_cnt = sum(1 for n in text_names if "deadend" in n.lower() or "dead_end" in n.lower())
    assert chromia_cnt >= 12, f"Missing Chromia moves ({chromia_cnt})!"
    assert deadend_cnt >= 8, f"Missing Dead End moves ({deadend_cnt})!"
    for req in ("move_lifeline_special_01", "move_lifeline_special_02", "move_vortex_special_01", "move_vortex_special_02", "move_vortex_attack_light_04"):
        assert req in text_names, f"Missing required move: {req}"
    v4_obj = chk_sf.objects[VORTEX_L4_MOVE_PID].read_typetree()
    v4_evs = json.loads(v4_obj["m_Script"])["moves"]["events"]
    assert any(e.get("type") == "AttackWindowMoveEvent" and e.get("d") == 19 for e in v4_evs)
    print(f"  [PASS] moves.assetbundle verified: total_objects={len(chk_sf.objects)}, Chromia={chromia_cnt}, DeadEnd={deadend_cnt}")
    return moves_path


def load_donor_clips() -> dict:
    """Load the 6 target donor AnimationClip typetrees directly from extracted assets."""
    specs = {
        "L1": (ROOT / "extracted_apk/assets/assetpack/characters/characters.assetbundle", -3430411122056989002, "brawler2_normal_attackLight_01_hook"),
        "L2": (ROOT / "extracted_apk/assets/assetpack/characters/characters.assetbundle", -4356099580166283104, "brawler2_normal_attackLight_02_hook"),
        "L3": (ROOT / "extracted_apk/assets/assetpack/jazz_gs_twm05_odr/jazz_gs_twm05.assetbundle", -6242698120350777026, "Jazz_GS_attackLight_01_upperCut"),
        "L4": (ROOT / "extracted_apk/assets/assetpack/hound_cin_tlk_odr/hound_cin_tlk.assetbundle", 3044918183802867597, "Hound_Cin_attackLight_02_rightPunch"),
        "M1": (ROOT / "extracted_apk/assets/assetpack/optimusprimal_bw_mp32_odr/optimusprimal_bw_mp32.assetbundle", 91323492706800577, "OPtimusPrimal_BW_attackMedium_01_smash"),
        "M2": (ROOT / "extracted_apk/assets/assetpack/characters_procedural_odr/character_anim_procedural.assetbundle", 835124858721742528, "feral_normal_attackMedium_02_big_up_slash_L"),
    }
    cache = {}
    clips = {}
    for slot_key, (bpath, clip_pid, expected_name) in specs.items():
        assert bpath.exists(), f"Missing donor bundle: {bpath}"
        if bpath not in cache:
            cache[bpath] = list(UnityPy.load(str(bpath)).assets)[0]
        dsf = cache[bpath]
        co = dsf.objects.get(clip_pid)
        assert co is not None and co.type.name == "AnimationClip", f"Clip {clip_pid} missing in {bpath.name}"
        ctree = copy.deepcopy(co.read_typetree())
        assert ctree.get("m_Name") == expected_name, f"Expected clip '{expected_name}', got '{ctree.get('m_Name')}'"
        # Verify pure humanoid self-contained clip with 0 external PPtr dependencies
        def _has_ext_pptr(x):
            if isinstance(x, dict):
                if "m_PathID" in x and "m_FileID" in x and x["m_PathID"] != 0:
                    return True
                return any(_has_ext_pptr(v) for v in x.values())
            if isinstance(x, list):
                return any(_has_ext_pptr(v) for v in x)
            return False
        assert not _has_ext_pptr(ctree), f"Unexpected PPtr dependency inside donor clip {expected_name}!"
        clips[slot_key] = ctree
        stop_t = ctree.get("m_MuscleClip", {}).get("m_StopTime", 0.0)
        print(f"  [+] Loaded donor {slot_key}: {expected_name} (stop={stop_t:.3f}s)")
    return clips


def collect_reachable(sf, root_pid: int) -> set:
    """Recursively collect all reachable (m_FileID, m_PathID) PPtrs from root_pid inside sf."""
    seen_local = set()
    reachable = set()
    stack = [root_pid]

    def _scan(x):
        if isinstance(x, dict):
            if "m_FileID" in x and "m_PathID" in x:
                fid, pid = int(x["m_FileID"]), int(x["m_PathID"])
                if pid != 0:
                    reachable.add((fid, pid))
                    if fid == 0 and pid not in seen_local:
                        stack.append(pid)
            for v in x.values():
                _scan(v)
        elif isinstance(x, list):
            for v in x:
                _scan(v)

    while stack:
        pid = stack.pop()
        if pid in seen_local:
            continue
        seen_local.add(pid)
        reachable.add((0, pid))
        o = sf.objects.get(pid)
        if o is not None:
            try:
                _scan(o.read_typetree())
            except Exception:
                pass
    return reachable


def rebuild_container_preload_table(sf):
    """Ensure every m_Container slice includes all reachable PPtrs in contiguous FileID runs sorted by PathID."""
    ab_obj = next(o for o in sf.objects.values() if o.type.name == "AssetBundle")
    ab_tree = ab_obj.read_typetree()
    old_pt = ab_tree.get("m_PreloadTable", [])
    container = ab_tree.get("m_Container", [])

    new_pt = []
    for cname, cinfo in container:
        pidx = int(cinfo.get("preloadIndex", 0))
        psize = int(cinfo.get("preloadSize", 0))
        root_pid = int(cinfo["asset"]["m_PathID"])

        existing_slice = old_pt[pidx : pidx + psize]
        # Preserve existing contiguous FileID run ordering
        fid_order = []
        by_fid = {}
        for entry in existing_slice:
            fid, pid = int(entry["m_FileID"]), int(entry["m_PathID"])
            if fid not in by_fid:
                fid_order.append(fid)
                by_fid[fid] = set()
            by_fid[fid].add(pid)

        reachable = collect_reachable(sf, root_pid)
        missing = reachable - {(f, p) for f, pset in by_fid.items() for p in pset}
        for fid, pid in missing:
            if fid not in by_fid:
                fid_order.append(fid)
                by_fid[fid] = set()
            by_fid[fid].add(pid)
            print(f"    [+] PreloadTable[{cname}]: added missing ({fid}, {pid})")

        cinfo["preloadIndex"] = len(new_pt)
        built_slice = []
        for fid in fid_order:
            for pid in sorted(by_fid[fid]):
                built_slice.append({"m_FileID": fid, "m_PathID": pid})
        cinfo["preloadSize"] = len(built_slice)
        new_pt.extend(built_slice)

    ab_tree["m_PreloadTable"] = new_pt
    ab_tree["m_Container"] = container
    ab_obj.save_typetree(ab_tree)


def verify_bundle_integrity(bundle_path: Path, expected_clips: dict):
    """Run full Chapter 9 Reload Integrity Gate + Combat Melee Verification on saved vortex_gs.assetbundle."""
    env = UnityPy.load(str(bundle_path))
    sf = list(env.assets)[0]

    # 1. SerializedFile.script_types sorted strictly ascending by (local_serialized_file_index, local_identifier_in_file)
    st_keys = [(x.local_serialized_file_index, x.local_identifier_in_file) for x in sf.script_types]
    assert st_keys == sorted(st_keys), f"script_types not sorted ascending!"

    # 2. Every MonoBehaviour (class_id == 114) has valid script_type_index matching its m_Script
    for o in sf.objects.values():
        st = getattr(o, "serialized_type", None)
        if st is not None and o.type.name == "MonoBehaviour":
            sti = st.script_type_index
            assert 0 <= sti < len(sf.script_types), f"Invalid script_type_index {sti} on obj {o.path_id}"
            ident = sf.script_types[sti]
            t = o.read_typetree()
            ms = t.get("m_Script", {})
            assert (ms.get("m_FileID"), ms.get("m_PathID")) == (ident.local_serialized_file_index, ident.local_identifier_in_file), (
                f"MonoBehaviour {o.path_id} m_Script mismatch: {ms} vs {(ident.local_serialized_file_index, ident.local_identifier_in_file)}"
            )

    # 3. Every local PPtr (m_FileID == 0) resolves cleanly inside sf.objects
    def _check_local_pptrs(x, owner_pid):
        if isinstance(x, dict):
            if "m_FileID" in x and "m_PathID" in x:
                if x["m_FileID"] == 0 and x["m_PathID"] != 0:
                    assert x["m_PathID"] in sf.objects, f"Dangling local PPtr {x} in obj {owner_pid}"
            for v in x.values():
                _check_local_pptrs(v, owner_pid)
        elif isinstance(x, list):
            for v in x:
                _check_local_pptrs(v, owner_pid)

    for pid, o in sf.objects.items():
        if o.type.name in ("GameObject", "MonoBehaviour", "AnimatorOverrideController"):
            _check_local_pptrs(o.read_typetree(), pid)

    # 4. m_PreloadTable & m_Container contiguous slices, ascending PathIDs per FileID, 0 missing reachable PPtrs
    ab_tree = next(o for o in sf.objects.values() if o.type.name == "AssetBundle").read_typetree()
    pt = ab_tree.get("m_PreloadTable", [])
    cursor = 0
    for cname, cinfo in ab_tree.get("m_Container", []):
        pidx = int(cinfo["preloadIndex"])
        psize = int(cinfo["preloadSize"])
        assert pidx == cursor, f"Non-contiguous slice on {cname}: start={pidx}, expected={cursor}"
        cursor += psize
        sl = pt[pidx : pidx + psize]
        seen_fids = set()
        prev_fid = None
        prev_pid = None
        for entry in sl:
            fid, pid = int(entry["m_FileID"]), int(entry["m_PathID"])
            if fid != prev_fid:
                assert fid not in seen_fids, f"Split FileID {fid} run inside {cname}"
                seen_fids.add(fid)
                prev_fid = fid
                prev_pid = pid
            else:
                assert pid > prev_pid, f"Unsorted/duplicate PathID in {cname} FileID {fid}: {prev_pid} -> {pid}"
                prev_pid = pid
        reach = collect_reachable(sf, int(cinfo["asset"]["m_PathID"]))
        sl_set = {(int(x["m_FileID"]), int(x["m_PathID"])) for x in sl}
        missing = reach - sl_set
        assert not missing, f"Container {cname} missing reachable PPtrs: {missing}"

    # 5. Verify Fight AOC, MoveSet, PrefabList and _overrideControllerList
    aoc = sf.objects[VORTEX_FIGHT_AOC_PID].read_typetree()
    for key, (local_pid, slot_idx, orig_pid, _state_name) in VORTEX_CLIP_SLOTS.items():
        c = aoc["m_Clips"][slot_idx]
        assert c["m_OriginalClip"]["m_PathID"] == orig_pid
        assert c["m_OverrideClip"] == {"m_FileID": 0, "m_PathID": local_pid}
        clip_name = sf.objects[local_pid].read_typetree().get("m_Name")
        assert clip_name == expected_clips[key]["m_Name"], f"{key} mismatch: {clip_name}"

    ms = sf.objects[VORTEX_MOVESET_PID].read_typetree()["_moves"]
    expected_moves = [
        ("Base.LightAttack01",  "move_brawler_2_attack_light_01", MOVE_G1_OP_L1_PID),
        ("Base.LightAttack02",  "move_brawler_2_attack_light_02", MOVE_G1_OP_L2_PID),
        ("Base.LightAttack03",  "move_jazz_attack_light_01",      MOVE_JAZZ_L1_PID),
        ("Base.LightAttack04",  "move_vortex_attack_light_04",    VORTEX_L4_MOVE_PID),
        ("Base.MediumAttack01", "move_primal_attack_medium_01",   MOVE_PRIMAL_M1_PID),
        ("Base.MediumAttack02", "move_feral_attack_medium_02",    MOVE_BONE_M2_PID),
    ]
    for idx, (st, mn, mpid) in enumerate(expected_moves):
        assert ms[idx]["_animStateName"] == st
        assert ms[idx]["_name"] == mn
        assert ms[idx]["_asset"] == {"m_FileID": 5, "m_PathID": mpid}

    plist = sf.objects[VORTEX_PREFABLIB_PID].read_typetree()["PrefabList"]
    assert any(item["Prefab"] == {"m_FileID": FX_DASH_TRAIL_FID, "m_PathID": FX_DASH_TRAIL_PID} for item in plist), (
        "fx_r_dash_trail missing from PrefabList!"
    )

    print(f"  [PASS] vortex_gs.assetbundle passed ALL P0 reload integrity checks! (PreloadTable={len(pt)}, script_types={len(st_keys)})")


def patch_vortex_bundle():
    vortex_path = ROOT / "assets_redeco" / "vortex_gs.assetbundle"
    assert vortex_path.exists(), f"Missing {vortex_path}"

    print("[*] Loading 6 donor AnimationClips...")
    donor_clips = load_donor_clips()

    print(f"\n[*] Patching Vortex bundle: {vortex_path}")
    env = UnityPy.load(str(vortex_path))
    sf = list(env.assets)[0]

    # Assert external FileIDs haven't drifted
    ext_cabs = [getattr(ext, "path", "").split("/")[-1] for ext in sf.externals]
    assert ext_cabs[FX_DASH_TRAIL_FID - 1] == "CAB-a742a3fff84aa604ba32daca2b1ea500", f"Unexpected FileID 4: {ext_cabs}"
    assert ext_cabs[5 - 1] == "CAB-47012f9f52e0ee1cac4dfad2d29a972d", f"Unexpected FileID 5 (moves): {ext_cabs}"

    # 1. Replace the 6 local melee AnimationClips in-place
    for slot_key, (local_pid, slot_idx, orig_pid, state_name) in VORTEX_CLIP_SLOTS.items():
        clip_obj = sf.objects.get(local_pid)
        assert clip_obj is not None and clip_obj.type.name == "AnimationClip"
        clip_obj.save_typetree(donor_clips[slot_key])
        print(f"  [+] Replaced local clip {local_pid} ({state_name}, slot[{slot_idx}]) -> {donor_clips[slot_key]['m_Name']}")

    # 2. Verify Fight AOC still wires slot[2,3,41,42,43,44] to those exact local clip PIDs
    aoc_obj = sf.objects[VORTEX_FIGHT_AOC_PID]
    aoc_tree = aoc_obj.read_typetree()
    assert aoc_tree.get("m_Name") == "override_Grindor_Cin_ROTF_fight"
    clips = aoc_tree["m_Clips"]
    for slot_key, (local_pid, slot_idx, orig_pid, state_name) in VORTEX_CLIP_SLOTS.items():
        assert clips[slot_idx]["m_OriginalClip"]["m_PathID"] == orig_pid, f"Slot {slot_idx} OriginalClip mismatch!"
        clips[slot_idx]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": local_pid}
    aoc_obj.save_typetree(aoc_tree)

    # 3. Update MoveSet (_moves[0..5])
    ms_obj = sf.objects[VORTEX_MOVESET_PID]
    ms_tree = ms_obj.read_typetree()
    moves = ms_tree["_moves"]
    new_move_defs = [
        (0, "Base.LightAttack01",  "move_brawler_2_attack_light_01", MOVE_G1_OP_L1_PID),
        (1, "Base.LightAttack02",  "move_brawler_2_attack_light_02", MOVE_G1_OP_L2_PID),
        (2, "Base.LightAttack03",  "move_jazz_attack_light_01",      MOVE_JAZZ_L1_PID),
        (3, "Base.LightAttack04",  "move_vortex_attack_light_04",    VORTEX_L4_MOVE_PID),
        (4, "Base.MediumAttack01", "move_primal_attack_medium_01",   MOVE_PRIMAL_M1_PID),
        (5, "Base.MediumAttack02", "move_feral_attack_medium_02",    MOVE_BONE_M2_PID),
    ]
    for idx, state_name, move_name, move_pid in new_move_defs:
        assert moves[idx]["_animStateName"] == state_name, f"MoveSet[{idx}] expected {state_name}, got {moves[idx]['_animStateName']}"
        moves[idx]["_name"] = move_name
        moves[idx]["_asset"] = {"m_FileID": 5, "m_PathID": move_pid}
        print(f"  [+] MoveSet[{idx}] ({state_name}) -> {move_name} (FileID=5, PathID={move_pid})")
    ms_tree["_moves"] = moves
    ms_obj.save_typetree(ms_tree)

    # 4. Update _overrideControllerList metadata strings cleanly
    meta_obj = sf.objects[VORTEX_AOC_META_PID]
    meta_tree = meta_obj.read_typetree()
    state_to_clipname = {
        state_name: donor_clips[slot_key]["m_Name"]
        for slot_key, (_, _, _, state_name) in VORTEX_CLIP_SLOTS.items()
    }
    for entry in meta_tree.get("_overrideControllerList", []):
        su = entry.get("StateUniqueName")
        if su in state_to_clipname:
            entry["OverrideClipName"] = state_to_clipname[su]
    meta_obj.save_typetree(meta_tree)
    print("  [+] Updated _overrideControllerList clip names metadata")

    # 5. Add fx_r_dash_trail (character_fx) to PrefabList for Bonecrusher M2
    pl_obj = sf.objects[VORTEX_PREFABLIB_PID]
    pl_tree = pl_obj.read_typetree()
    plist = pl_tree["PrefabList"]
    if not any(item["Prefab"] == {"m_FileID": FX_DASH_TRAIL_FID, "m_PathID": FX_DASH_TRAIL_PID} for item in plist):
        plist.append({"Prefab": {"m_FileID": FX_DASH_TRAIL_FID, "m_PathID": FX_DASH_TRAIL_PID}, "Amount": 1})
        pl_tree["PrefabList"] = plist
        pl_obj.save_typetree(pl_tree)
        print(f"  [+] Added fx_r_dash_trail (FileID={FX_DASH_TRAIL_FID}, PathID={FX_DASH_TRAIL_PID}) to PrefabList")
    else:
        print("  [~] fx_r_dash_trail already in PrefabList")

    # 6. Flush modified typetrees in memory before recursive PreloadTable collection
    mem_bytes = env.file.save(packer="none")
    env2 = UnityPy.load(io.BytesIO(mem_bytes))
    sf2 = list(env2.assets)[0]
    rebuild_container_preload_table(sf2)

    out_bytes = env2.file.save(packer="lz4")
    vortex_path.write_bytes(out_bytes)
    print(f"  [+] Saved {vortex_path.name} ({len(out_bytes):,} bytes)")

    verify_bundle_integrity(vortex_path, donor_clips)


def main():
    print("=== Patching Vortex Melee Combo Moveset (L1-L4, M1-M2) ===")
    patch_moves_bundle()
    patch_vortex_bundle()
    print("\n[SUCCESS] Vortex melee moveset and AnimationClips updated & verified cleanly!")


if __name__ == "__main__":
    main()
