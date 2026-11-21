import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import numpy as np
from PIL import Image

TDIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\swoop\01_master\textures")
for name in ("Tx_Swoop_D.png", "Tx_Swoop_D_RGB.png", "Tx_Swoop_S.png", "Tx_Swoop_N.png"):
    im = Image.open(TDIR / name)
    arr = np.array(im)
    print(f"{name}: mode={im.mode} size={im.size} shape={arr.shape}")
    if arr.ndim == 3 and arr.shape[2] == 4:
        a = arr[:, :, 3]
        print(f"  Alpha min={a.min()} max={a.max()} mean={a.mean():.1f} (<250 count={(a<250).sum()}, >0&<255={( (a>0)&(a<255) ).sum()})")
        if (a < 250).sum() > 0:
            ys, xs = np.where(a < 250)
            print(f"  Alpha<250 bbox: x=[{xs.min()},{xs.max()}], y=[{ys.min()},{ys.max()}]")
    if name == "Tx_Swoop_S.png":
        for ch in range(arr.shape[2]):
            c = arr[:, :, ch]
            print(f"  S ch[{ch}]: min={c.min()} max={c.max()} mean={c.mean():.1f}")
        # Check S at Robot Visor px=[888:951, 648:672] and Bird Head [600:685, 5:96]
        print("  S at Robot visor [655:665, 915:935] mean RGB:", arr[655:665, 915:935].mean(axis=(0,1)))
        print("  S at Bird cluster (603..663, 7..30) mean RGB:", arr[10:25, 610:650].mean(axis=(0,1)))
        print("  S at Bird cluster (662..685, 39..95) mean RGB:", arr[45:90, 665:682].mean(axis=(0,1)))
    if name == "Tx_Swoop_D.png":
        # Check pixel values at Robot visor & Bird clusters
        print("  D at Robot visor [655:665, 915:935] mean:", arr[655:665, 915:935].mean(axis=(0,1)))
        print("  D at Robot visor [642:650, 950:985] mean:", arr[642:650, 950:985].mean(axis=(0,1)))
        print("  D at Bird (603..663, 7..30) mean:", arr[10:25, 610:650].mean(axis=(0,1)))
        print("  D at Bird (662..685, 39..95) mean:", arr[45:90, 665:682].mean(axis=(0,1)))
