import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

for name in ["starsaber_gs_leader2014", "swoop_gs_deluxe2008"]:
    p = Path(f"assets_redeco/{name}.assetbundle")
    if not p.exists():
        print(f"Not found: {p}")
        continue
    env = UnityPy.load(str(p))
    for obj in env.objects:
        if obj.type.name == "AssetBundle":
            tt = obj.read_typetree()
            print(f"=== {name} AssetBundle ===")
            print("m_Name:", tt.get("m_Name"))
            print("m_AssetBundleName:", tt.get("m_AssetBundleName"))
            for k, v in tt.get("m_Container", []):
                print(f"  Container key: '{k}' -> asset pathID: {v['asset']['m_PathID']}")
