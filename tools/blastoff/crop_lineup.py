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
arr = np.array(im)

# Let's save 5 crops:
# 1. Brawl (leftmost)
# 2. Blast Off (second)
# 3. Onslaught (third)
# 4. Vortex (fourth)
# 5. Swindle (fifth)

crops = {
    "brawl": (40, 0, 240, 205),
    "blastoff": (260, 0, 420, 205),
    "onslaught": (470, 0, 610, 205),
    "vortex": (660, 0, 820, 205),
    "swindle": (820, 0, 990, 205),
}

for name, box in crops.items():
    cropped = im.crop(box)
    cropped.save(f"renders/blastoff/crop_{name}.png")

print("Saved crops.")
