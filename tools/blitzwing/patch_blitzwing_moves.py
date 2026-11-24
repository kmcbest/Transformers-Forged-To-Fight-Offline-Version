import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import copy
import json
from pathlib import Path
import UnityPy

ROOT = Path(__file__).resolve().parents[2]
MOVES_BUNDLE = ROOT / "assets_redeco" / "moves.assetbundle"

# Donor MoveData PIDs in moves.assetbundle
DONOR_MIXMASTER_S1_PID = 4499258370306887049
DONOR_BLUDGEON_S2_PID  = -2946028093795316441
DONOR_WINDBLADE_S1_PID = 8938417396863993065
DONOR_SIDESWIPE_S2_PID = 446359208563810113

# Dedicated deterministic PathIDs for Blitzwing custom SP moves
BW_TANK_S1_PID = -8888888888888888901
BW_TANK_S2_PID = -8888888888888888902
BW_JET_S1_PID  = -8888888888888888903
BW_JET_S2_PID  = -8888888888888888904


def rewrite_ref_dict(d, path_map):
    if isinstance(d, dict) and "r" in d and isinstance(d["r"], str):
        r = d["r"]
        for old_sub, new_sub in path_map:
            if old_sub in r:
                r = r.replace(old_sub, new_sub)
        d["r"] = r


def clone_and_transform_move(moves_file, src_pid, dst_pid, new_name, event_filter_fn, extra_events=None):
    src_reader = moves_file.objects[src_pid]
    tt = copy.deepcopy(src_reader.read_typetree())
    tt["m_Name"] = new_name
    raw = tt["m_Script"]
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    data = json.loads(raw)
    mv = data["moves"]
    mv["id"] = new_name
    if "m_Name" in mv:
        mv["m_Name"] = new_name

    new_events = []
    for ev in mv.get("events", []):
        ev = copy.deepcopy(ev)
        res = event_filter_fn(ev, new_name)
        if res is None:
            continue
        res["mn"] = new_name
        new_events.append(res)

    if extra_events:
        for ex in extra_events:
            new_events.append(ex)

    new_events.sort(key=lambda x: x.get("f", 0))
    mv["events"] = new_events
    data["moves"] = mv
    tt["m_Script"] = json.dumps(data)

    # Insert or update object safely in moves_file
    if dst_pid in moves_file.objects:
        dst_obj = moves_file.objects[dst_pid]
        dst_obj.save_typetree(tt)
    else:
        dst_obj = copy.copy(src_reader)
        dst_obj.path_id = dst_pid
        moves_file.objects[dst_pid] = dst_obj
        dst_obj.save_typetree(tt)

    return new_name, dst_pid, len(new_events)


