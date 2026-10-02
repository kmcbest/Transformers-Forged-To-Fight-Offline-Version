import sys
import UnityPy
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = Path(r"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "AssetBundle":
        data = obj.read()
        print(f"Container count: {len(data.m_Container)}")
        for i, (k, v) in enumerate(data.m_Container[:25]):
            print(f"  [{i}] '{k}'")
        break
