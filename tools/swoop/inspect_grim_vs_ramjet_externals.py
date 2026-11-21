import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

TFTF = Path(r"E:\Agent\TFTF")
GRIM = TFTF / "extracted_apk/assets/assetpack/grimlock_gs_mp08_odr/grimlock_gs_mp08.assetbundle"
RAMJET = TFTF / "extracted_apk/assets/assetpack/ramjet_gs_deluxe2008_odr/ramjet_gs_deluxe2008.assetbundle"

for label, bp in [("Grimlock", GRIM), ("Ramjet", RAMJET)]:
    e = UnityPy.load(str(bp))
    sf = list(e.assets)[0]
    print(f"\n=== {label} Externals ===")
    for i, ext in enumerate(sf.externals, 1):
        print(f"  FileID={i}: {ext.path}")

eg = UnityPy.load(str(GRIM))
gmap = {o.path_id: o for o in eg.objects}
print("\n=== Grimlock Fireball Projectile MonoBehaviour (-4879017508623021442) ===")
print(gmap[-4879017508623021442].read_typetree())
