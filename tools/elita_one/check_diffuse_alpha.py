from PIL import Image
import numpy as np

for name in ["cha_elita_one_main_a.png", "cha_elita_one_vh_a.png"]:
    p = f"toolchain/unity_build_project/Assets/ElitaOne/{name}"
    img = Image.open(p)
    print(f"{name}: mode={img.mode}, size={img.size}")
    if img.mode == "RGBA":
        arr = np.array(img)
        alpha = arr[:, :, 3]
        min_a, max_a, mean_a = alpha.min(), alpha.max(), alpha.mean()
        print(f"  Alpha min={min_a}, max={max_a}, mean={mean_a:.1f}")
        num_transparent = (alpha < 255).sum()
        print(f"  Pixels with alpha < 255: {num_transparent} / {alpha.size} ({num_transparent/alpha.size*100:.1f}%)")
