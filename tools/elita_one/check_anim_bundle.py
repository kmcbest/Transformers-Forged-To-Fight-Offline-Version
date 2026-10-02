from pathlib import Path

p = Path(r"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle")
print("Exists:", p.exists())
if p.exists():
    print("Size:", p.stat().st_size)
