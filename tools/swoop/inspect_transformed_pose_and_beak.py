import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json
import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
TFTF = Path(r"E:\Agent\TFTF")

RAMJET = TFTF / "extracted_apk/assets/assetpack/ramjet_gs_deluxe2008_odr/ramjet_gs_deluxe2008.assetbundle"
SKYWARP = TFTF / "extracted_apk/assets/assetpack/skywarp_gs_leader2015_odr/skywarp_gs_leader2015.assetbundle"
MOVES = ROOT / "assets_redeco/moves.assetbundle"

def check_transformed_tr(label, bp):
    e = UnityPy.load(str(bp))
    omap = {o.path_id: o for o in e.objects}
    for o in e.objects:
        if o.type.name == "GameObject" and o.read_typetree().get("m_Name") == "transformed":
            go = o.read_typetree()
            tr_pid = next(c["component"]["m_PathID"] for c in go["m_Component"] if omap[c["component"]["m_PathID"]].type.name == "Transform")
            tr = omap[tr_pid].read_typetree()
            father_pid = tr["m_Father"]["m_PathID"]
            father_go = omap[omap[father_pid].read_typetree()["m_GameObject"]["m_PathID"]].read_typetree()["m_Name"]
            print(f"{label} 'transformed' (GO={o.path_id}, parent='{father_go}'):")
            print(f"  pos={tr['m_LocalPosition']}, rot={tr['m_LocalRotation']}, scale={tr['m_LocalScale']}")

check_transformed_tr("Ramjet", RAMJET)
check_transformed_tr("Skywarp", SKYWARP)

# Check some ProjectileMoveEvents in moves.assetbundle to see ref / atr / po conventions
em = UnityPy.load(str(MOVES))
print("\n=== Sample ProjectileMoveEvents ===")
for o in em.objects:
    if o.type.name == "TextAsset":
        tt = o.read_typetree()
        n = tt.get("m_Name", "")
        if n in ("move_heavy_starscream_shoot", "move_heavy_grimlock", "move_ranged_ramjet_01", "move_special_01_ramjet", "move_special_02_grimlock"):
            s = tt["m_Script"]
            if isinstance(s, bytes):
                s = s.decode("utf-8", errors="replace")
            d = json.loads(s)
            for ev in d["moves"]["events"]:
                if ev.get("type") in ("ProjectileMoveEvent", "ParticleMoveEvent", "PlayPropAnimatorStateMoveEvent", "TransformMoveEvent"):
                    print(f"  [{n}] f={ev.get('f')} d={ev.get('d')} type={ev.get('type')} pn={ev.get('pn','')} sn={ev.get('sn','')} ref={ev.get('ref')} atr={ev.get('atr')} po={ev.get('po')}")
