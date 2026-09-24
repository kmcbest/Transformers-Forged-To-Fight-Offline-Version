# -*- coding: utf-8 -*-
import sys
from pathlib import Path
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

tex_dir = Path(r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\textures")

for name in ["rb_demolishor_normspec_cust_e_mat_inst.jpeg", "rb_demolishor_n.jpeg", "rb_demolishor_e.jpeg"]:
    p = tex_dir / name
    img = Image.open(p)
    arr = np.array(img)
    print(f"\n=== {name} ({arr.shape}) ===")
    for c, c_name in enumerate(["Red", "Green", "Blue"]):
        ch = arr[:, :, c]
        print(f"  {c_name}: min={ch.min()}, max={ch.max()}, mean={ch.mean():.1f}, std={ch.std():.1f}")
