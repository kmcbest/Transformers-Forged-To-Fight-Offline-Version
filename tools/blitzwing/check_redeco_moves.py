import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

ROOT_BL = Path(r"E:\Agent\TFTF-blender")
nf = UnityPy.load(str(ROOT_BL / "assets_netflix" / "moves.assetbundle"))
rd = UnityPy.load(str(ROOT_BL / "assets_redeco" / "moves.assetbundle"))

nf_names = {o.read_typetree().get("m_Name", ""): o.path_id for o in nf.objects if o.type.name == "TextAsset"}
rd_names = {o.read_typetree().get("m_Name", ""): o.path_id for o in rd.objects if o.type.name == "TextAsset"}

print(f"Netflix moves: {len(nf_names)}, Redeco moves: {len(rd_names)}")
extra = set(rd_names.keys()) - set(nf_names.keys())
print(f"Extra moves in assets_redeco/moves.assetbundle: {sorted(extra)}")
for nm in sorted(extra):
    print(f"  {nm}: PID={rd_names[nm]}")
