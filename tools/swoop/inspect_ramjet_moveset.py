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
            name = d.get("m_Name", "")
            if "_moves" in d:
                print(f"Found MoveSet: {name} (PID: {obj.path_id})")
                moves = d.get("_moves", [])
                print(f"  Count: {len(moves)}")
                for i, m in enumerate(moves):
                    an = m.get("_animStateName", "")
                    mn = m.get("_name", "")
                    asset = m.get("_asset", {})
                    if "heavy" in mn.lower() or "heavy" in an.lower():
                        print(f"    Slot {i}: {an} -> {mn} (Asset: {asset})")
            if "_categories" in d or "_audioEvents" in d:
                print(f"Found Audio: {name} (PID: {obj.path_id})")
        except:
            pass
