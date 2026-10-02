from pathlib import Path

p = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets")
for f in p.glob("**/*anim*.assetbundle"):
    print(f.relative_to(p), f.stat().st_size)
