from PIL import Image
import numpy as np

img = Image.open("tools/elita_one/arcee_extracted/cha_arcee_gs_deluxe2014_main_a.png")
print("Arcee diffuse mode:", img.mode, "size:", img.size)
if img.mode == "RGBA":
    arr = np.array(img)
    alpha = arr[:, :, 3]
    print(f"Arcee alpha: min={alpha.min()}, max={alpha.max()}, mean={alpha.mean():.1f}")
