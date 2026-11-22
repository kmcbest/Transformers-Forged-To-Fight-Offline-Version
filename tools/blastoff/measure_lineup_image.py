import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image
import numpy as np

img_path = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\5d3b25eb-29f0-44ca-b379-77e4974af4f3\.user_uploaded\media_1795357145861_83266dc0.jpg")
im = Image.open(img_path)
print(f"Image size: {im.size}")

# Let's inspect the layout of the image
# From left to right:
# Brawl: x roughly 0..250
# Blastoff: x roughly 250..420
# Onslaught: x roughly 420..650
# Vortex: x roughly 650..820
# Swindle: x roughly 820..1000

# Let's measure the head top Y and foot bottom Y for each of the 5 robots!
# In PIL: y=0 is top, y=im.size[1] is bottom.
arr = np.array(im)
# Find the floor ground line:
# Look at the bottom of their feet
print(f"Image height: {arr.shape[0]}, width: {arr.shape[1]}")
