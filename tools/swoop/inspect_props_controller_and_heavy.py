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
GRIM = TFTF / "extracted_apk/assets/assetpack/grimlock_gs_mp08_odr/grimlock_gs_mp08.assetbundle"
SWOOP = ROOT / "assets_redeco/swoop_gs_deluxe2008.assetbundle"
MOVES = ROOT / "assets_redeco/moves.assetbundle"

for label, bp in [("Ramjet", RAMJET), ("Skywarp", SKYWARP), ("Grimlock", GRIM), ("Swoop", SWOOP)]:
    e = UnityPy.load(str(bp))
    print(f"\n=== {label} Props / Transform / CharacterConfig MonoBehaviours ===")
    for o in e.objects:
        if o.type.name == "MonoBehaviour":
            tt = o.read_typetree()
            if any(k in tt for k in ("_props", "TransformedScaleFactor", "_transformedScaleFactor", "_vehicleScale", "Props")):
                print(f"  MB PID={o.path_id}: keys={list(tt.keys())}")
                for k in tt:
                    if any(s in k.lower() for s in ("scale", "prop", "factor", "transform")):
                        print(f"    {k} = {tt[k]}")

print("\n=== Compare ALL events in move_heavy_grimlock vs move_heavy_starscream_shoot vs move_heavy_ramjet_donut ===")
em = UnityPy.load(str(MOVES))
for o in em.objects:
    if o.type.name == "TextAsset":
        tt = o.read_typetree()
        n = tt.get("m_Name", "")
        if n in ("move_heavy_grimlock", "move_heavy_starscream_shoot", "move_heavy_ramjet_donut", "move_heavy_swoop"):
            d = json.loads(tt["m_Script"])
            print(f"\n--- {n} ---")
            for ev in d["moves"]["events"]:
                print(f"  f={ev.get('f'):2d} d={ev.get('d'):2d} {ev.get('type'):30s} sm={ev.get('sm','')} en={ev.get('en','')} p={ev.get('p','')} pn={ev.get('pn','')} sn={ev.get('sn','')} st={ev.get('State','')}")
