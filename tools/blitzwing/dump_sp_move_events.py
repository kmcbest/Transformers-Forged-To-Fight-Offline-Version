import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json
from pathlib import Path
import UnityPy

MOVES_BUNDLE = Path(r"E:\Agent\TFTF-blender\assets_redeco\moves.assetbundle")
env = UnityPy.load(str(MOVES_BUNDLE))

target_moves = [
    "move_mixmaster_special_01",
    "move_bludgeon_special_02",
    "move_windblade_special_01",
    "move_sideswipe_special_02",
]

for o in env.objects:
    if o.type.name == "TextAsset":
        t = o.read()
        if t.m_Name in target_moves:
            raw = t.m_Script if isinstance(t.m_Script, str) else t.m_Script.decode("utf-8", errors="replace")
            mv = json.loads(raw)["moves"]
            evts = mv.get("events", [])
            max_f = max([e.get("f", 0) + e.get("d", 0) for e in evts] or [0])
            print(f"\n=== {t.m_Name} (events={len(evts)}, max_f={max_f}) ===")
            for e in evts:
                et = e.get("type", "")
                if any(k in et for k in ("Prop", "Particle", "Projectile", "Audio", "AttackWindow", "Hit")):
                    short = {k: v for k, v in e.items() if k in ("type", "f", "d", "p", "en", "pn", "sn", "ref", "atr", "po", "ro")}
                    print(f"  {short}")
