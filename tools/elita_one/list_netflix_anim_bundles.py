from pathlib import Path

p = Path(r"E:\Agent\TFTF\assets_netflix")
for f in p.glob("*anim*"):
    print(f.name, f.stat().st_size)