def main():
    print(f"Loading {MOVES_BUNDLE}...")
    env = UnityPy.load(str(MOVES_BUNDLE))
    moves_file = list(env.file.files.values())[0]

    for req_pid in (DONOR_MIXMASTER_S1_PID, DONOR_BLUDGEON_S2_PID, DONOR_WINDBLADE_S1_PID, DONOR_SIDESWIPE_S2_PID):
        assert req_pid in moves_file.objects, f"Missing donor PID {req_pid}!"

    # 1. Tank S1 (Mixmaster S1, NO sword)
    def filter_tank_s1(ev, new_name):
        if ev.get("type") == "PlayPropAnimatorStateMoveEvent":
            return None
        path_map = [
            (
                "character_model/Reference/Hips/Spine/Spine1/sheildgun/Reference/COG/cannon/fx",
                "character_model/Reference/Hips/Spine/Spine1",
            ),
        ]
        rewrite_ref_dict(ev.get("ref"), path_map)
        rewrite_ref_dict(ev.get("atr"), path_map)
        if ev.get("pn") == "fx_p_mixmaster_gun_fire_special":
            ev["pn"] = "fx_p_tank_muzzle_small"
        return ev

    # 2. Tank S2 (Bludgeon S2, draws sword during S2)
    def filter_tank_s2(ev, new_name):
        if ev.get("type") == "PlayPropAnimatorStateMoveEvent":
            return None
        if ev.get("type") == "PropMoveEvent":
            return None
        if ev.get("pn") == "fx_p_tank_muzzle_flash":
            ev["pn"] = "fx_p_tank_muzzle_small"
        elif ev.get("pn") == "fx_p_tank_shell_hit":
            ev["pn"] = "fx_p_missile_projectile_impact"
        return ev

    tank_s2_sword_evt = {
        "p": "sword",
        "inf": False,
        "type": "PropMoveEvent",
        "tar": 0,
        "sc": [],
        "mn": "move_blitzwing_tank_s2",
        "dn": "PropMoveEvent--bw_tank_s2_sword",
        "en": True,
        "cc": [],
        "id": -9910001,
        "d": 93,
        "f": 0,
    }

    # 3. Jet S1 (Windblade S1, draws sword during S1)
    def filter_jet_s1(ev, new_name):
        if ev.get("type") in ("PropMoveEvent", "PlayPropAnimatorStateMoveEvent"):
            return None
        path_map = [
            ("/RightHand/Sword/cha_windblade_gs_deluxe2014_wpns_sword", "/RightHand/sword/cha_megatron_gs_leader2015_wpns_cannon_right"),
            ("/RightHand/Sword/Reference", "/RightHand/sword/Reference"),
            ("/RightHand/Sword", "/RightHand/sword"),
        ]
        rewrite_ref_dict(ev.get("ref"), path_map)
        rewrite_ref_dict(ev.get("atr"), path_map)
        if ev.get("pn") == "fx_p_windblade_radius":
            ev["pn"] = "fx_p_hit_punch_sparks_special"
        return ev

    jet_s1_sword_evt = {
        "p": "sword",
        "inf": False,
        "type": "PropMoveEvent",
        "tar": 0,
        "sc": [],
        "mn": "move_blitzwing_jet_s1",
        "dn": "PropMoveEvent--bw_jet_s1_sword",
        "en": True,
        "cc": [],
        "id": -9910002,
        "d": 58,
        "f": 0,
    }

    # 4. Jet S2 (Sideswipe S2, NO sword)
    def filter_jet_s2(ev, new_name):
        if ev.get("type") in ("PropMoveEvent", "PlayPropAnimatorStateMoveEvent"):
            return None
        path_map = [
            (
                "character_model/Reference/Hips/Spine/Spine1/rocketBase/Reference/COG/Hinge/FX",
                "character_model/Reference/Hips/Spine/Spine1/RightShoulder",
            ),
        ]
        rewrite_ref_dict(ev.get("ref"), path_map)
        rewrite_ref_dict(ev.get("atr"), path_map)
        return ev

    created = [
        clone_and_transform_move(moves_file, DONOR_MIXMASTER_S1_PID, BW_TANK_S1_PID, "move_blitzwing_tank_s1", filter_tank_s1),
        clone_and_transform_move(moves_file, DONOR_BLUDGEON_S2_PID,  BW_TANK_S2_PID, "move_blitzwing_tank_s2", filter_tank_s2, [tank_s2_sword_evt]),
        clone_and_transform_move(moves_file, DONOR_WINDBLADE_S1_PID, BW_JET_S1_PID,  "move_blitzwing_jet_s1",  filter_jet_s1,  [jet_s1_sword_evt]),
        clone_and_transform_move(moves_file, DONOR_SIDESWIPE_S2_PID, BW_JET_S2_PID,  "move_blitzwing_jet_s2",  filter_jet_s2),
    ]
    for nm, pid, cnt in created:
        print(f"  [+] {nm} (PID={pid}) -> {cnt} events")

    # Update AssetBundle container
    ab_obj = next(o for o in env.objects if o.type.name == "AssetBundle")
    ab_tree = ab_obj.read_typetree()
    container = [c for c in ab_tree.get("m_Container", []) if "move_blitzwing_" not in c[0]]
    for nm, pid, _ in created:
        container.append([
            f"assets/bundles/movedata/{nm}.txt",
            {"preloadIndex": 0, "preloadSize": 0, "asset": {"m_FileID": 0, "m_PathID": pid}},
        ])
    ab_tree["m_Container"] = container
    ab_obj.save_typetree(ab_tree)

    saved = env.file.save(packer="lz4")
    MOVES_BUNDLE.write_bytes(saved)

    # Verification pass on saved bundle
    ver_env = UnityPy.load(str(MOVES_BUNDLE))
    names = {o.read().m_Name: o.path_id for o in ver_env.objects if o.type.name == "TextAsset"}
    assert "move_lifeline_special_01" in names and "move_lifeline_special_02" in names, "Lost Lifeline moves!"
    for nm, pid, _ in created:
        assert names.get(nm) == pid, f"Verification failed for {nm}"
    assert len(names) >= 956, f"Expected >= 956 moves, got {len(names)}"
    print(f"[✓] Verified & saved {MOVES_BUNDLE.name} ({len(saved)} bytes, total TextAssets={len(names)})")


if __name__ == "__main__":
    main()
