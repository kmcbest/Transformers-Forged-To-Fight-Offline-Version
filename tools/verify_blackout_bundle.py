import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

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
for pid in [991101, 991102, 991103, 991104, 991105, 991106]:
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
assert moves[7]['_name'] == "move_blackout_special_02"
assert moves[44]['_name'] == "move_heavy_plane_shoot"

# 6. Check PlayerReferences
pref = sf.objects[4809715625580256617].read_typetree()
print(f"VictoryStagePrefab: {pref.get('VictoryStagePrefab')}")
assert pref.get('VictoryStagePrefab') == {'m_FileID': 7, 'm_PathID': 7184980468553159185}, "VictoryStagePrefab wrong!"

# 7. Check Textures
main_tex = sf.objects[-527106191474585865].read()
print(f"Main texture image: {main_tex.m_Width}x{main_tex.m_Height}")

print("[+] All bundle integrity checks passed with flying colors!")
