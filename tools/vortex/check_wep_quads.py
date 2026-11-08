import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from PIL import Image
import numpy as np

wep = Image.open(r"E:\Agent\TFTF-blender\3rd-party-models\vortex\textures\wep.jpg")
arr = np.array(wep)
print(f"wep.jpg shape: {arr.shape}")
# Check corners of wep.jpg: is there any 256x256 or 128x128 empty region?
# Let's check 4 quadrants of wep.jpg
q0 = arr[0:256, 0:256] # top-left
q1 = arr[0:256, 256:512] # top-right
q2 = arr[256:512, 0:256] # bottom-left
q3 = arr[256:512, 256:512] # bottom-right
print(f"q0 max={q0.max()}, mean={q0.mean():.1f}")
print(f"q1 max={q1.max()}, mean={q1.mean():.1f}")
print(f"q2 max={q2.max()}, mean={q2.mean():.1f}")
print(f"q3 max={q3.max()}, mean={q3.mean():.1f}")
