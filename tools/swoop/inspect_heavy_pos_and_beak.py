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

MOVES = ROOT / "assets_redeco/moves.assetbundle"
RAMJET = TFTF / "extracted_apk/assets/assetpack/ramjet_gs_deluxe2008_odr/ramjet_gs_deluxe2008.assetbundle"
SKYWARP = TFTF / "extracted_apk/assets/assetpack/skywarp_gs_leader2015_odr/skywarp_gs_leader2015.assetbundle"

em = UnityPy.load(str(MOVES))
print("=== All Heavy ProjectileMoveEvents ===")
for o in em.objects:
    if o.type.name == "TextAsset":
        tt = o.read_typetree()
        n = tt.get("m_Name", "")
        if ("heavy" in n or "ranged" in n or "special_01_ramjet" in n) and any(k in n for k in ("ramjet", "starscream", "skywarp", "thundercracker", "jetfire", "grimlock", "swoop", "megatron", "shockwave")):
            s = tt["m_Script"]
            if isinstance(s, bytes):
                s = s.decode("utf-8", errors="replace")
            d = json.loads(s)
            projs = [ev for ev in d["moves"]["events"] if ev.get("type") in ("ProjectileMoveEvent", "ParticleMoveEvent") and ("ignition" in ev.get("pn","") or "muzzle" in ev.get("pn","") or ev.get("type") == "ProjectileMoveEvent")]
            if projs:
                print(f"\n[{n}]:")
                for ev in projs:
                    print(f"  f={ev.get('f')} {ev.get('type')} pn={ev.get('pn')} ref={ev.get('ref')} atr={ev.get('atr')} po={ev.get('po')}")

print("\n=== Check Ramjet vs Skywarp Robot Hips pos in prefab ===")
for label, bp, rname in [("Ramjet", RAMJET, "Ramjet_GS_Deluxe2008"), ("Skywarp", SKYWARP, "Skywarp_GS_Leader2015")]:
    e = UnityPy.load(str(bp))
    omap = {o.path_id: o for o in e.objects}
    for o in e.objects:
        if o.type.name == "GameObject" and o.read_typetree().get("m_Name") == "Hips":
            g = o.read_typetree()
            tr_pid = next(c["component"]["m_PathID"] for c in g["m_Component"] if omap[c["component"]["m_PathID"]].type.name == "Transform")
            tr = omap[tr_pid].read_typetree()
            print(f"  {label} Hips: pos={tr['m_LocalPosition']}, rot={tr['m_LocalRotation']}")
            break
