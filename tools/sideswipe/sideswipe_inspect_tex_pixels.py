import sys
import os
import numpy as np
from PIL import Image

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

tex_dir = r"C:\Users\Xiangli496\.gemini\antigravity\brain\1ddfb8b4-479e-45f9-9da6-2409640018a4\scratch\textures"

for f in sorted(os.listdir(tex_dir)):
    if f.endswith('.png'):
        p = os.path.join(tex_dir, f)
        im = Image.open(p)
        arr = np.array(im)
        print(f"Texture: {f:<25} Size: {im.size} Mode: {im.mode} Shape: {arr.shape} Min: {arr.min()} Max: {arr.max()} Mean: {arr.mean():.1f}")
