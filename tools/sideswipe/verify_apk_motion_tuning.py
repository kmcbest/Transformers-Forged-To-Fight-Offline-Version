import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zipfile
import io
from pathlib import Path
import UnityPy

apk_path = Path(r"E:\Agent\TFTF-blender\build\Transformers-9.2-offline-blender2.apk")

with zipfile.ZipFile(apk_path, "r") as zf:
    data = zf.read("assets/assetpack/sideswipe_cin_rotf_odr/sideswipe_cin_rotf.assetbundle")

env = UnityPy.load(io.BytesIO(data))
sf = list(env.assets)[0]

# Check PlayerReferences
for o in sf.objects.values():
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "SpecialStagePrefab" in tt:
            ssp = tt.get("SpecialStagePrefab")
            vsp = tt.get("VictoryStagePrefab")
            print("APK Inside PlayerReferences:")
            print("  SpecialStagePrefab:", ssp)
            print("  VictoryStagePrefab:", vsp)
            assert ssp.get("m_PathID") == 3256447252977910551, "SpecialStagePrefab mismatch!"
            assert vsp.get("m_PathID") == 1484321543804849475, "VictoryStagePrefab mismatch!"
            break

# Check Fight AOC
FIGHT_AOC_PID = -2047393535863576714
fight_aoc = sf.objects[FIGHT_AOC_PID].read_typetree()
clips = fight_aoc.get("m_Clips", [])
print("\nAPK Inside Fight AOC:")
print("  Slot 04 (S1):", clips[4].get("m_OverrideClip"))
print("  Slot 05 (S2):", clips[5].get("m_OverrideClip"))
print("  Slot 31 (S3):", clips[31].get("m_OverrideClip"))
print("  Slot 32 (S3 React):", clips[32].get("m_OverrideClip"))
print("  Slot 39 (Victory):", clips[39].get("m_OverrideClip"))
print("  Slot 40 (Victory Idle):", clips[40].get("m_OverrideClip"))
print("  Slot 44 (M2):", clips[44].get("m_OverrideClip"))
print("  Slot 58 (Heavy):", clips[58].get("m_OverrideClip"))

assert clips[4]["m_OverrideClip"]["m_PathID"] == -3664095140934993801 # Drift S1
assert clips[5]["m_OverrideClip"]["m_PathID"] == 868105726138923071 # Cheetor S1
assert clips[31]["m_OverrideClip"]["m_PathID"] == -4693390210307202245 # Optimus S3
assert clips[32]["m_OverrideClip"]["m_PathID"] == -7999335457178782659 # Optimus S3 HitReact
assert clips[39]["m_OverrideClip"]["m_PathID"] == -3196363985734342445 # Drift Victory
assert clips[40]["m_OverrideClip"]["m_PathID"] == 3303065432090877960 # Drift Victory Idle
assert clips[44]["m_OverrideClip"]["m_PathID"] == -1929738649458782990 # Cheetor M2
assert clips[58]["m_OverrideClip"]["m_PathID"] == -4177997624914663523 # Sideswipe Car Heavy

# Check MoveSet
MOVESET_PID = -5126079019749064592
moveset = sf.objects[MOVESET_PID].read_typetree()
moves = moveset.get("_moves", [])
print("\nAPK Inside MoveSet:")
print(f"  Move 05 (M2): {moves[5].get('_name')} -> {moves[5].get('_asset')}")
print(f"  Move 06 (S1): {moves[6].get('_name')} -> {moves[6].get('_asset')}")
print(f"  Move 07 (S2): {moves[7].get('_name')} -> {moves[7].get('_asset')}")
print(f"  Move 43 (Heavy): {moves[43].get('_name')} -> {moves[43].get('_asset')}")

assert moves[5]["_name"] == "move_cheetor_attack_medium_02"
assert moves[6]["_name"] == "move_drift_special_01"
assert moves[7]["_name"] == "move_cheetor_special_01"
assert moves[43]["_name"] == "move_heavy_car_donut"

print("\n[ALL PASS] The APK contains 100% verified tuned moveset & stages!")
