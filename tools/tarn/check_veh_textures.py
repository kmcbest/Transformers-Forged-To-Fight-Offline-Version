import sys
from pathlib import Path
import numpy as np
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

VEH_DIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Tarn\03_vehicle_preprocessed_tftf")
for name in ["tarn_veh_base_graded.png", "tarn_veh_emissive_mask.png", "tarn_veh_normal_kabam.png", "tarn_veh_normal_std.png", "tarn_veh_raoe.png"]:
    p = VEH_DIR / name
    img = Image.open(p)
    arr = np.array(img)
    print(f"{name:28s}: mode={img.mode:4s} size={img.size} min={arr.min(axis=(0,1)).tolist()} max={arr.max(axis=(0,1)).tolist()} mean={np.round(arr.mean(axis=(0,1)),1).tolist()}")
    if "raoe" in name:
        nz = (arr[..., 2] > 0).mean() * 100
        print(f"  RAOE B>0 ratio: {nz:.2f}%, B max={arr[...,2].max()}, B p99={np.percentile(arr[...,2], 99):.1f}")
