import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
SS_BUNDLE_PATH = ROOT / "assets_redeco" / "sideswipe_cin_rotf.assetbundle"

print("=== Verifying Sideswipe Bundle Special Moves ===")
env = UnityPy.load(str(SS_BUNDLE_PATH))

# 1. Check MoveSet
moveset = None
fight_aoc = None
matinee_aoc = None

FIGHT_AOC_PID = -2047393535863576714
MATINEE_AOC_PID = -2768898539375720182
MOVESET_PID = -5126079019749064592

for obj in env.objects:
    if obj.path_id == MOVESET_PID:
        moveset = obj.read_typetree()
    elif obj.path_id == FIGHT_AOC_PID:
        fight_aoc = obj.read_typetree()
    elif obj.path_id == MATINEE_AOC_PID:
        matinee_aoc = obj.read_typetree()

assert moveset is not None, "MoveSet not found!"
assert fight_aoc is not None, "Fight AOC not found!"
assert matinee_aoc is not None, "MatineeAOC not found!"

# Check Move 06 (S1) and Move 07 (S2)
moves = moveset["_moves"]
print(f"Move 06: name={moves[6].get('_name')}, asset={moves[6].get('_asset')}")
print(f"Move 07: name={moves[7].get('_name')}, asset={moves[7].get('_asset')}")
assert moves[6].get("_name") == "move_barricade_special_01", "Move 06 is not move_barricade_special_01!"
assert moves[7].get("_name") == "move_arcee_special_02", "Move 07 is not move_arcee_special_02!"

# Check Fight AOC Slot 4 and Slot 5
clips = fight_aoc["m_Clips"]
print(f"Fight AOC Slot 04 (S1): orig={clips[4].get('m_OriginalClip')} over={clips[4].get('m_OverrideClip')}")
print(f"Fight AOC Slot 05 (S2): orig={clips[5].get('m_OriginalClip')} over={clips[5].get('m_OverrideClip')}")
assert clips[4]["m_OverrideClip"]["m_PathID"] == -2570347918429811085, "Slot 04 override is not Barricade S1!"
assert clips[5]["m_OverrideClip"]["m_PathID"] == 1304560969345666953, "Slot 05 override is not Arcee S2!"

# Check MatineeAOC
for item in matinee_aoc["_overrideControllerList"]:
    sh = item.get("StateHash")
    if sh == 1671240305:
        print(f"MatineeAOC S1: '{item.get('OverrideClipName')}'")
        assert item.get("OverrideClipName") == "barricade_cin_attackSpecial_01"
    elif sh == -90944565:
        print(f"MatineeAOC S2: '{item.get('OverrideClipName')}'")
        assert item.get("OverrideClipName") == "Arcee_Normal_attackSpecial_02"

# Check that Arcee S2 clip exists locally in bundle
all_pids = [o.path_id for o in env.objects]
assert 1304560969345666953 in all_pids, "Arcee S2 clip not found in bundle!"
print(f"Arcee S2 clip {1304560969345666953} verified in bundle objects!")
print("[✓] ALL CHECKS PASSED PERFECTLY!")
