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
    if obj.type.name == "GameObject":
        try:
            d = obj.read_typetree()
            name = d.get("m_Name", "")
            if "ramjet" in name.lower() or "deluxe" in name.lower():
                print(f"GameObject: {name} (PID: {obj.path_id})")
        except:
            pass
