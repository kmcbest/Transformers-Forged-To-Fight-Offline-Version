import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from PIL import Image
import numpy as np

img = Image.open(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\textures\Body_Lights.png")
print("Body_Lights.png format:", img.format, img.size, img.mode)
arr = np.array(img)
print("Array shape:", arr.shape)
print("Non-zero pixels:", np.count_nonzero(arr))
print("Min:", arr.min(), "Max:", arr.max(), "Mean:", arr.mean())

# Check where it is non-zero
if arr.ndim == 3:
    lum = arr.mean(axis=2)
else:
    lum = arr
ys, xs = np.where(lum > 10)
print(f"Luminance > 10 bounds: Y in [{ys.min()}, {ys.max()}], X in [{xs.min()}, {xs.max()}]")
print(f"Sample pixel at Y=ys.mean, X=xs.mean: {arr[int(ys.mean()), int(xs.mean())]}")
