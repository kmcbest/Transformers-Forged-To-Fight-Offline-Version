import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        try:
            d = obj.read_typetree()
            if "PrefabList" in d:
                print(f"Found PrefabLib: {d.get('m_Name')} (PID: {obj.path_id})")
                for item in d.get("PrefabList", []):
                    pref = item.get("Prefab", {})
                    # find what prefab is
                    print(f"  Item: {pref}")
        except:
            pass
