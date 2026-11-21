import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import numpy as np
from PIL import Image

TDIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\swoop\01_master\textures")
s = np.array(Image.open(TDIR / "Tx_Swoop_S.png").convert("RGB"), dtype=np.float32)
d = np.array(Image.open(TDIR / "Tx_Swoop_D_RGB.png").convert("RGB"), dtype=np.float32)
ws = np.array(Image.open(TDIR / "Tx_Swoop_Weapon_S.png").convert("RGB"), dtype=np.float32)

for name, arr in (("Tx_Swoop_S", s), ("Tx_Swoop_Weapon_S", ws)):
    print(f"=== {name} ===")
    for i, ch in enumerate(("R", "G", "B")):
        c = arr[:, :, i]
        print(f"  {ch}: mean={c.mean():.1f} p10={np.percentile(c,10):.1f} p50={np.percentile(c,50):.1f} p90={np.percentile(c,90):.1f} min={c.min():.0f} max={c.max():.0f}")

# Check S values on Gold beak vs Blue chest vs Red helmet vs Silver wings
gold = (d[:,:,0] > 130) & (d[:,:,1] > 110) & (d[:,:,2] < 70)
blue = (d[:,:,2] > d[:,:,0] + 25) & (d[:,:,2] > 90)
red  = (d[:,:,0] > d[:,:,1] + 40) & (d[:,:,0] > 90)
silver = (d[:,:,0] > 115) & (np.abs(d[:,:,0] - d[:,:,2]) < 12)
dark = (d.mean(axis=2) < 60) & (np.abs(d[:,:,0] - d[:,:,2]) < 15)
for label, m in (("Gold", gold), ("Blue", blue), ("Red", red), ("Silver", silver), ("DarkMetal", dark)):
    if m.sum() > 0:
        print(f"  {label:10s} (n={m.sum():6d}): D_mean={d[m].mean(axis=0).round(1)} | S_mean={s[m].mean(axis=0).round(1)}")
