import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

TFTF = Path(r"E:\Agent\TFTF")
GRIM = TFTF / "extracted_apk/assets/assetpack/grimlock_gs_mp08_odr/grimlock_gs_mp08.assetbundle"
SKYWARP = TFTF / "extracted_apk/assets/assetpack/skywarp_gs_leader2015_odr/skywarp_gs_leader2015.assetbundle"

for label, bp, gname in [
    ("Grimlock Fireball", GRIM, "projectile_grimlock_fireball"),
    ("Skywarp/Starscream Missile", SKYWARP, "projectile_starscream_missile"),
]:
    e = UnityPy.load(str(bp))
    omap = {o.path_id: o for o in e.objects}
    for o in e.objects:
        if o.type.name == "GameObject" and o.read_typetree().get("m_Name") == gname:
            go = o.read_typetree()
            print(f"\n=== {label} ('{gname}', PID={o.path_id}) ===")
            for c in go["m_Component"]:
                co = omap[c["component"]["m_PathID"]]
                ct = co.read_typetree()
                print(f"  Comp {co.type.name} (PID={co.path_id}):")
                if co.type.name == "MonoBehaviour":
                    for k in ("_speed", "_homingStrength", "_homingSpeed", "_aimAtTarget", "_hitDetectionRadius", "_radius", "_gravity", "_arcHeight", "_moves", "PrefabList"):
                        if k in ct:
                            print(f"    {k} = {ct[k]}")
                elif co.type.name == "Transform":
                    print(f"    pos={ct['m_LocalPosition']}, rot={ct['m_LocalRotation']}")
