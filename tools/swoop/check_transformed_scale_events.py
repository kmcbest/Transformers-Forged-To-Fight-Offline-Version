import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json
import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
MOVES = ROOT / "assets_redeco/moves.assetbundle"
SWOOP = ROOT / "assets_redeco/swoop_gs_deluxe2008.assetbundle"
TFTF = Path(r"E:\Agent\TFTF")
SKYWARP = TFTF / "extracted_apk/assets/assetpack/skywarp_gs_leader2015_odr/skywarp_gs_leader2015.assetbundle"

em = UnityPy.load(str(MOVES))
print("=== ALL moves with TransformedStateScaleEvent (heavy/special) ===")
for o in em.objects:
    if o.type.name == "TextAsset":
        tt = o.read_typetree()
        n = tt.get("m_Name", "")
        if "heavy" in n:
            d = json.loads(tt["m_Script"])
            evs = d["moves"]["events"]
            tscales = [e for e in evs if e.get("type") == "TransformedStateScaleEvent"]
            tforms = [e for e in evs if e.get("type") == "TransformMoveEvent"]
            pstates = [e for e in evs if e.get("type") == "PlayPropAnimatorStateMoveEvent"]
            if tforms:
                print(f"  {n:35s} | Trans={[(e['f'], e['d'], e.get('State')) for e in tforms]} | TScale={[(e['f'], e['d'], e.get('sm')) for e in tscales]} | PlayProp={[(e['f'], e.get('sn')) for e in pstates]}")

print("\n=== Check Ramjet_GS_Deluxe2008_01 Material vs Shader in Showroom / Battle ===")
# Also inspect Character.cs / PropsController Scale factor in gamedata / Skywarp vs Ramjet
es = UnityPy.load(str(SWOOP))
omap = {o.path_id: o for o in es.objects}
# Check ALL MonoBehaviours attached to transformed (7693429312995989932) and cha_ramjet_gs_deluxe2008_01 (4244665296975761270)
for gpid in (7693429312995989932, 4244665296975761270):
    g = omap[gpid].read_typetree()
    print(f"\nGO '{g['m_Name']}' comps:")
    for c in g["m_Component"]:
        co = omap[c["component"]["m_PathID"]]
        print(f"  {co.type.name} PID={co.path_id}")
