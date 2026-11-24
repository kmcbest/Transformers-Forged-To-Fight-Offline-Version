import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json
import UnityPy
from pathlib import Path

ROOT_BL = Path(r"E:\Agent\TFTF-blender")
ROOT_GM = Path(r"E:\Agent\TFTF")

moves_env = UnityPy.load(str(ROOT_BL / "assets_netflix" / "moves.assetbundle"))
mmap = {}
for o in moves_env.objects:
    if o.type.name == "TextAsset":
        tt = o.read_typetree()
        mmap[tt.get("m_Name", "")] = (o.path_id, tt.get("m_Script", ""))

check_names = [
    "move_tactical_attack_light_01",
    "move_cheetor_attack_light_02",
    "move_military_attack_light_03",
    "move_military_attack_medium_02",
    "move_wheeljack_attack_medium_01",
    "move_kickback_attack_medium_02",
    "move_mixmaster_special_01",
    "move_bludgeon_special_02",
    "move_windblade_special_01",
    "move_sideswipe_special_02",
]

for nm in check_names:
    pid, raw = mmap[nm]
    d = json.loads(raw)
    evs = d.get("moves", {}).get("events", [])
    max_f = max([e.get("f", 0) + e.get("d", 0) for e in evs] or [0])
    print(f"\n=== {nm} (PID={pid}, max_f={max_f}) ===")
    for e in evs:
        t = e.get("type", "")
        if t in ("PropMoveEvent", "PlayPropAnimatorStateMoveEvent", "ParticleMoveEvent", "ProjectileMoveEvent", "ChainMoveEvent", "AttackWindowMoveEvent", "CharacterAudioMoveEvent"):
            print(f"  f={e.get('f',0):2d} d={e.get('d',0):2d} {t}: { {k:v for k,v in e.items() if k not in ('cc','sc','mn','dn','id','inf','tar','roc','poc','di')} }")
