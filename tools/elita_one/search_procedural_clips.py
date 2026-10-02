import sys
import UnityPy
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = Path(r"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "AssetBundle":
        data = obj.read()
        print(f"Total container assets: {len(data.m_Container)}")
        for k, v in data.m_Container:
            lower = k.lower()
            if any(w in lower for w in ["agile", "female", "teamselect", "idle", "attacklight", "heavy"]):
                if "proxy" not in lower:
                    print(f"  '{k}'")
        break
