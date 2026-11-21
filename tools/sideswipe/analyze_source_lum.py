import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image
import numpy as np

p = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\textures\Body_Diffuse.png")
im = np.array(Image.open(p).convert("RGB"), dtype=np.float32)
lum = im.mean(axis=2)
sat = (im.max(axis=2) - im.min(axis=2)) / np.maximum(im.max(axis=2), 1.0)

print(f"Body_Diffuse overall: mean lum = {lum.mean():.1f}, max = {lum.max():.1f}, min = {lum.min():.1f}")
armor = (lum >= 50.0) & (sat < 0.25)
print(f"Silver armor pixels ({armor.mean()*100:.1f}%): mean lum = {lum[armor].mean():.1f}, p90 = {np.percentile(lum[armor], 90):.1f}")
joint = lum < 50.0
print(f"Dark joint pixels ({joint.mean()*100:.1f}%): mean lum = {lum[joint].mean():.1f}")
