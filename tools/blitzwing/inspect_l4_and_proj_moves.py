import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json
import UnityPy
from pathlib import Path

ROOT_BL = Path(r"E:\Agent\TFTF-blender")
moves_env = UnityPy.load(str(ROOT_BL / "assets_netflix" / "moves.assetbundle"))
mmap = {o.read_typetree().get("m_Name", ""): (o.path_id, o.read_typetree().get("m_Script", ""))
        for o in moves_env.objects if o.type.name == "TextAsset"}

for nm in ("move_tactical_attack_light_04", "move_military_attack_medium_02", "move_wheeljack_attack_medium_01", "move_kickback_attack_medium_02", "move_special_bullet_fire", "move_special_bullet_explode", "move_projectile_sideswipe_missile_fire", "move_projectile_sideswipe_missile_explode"):
    if nm in mmap:
        pid, raw = mmap[nm]
        data = json.loads(raw)
        print(f"\n=== {nm} (PID={pid}) ===")
        for ev in data["moves"]["events"]:
            print(f"  f={ev.get('f',0):2d} d={ev.get('d',0):2d} {ev.get('type')}: { {k:v for k,v in ev.items() if k not in ('cc','sc','mn','dn','id','inf','tar','roc','poc','di','ccs')} }")
