import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from PIL import Image
import numpy as np

img = Image.open(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\textures\Body_Lights.png").convert("RGBA")
arr = np.array(img)
print("RGBA shape:", arr.shape)
print("Top-left pixel:", arr[0, 0])
print("Center pixel:", arr[32, 64])
print("Bottom-right pixel:", arr[63, 127])
print("Unique colors count:", len(np.unique(arr.reshape(-1, 4), axis=0)))

# Let's save a preview to artifacts
img.save(r"C:\Users\Xiangli496\.gemini\antigravity\brain\1ddfb8b4-479e-45f9-9da6-2409640018a4\source_body_lights_preview.png")
print("Saved preview to artifacts.")
