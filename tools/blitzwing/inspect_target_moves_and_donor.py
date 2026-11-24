import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json
import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")

# 1. Check Megatron donor externals and FileIDs
meg_path = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_gs_leader2015_odr" / "megatron_gs_leader2015.assetbundle"
env_meg = UnityPy.load(str(meg_path))
for cab_name, cab_file in env_meg.file.files.items():
    if hasattr(cab_file, "externals"):
        print("=== Megatron Externals (1-based FileIDs) ===")
        for idx, ext in enumerate(cab_file.externals, start=1):
            print(f"  FileID={idx}: path='{ext.path}' name='{ext.name}'")

# Check Megatron Fight AOC clip count and slot names
for o in env_meg.objects:
    if o.path_id == -7755666207738536548:  # override_Megatron_GS_Leader2015_fight
        aoc = o.read_typetree()
        print(f"\n=== Megatron Fight AOC: {aoc['m_Name']} clips={len(aoc['m_Clips'])} ===")
        for i, c in enumerate(aoc["m_Clips"]):
            orig = c["m_OriginalClip"]
            ovr = c["m_OverrideClip"]
            if i in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 41, 42, 43, 44, 45, 50, 51, 52, 53, 54, 58, 59, 60, 61, 62, 63, 64, 65, 66):
                print(f"  slot[{i:02d}] orig=({orig['m_FileID']},{orig['m_PathID']}) -> ovr=({ovr['m_FileID']},{ovr['m_PathID']})")

# 2. Check target moves in assets_netflix/moves.assetbundle
moves_path = ROOT / "assets_netflix" / "moves.assetbundle"
env_moves = UnityPy.load(str(moves_path))
target_moves = {
    "move_attackRanged_handGun_left_XL_01",
    "move_attackRanged_handGun_left_XL_02",
    "move_attackRanged_handGun_left_XL_03B",
    "move_mixmaster_special_01",
    "move_bludgeon_special_02",
    "move_windblade_special_01",
    "move_sideswipe_special_02",
}
print("\n=== Target Moves in moves.assetbundle ===")
for o in env_moves.objects:
    if o.type.name == "TextAsset":
        tt = o.read_typetree()
        name = tt.get("m_Name", "")
        if any(k in name.lower() for k in ("prowl", "cheetor", "rhinox", "wheeljack", "kickback")) and ("light" in name.lower() or "medium" in name.lower()):
            print(f"  MELEE: {name} PID={o.path_id}")
        if name in target_moves:
            print(f"\n  SPECIAL/RANGED: {name} PID={o.path_id}")
            data = json.loads(tt["m_Script"])
            evs = data.get("moves", {}).get("events", [])
            for ev in evs:
                t = ev.get("type", "")
                if t in ("PropMoveEvent", "PlayPropAnimatorStateMoveEvent", "ProjectileMoveEvent", "ParticleMoveEvent", "CharacterAudioMoveEvent", "TransformMoveEvent"):
                    print(f"    f={ev.get('f')} d={ev.get('d')} {t}: { {k: v for k, v in ev.items() if k not in ('cc','sc','mn','dn','id','inf','tar')} }")
