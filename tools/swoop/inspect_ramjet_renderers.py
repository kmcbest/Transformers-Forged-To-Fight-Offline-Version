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
        data = obj.read()
        name = getattr(data, "m_Name", getattr(data, "name", ""))
        if "00" in name or "01" in name or "wing" in name.lower():
            print(f"GameObject: {name}")
    elif obj.type.name in ["MeshRenderer", "SkinnedMeshRenderer"]:
        data = obj.read()
        name = getattr(data, "m_Name", getattr(data, "name", ""))
        print(f"{obj.type.name}: {name}")
