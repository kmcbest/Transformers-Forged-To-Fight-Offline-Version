import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import numpy as np
import UnityPy
from pathlib import Path

bundle_path = Path("assets_redeco/blackout_cin_tf.assetbundle")
print(f"[*] Reloading bundle: {bundle_path}...")
env = UnityPy.load(str(bundle_path))
bf = list(env.files.values())[0]
sf = list(env.assets)[0]

# 1. Check CAB
cabs = [k for k in bf.files.keys() if k.startswith("CAB-")]
print(f"Found CAB files: {cabs}")
assert any("blackout2026cin" in c for c in cabs), "CAB string not updated!"

# 2. Check script_types sorting
skeys = [(s.local_serialized_file_index, s.local_identifier_in_file) for s in sf.script_types]
assert skeys == sorted(skeys), "script_types is not sorted ascending!"
print(f"[*] script_types sorted correctly: {len(skeys)} entries")

# 3. Check injected AnimationClips
for pid in [991101, 991102, 991103, 991104, 991105, 991106, 991107]:
    assert pid in sf.objects, f"Missing injected clip PID {pid}"
    clip_name = sf.objects[pid].read_typetree().get("m_Name")
    print(f"[*] Injected clip {pid}: {clip_name}")

# 4. Check Fight AOC
fight_aoc = sf.objects[259380691726149969].read_typetree()
clips = fight_aoc.get("m_Clips", [])
print(f"Fight AOC clips: {len(clips)}")
print(f"  Slot 2 (L1): {clips[2]['m_OverrideClip']}")
print(f"  Slot 3 (L2): {clips[3]['m_OverrideClip']}")
print(f"  Slot 41 (L3): {clips[41]['m_OverrideClip']}")
print(f"  Slot 43 (L4): {clips[43]['m_OverrideClip']}")
print(f"  Slot 42 (M1): {clips[42]['m_OverrideClip']}")
print(f"  Slot 44 (M2): {clips[44]['m_OverrideClip']}")
print(f"  Slot 58 (Heavy): {clips[58]['m_OverrideClip']}")
print(f"  Slot 4 (S1): {clips[4]['m_OverrideClip']}")
print(f"  Slot 5 (S2): {clips[5]['m_OverrideClip']}")
print(f"  Slot 39 (Victory): {clips[39]['m_OverrideClip']}")
print(f"  Slot 40 (Victory Idle): {clips[40]['m_OverrideClip']}")

assert clips[2]['m_OverrideClip']['m_PathID'] == 991101, "Slot 2 (L1) mismatch!"
assert clips[3]['m_OverrideClip']['m_PathID'] == 991102, "Slot 3 (L2) mismatch!"
assert clips[41]['m_OverrideClip']['m_PathID'] == 991103, "Slot 41 (L3) mismatch!"
assert clips[43]['m_OverrideClip']['m_PathID'] == 991104, "Slot 43 (L4) mismatch!"
assert clips[42]['m_OverrideClip']['m_PathID'] == 991105, "Slot 42 (M1) mismatch!"
assert clips[44]['m_OverrideClip']['m_PathID'] == 991106, "Slot 44 (M2) mismatch!"
assert clips[58]['m_OverrideClip']['m_PathID'] == -7224602046215420873, "Slot 58 (Heavy missile) mismatch!"
assert clips[4]['m_OverrideClip']['m_PathID'] == 991107, "Slot 4 (Galvatron S2 -> S1) mismatch!"
assert clips[5]['m_OverrideClip']['m_PathID'] == 5129418086538677414, "Slot 5 (Grindor S2) mismatch!"

# 4.5. Check grafted Galvatron native purple projectile_blackout_energy_bullet & PrefabLib
pl = sf.objects[-5353390358171322875].read_typetree().get("PrefabList", [])
pl_names = {}
for p in pl:
    fid, pid = p["Prefab"]["m_FileID"], p["Prefab"]["m_PathID"]
    if fid == 0 and pid in sf.objects:
        pl_names[sf.objects[pid].read_typetree().get("m_Name", "")] = pid
