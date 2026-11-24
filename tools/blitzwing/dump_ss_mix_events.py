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

for target in ("move_mixmaster_special_01", "move_sideswipe_special_02"):
    for o in env.objects:
        if o.type.name == "TextAsset":
            t = o.read()
            if t.m_Name == target:
                raw = t.m_Script if isinstance(t.m_Script, str) else t.m_Script.decode("utf-8", errors="replace")
                mv = json.loads(raw)["moves"]
                print(f"\n=== {t.m_Name} (events={len(mv.get('events', []))}) ===")
                for e in mv.get("events", []):
                    et = e.get("type", "")
                    if any(k in et for k in ("Prop", "Particle", "Projectile", "Audio", "AttackWindow", "Hit")):
                        print(" ", {k: v for k, v in e.items() if k in ("type", "f", "d", "p", "en", "pn", "sn", "ref", "atr", "po", "ro")})
