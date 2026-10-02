import sys
import UnityPy
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = Path(r"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle")
env = UnityPy.load(str(bundle_path))

count = 0
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read()
        name = getattr(data, 'name', getattr(data, 'm_Name', ''))
        if any(k in name.lower() for k in ["agile", "teamselect", "victory"]):
            print(f"Clip: '{name}'")
            count += 1
            if count >= 20: break
