import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np
from pathlib import Path
from PIL import Image

base = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm")
for fn in ["cha_strongarm_vh_a.png", "cha_strongarm_vh_NM.png", "cha_strongarm_vh_Emission.png", "cha_strongarm_vh_tform_misc_RAOE.png"]:
    p = base / fn
    arr = np.array(Image.open(p).convert("RGBA"))
    print(f"\n=== {fn} {arr.shape} ===")
    for i, ch in enumerate(["R", "G", "B", "A"]):
        print(f"  {ch}: min={arr[:,:,i].min():3d}, p50={np.percentile(arr[:,:,i],50):5.1f}, p95={np.percentile(arr[:,:,i],95):5.1f}, max={arr[:,:,i].max():3d}, mean={arr[:,:,i].mean():5.1f}")
    if "RAOE" in fn:
        em = arr[:,:,2] > 0
        print(f"  Emissive B>0 px={em.sum()} ({em.mean()*100:.2f}%), B>0 values: min={arr[em,2].min() if em.any() else 0}, max={arr[em,2].max() if em.any() else 0}")

# Check how bright/saturated red/cyan are on cha_strongarm_vh_a.png at lightbar region
a = np.array(Image.open(base / "cha_strongarm_vh_a.png").convert("RGB"))
H, W, _ = a.shape
# Bottom-right lightbar region in strongarm_vehicle.png: x=[0.59..0.90], y=[0.64..0.79]
lb = a[int(H*0.64):int(H*0.79), int(W*0.59):int(W*0.90)]
print(f"\nLightbar RGB max=({lb[:,:,0].max()}, {lb[:,:,1].max()}, {lb[:,:,2].max()})")
# Roof top-right smudge region: x=[0.84..1.0], y=[0.10..0.33]
rf = a[int(H*0.10):int(H*0.33), int(W*0.84):W]
print(f"Roof top-right min=({rf[:,:,0].min()}, {rf[:,:,1].min()}, {rf[:,:,2].min()}), max=({rf[:,:,0].max()}, {rf[:,:,1].max()}, {rf[:,:,2].max()}), mean=({rf[:,:,0].mean():.1f}, {rf[:,:,1].mean():.1f}, {rf[:,:,2].mean():.1f})")
