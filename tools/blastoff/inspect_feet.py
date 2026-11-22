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

# Let's inspect the crops visually and find feet / ground line
# Let's save marked images with lines showing head and feet
import matplotlib.pyplot as plt

# Let's find foot contact for each bot:
# Look at feet Y around 130..150
# Brawl feet:
# Blast Off feet:
# Onslaught feet:
print("Foot contact Y:")
for name, xc in [("Brawl", 145), ("BlastOff", 348), ("Onslaught", 540), ("Vortex", 745), ("Swindle", 905)]:
    # Look from Y=120 to Y=170
    # In each bot, foot contact with ground shadow
    # Let's print pixel colors from y=125 to 155
    print(f"\n{name} column x={xc}:")
    for y in range(125, 155, 3):
        print(f"  Y={y}: {arr[y, xc, :3].tolist()}")