assert "projectile_blackout_energy_bullet" in pl_names, "PrefabLib missing projectile_blackout_energy_bullet!"
for fx_n in [
    "fx_p_blackout_charge_up", "fx_p_blackout_energy_ball",
    "fx_p_blackout_blast_streaks", "fx_p_blackout_blast_discharge", "fx_p_blackout_large_blast"
]:
    assert fx_n in pl_names, f"PrefabLib missing {fx_n}!"
# Verify all grafted FX materials have Galvatron's native purple/violet palette
for pid, o in sf.objects.items():
    if o.type.name == "Material":
        mt = o.read_typetree()
        if "blackout" in mt.get("m_Name", "").lower() and "cha_" not in mt.get("m_Name", "").lower():
            cols = dict(mt.get("m_SavedProperties", {}).get("m_Colors", []))
            em = cols.get("_emissive_intensity_col", {})
            if em:
                assert em.get("b", 0) > 0.9 and (em.get("b", 0) - em.get("g", 0)) > 0.2, f"Material {mt['m_Name']} not native Galvatron purple: {em}"
print(f"[+] Verified Galvatron native purple projectile & 5 S1 FX prefabs in PrefabLib!")

# 5. Check MoveSet
moveset = sf.objects[-2282744758651308026].read_typetree()
moves = moveset.get("_moves", [])
print(f"MoveSet moves: {len(moves)}")
print(f"  move[0] (L1): {moves[0]['_name']}")
print(f"  move[1] (L2): {moves[1]['_name']}")
print(f"  move[2] (L3): {moves[2]['_name']}")
print(f"  move[3] (L4): {moves[3]['_name']}")
print(f"  move[4] (M1): {moves[4]['_name']}")
print(f"  move[5] (M2): {moves[5]['_name']}")
print(f"  move[6] (S1): {moves[6]['_name']}")
print(f"  move[7] (S2): {moves[7]['_name']}")
print(f"  move[44] (Heavy): {moves[44]['_name']}")

assert moves[0]['_name'] == "move_megatronus_attack_light_01"
assert moves[1]['_name'] == "move_megatronus_attack_light_02"
assert moves[2]['_name'] == "move_megatronus_attack_light_03"
assert moves[3]['_name'] == "move_megatronus_attack_light_04"
assert moves[4]['_name'] == "move_megatronus_attack_medium_01"
assert moves[5]['_name'] == "move_megatronus_attack_medium_02"
assert moves[6]['_name'] == "move_blackout_special_01"
assert moves[7]['_name'] == "move_grindor_special_02"
assert moves[44]['_name'] == "move_heavy_plane_shoot"

# 5.5. Verify move_blackout_special_01 in moves.assetbundle fires projectile_blackout_energy_bullet
m_sf = list(UnityPy.load("assets_redeco/moves.assetbundle").assets)[0]
s1_data = json.loads(m_sf.objects[-8888888888888888891].read_typetree()["m_Script"])
proj_events = [e for e in s1_data["moves"]["events"] if e.get("type") == "ProjectileMoveEvent"]
assert len(proj_events) > 0 and all(e["pn"] == "projectile_blackout_energy_bullet" for e in proj_events), f"S1 projectile mismatch: {proj_events}"
print(f"move_blackout_special_01 projectile verified: {[e['pn'] for e in proj_events]}")

# 6. Check PlayerReferences
pref = sf.objects[4809715625580256617].read_typetree()
print(f"VictoryStagePrefab: {pref.get('VictoryStagePrefab')}")
assert pref.get('VictoryStagePrefab') == {'m_FileID': 7, 'm_PathID': 7184980468553159185}, "VictoryStagePrefab wrong!"

# 7. Check Textures (verify recolored dark gunmetal grey vs Grindor)
main_tex = sf.objects[-527106191474585865].read()
arr = np.array(main_tex.image.convert("RGB"), dtype=np.float32)
mean_rgb = arr.mean(axis=(0, 1))
print(f"Main texture image: {main_tex.m_Width}x{main_tex.m_Height}, mean_RGB={mean_rgb.round(1).tolist()}")
assert mean_rgb.mean() < 85.0, f"Main texture too bright ({mean_rgb})!"

print("[+] All bundle integrity checks passed with flying colors!")
