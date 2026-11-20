import json
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

def verify_all():
    print("=== [1/3] VERIFYING BLACKOUT ASSETBUNDLE ===")
    b_path = Path("assets_redeco/blackout_cin_tf.assetbundle")
    assert b_path.exists(), f"Missing {b_path}"
    env_b = UnityPy.load(str(b_path))
    sf_b = list(env_b.assets)[0]

    # 1. AnimationClip
    clip_obj = sf_b.objects.get(991107)
    assert clip_obj is not None, "Missing AnimationClip 991107"
    clip_tree = clip_obj.read_typetree()
    name = clip_tree.get("m_Name")
    duration = clip_tree.get("m_MuscleClip", {}).get("m_StopTime", 0)
    bindings_count = len(clip_tree.get("m_ClipBindingConstant", {}).get("genericBindings", []))
    print(f"  [AnimationClip 991107] name='{name}', duration={duration}s, bindings={bindings_count}")
    assert duration == 2.0, f"Expected 2.0s duration, got {duration}"
    assert bindings_count == 130, f"Expected 130 genericBindings, got {bindings_count}"

    # 2. Fight AOC Slot 4
    aoc_obj = sf_b.objects.get(259380691726149969)
    assert aoc_obj is not None, "Missing Fight AOC"
    aoc_tree = aoc_obj.read_typetree()
    slot4 = aoc_tree["m_Clips"][4]
    slot4_override = slot4.get("m_OverrideClip", {}).get("m_PathID")
    print(f"  [Fight AOC Slot 4] OverrideClip PathID={slot4_override}")
    assert slot4_override == 991107, f"Slot 4 should point to 991107, got {slot4_override}"

    # 3. AudioClip grindor_special_1
    audio_obj = None
    for o in sf_b.objects.values():
        if o.type.name == "AudioClip" and o.read_typetree().get("m_Name") == "grindor_special_1":
            audio_obj = o
            break
    assert audio_obj is not None, "Missing grindor_special_1 AudioClip"
    atree = audio_obj.read_typetree()
    print(f"  [AudioClip grindor_special_1] len={atree.get('m_Length')}s, res={atree.get('m_Resource')}")
    assert atree.get("m_Length", 0) > 2.3, f"Expected audio length > 2.3s, got {atree.get('m_Length')}"
    assert atree.get("m_Resource", {}).get("m_Size") == 19712, "Resource size mismatch"

    # 4. Main PrefabLib contains Jetfire Projectile roots
    plib_obj = sf_b.objects.get(-5353390358171322875)
    assert plib_obj is not None, "Missing main PrefabLib"
    ptree = plib_obj.read_typetree()
    plib_pids = {p["Prefab"]["m_PathID"] for p in ptree.get("PrefabList", [])}
    print(f"  [Main PrefabLib] items={len(ptree.get('PrefabList', []))}")

    # Check root GameObjects exist
    target_names = {"projectile_jetfire_sp1_bullet", "fx_p_jetfire_special_projectile", "fx_p_jetfire_projectile_impact"}
    found_targets = {}
    for pid, obj in sf_b.objects.items():
        if obj.type.name == "GameObject":
            gname = obj.read_typetree().get("m_Name")
            if gname in target_names:
                found_targets[gname] = pid
                assert pid in plib_pids, f"Root {gname} (PID {pid}) not registered in PrefabLib"
    assert len(found_targets) == 3, f"Expected 3 target roots, found {found_targets}"
    print(f"  [Injected Roots Verified] {found_targets}")

    print("\n=== [2/3] VERIFYING MOVES ASSETBUNDLE ===")
    m_path = Path("assets_redeco/moves.assetbundle")
    assert m_path.exists(), f"Missing {m_path}"
    env_m = UnityPy.load(str(m_path))
    sf_m = list(env_m.assets)[0]

    s1_obj = sf_m.objects.get(-8888888888888888891)
    assert s1_obj is not None, "Missing move_blackout_special_01 TextAsset"
    s1_tree = s1_obj.read_typetree()
    assert s1_tree.get("m_Name") == "move_blackout_special_01"
    s1_json = json.loads(s1_tree.get("m_Script"))
    events = s1_json.get("moves", {}).get("events", [])
    print(f"  [move_blackout_special_01] Total events={len(events)}")

    # Check audio event
    audio_events = [e for e in events if e.get("type") == "CharacterAudioMoveEvent" and e.get("en") == "gen_special_1"]
    assert len(audio_events) >= 1, "Missing gen_special_1 CharacterAudioMoveEvent"
    print(f"  [Audio Event Verified] frame={audio_events[0].get('f')}, sound={audio_events[0].get('en')}")

    # Check invulnerability event
    inv_events = [e for e in events if e.get("type") == "InvulnerabilityMoveEvent"]
    assert len(inv_events) >= 1, "Missing InvulnerabilityMoveEvent"
    print(f"  [Invulnerability Verified] duration={inv_events[0].get('d')}")

    # Check projectiles
    proj_events = [e for e in events if e.get("type") == "ProjectileMoveEvent"]
    assert len(proj_events) == 2, f"Expected 2 ProjectileMoveEvents, got {len(proj_events)}"
    for idx, pev in enumerate(proj_events):
        print(f"  [Projectile #{idx+1}] frame={pev.get('f')}, pn={pev.get('pn')}, hd={pev.get('hd')}")
        assert pev.get("pn") == "projectile_jetfire_sp1_bullet", f"Bad projectile name: {pev.get('pn')}"
        assert pev.get("of") == "", f"Bad of: {pev.get('of')}"
        assert pev.get("oe") == "", f"Bad oe: {pev.get('oe')}"

    # First projectile must be blockable (u=False, idx=0) and aligned to arm (y=8.0)
    assert proj_events[0].get("f") == 10, f"Expected first projectile at frame 10, got {proj_events[0].get('f')}"
    assert proj_events[0]["hd"].get("u") is False, "First projectile must be blockable"
    assert proj_events[0]["hd"].get("idx") == 0, "First projectile idx must be 0"
    assert proj_events[0]["po"]["o"]["y"] == 8.0, f"Expected y=8.0 for first projectile, got {proj_events[0]['po']['o']['y']}"

    # Second projectile must be unblockable (u=True, idx=100)
    assert proj_events[1].get("f") == 32, f"Expected second projectile at frame 32, got {proj_events[1].get('f')}"
    assert proj_events[1]["hd"].get("u") is True, "Second projectile must be unblockable"
    assert proj_events[1]["hd"].get("idx") == 100, "Second projectile idx must be 100"

    # Verify AssetBundle container
    for o in sf_m.objects.values():
        if o.type.name == "AssetBundle":
            c = o.read_typetree().get("m_Container", [])
            s1_entry = [item for item in c if "move_blackout_special_01" in item[0]]
            assert len(s1_entry) == 1, "Missing move_blackout_special_01 in container"
            print(f"  [AssetBundle Container] entry verified: {s1_entry[0][0]}")

    print("\n[ALL CHECKS PASSED] Both assetbundles verified successfully!")

if __name__ == "__main__":
    verify_all()
