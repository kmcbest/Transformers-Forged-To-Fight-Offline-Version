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

# Let's inspect columns corresponding to the center of each bot's head:
# Brawl: center around x=145
# Blast Off: center around x=348
# Onslaught: center around x=540
# Vortex: center around x=745
# Swindle: center around x=905

points = {
    "Brawl": 145,
    "BlastOff": 348,
    "Onslaught": 540,
    "Vortex": 745,
    "Swindle": 905,
}

# The floor background color is roughly (125, 115, 100) or brownish-grey
# Let's find for each x center: where does the head top begin (first non-background pixel from y=0 down)
# and where does the foot touch the ground (around y=130..160)

for name, xc in points.items():
    col_strip = arr[:, xc-5:xc+6, :3]
    # mean color along strip
    col_mean = col_strip.mean(axis=1)
    
    # Background color at top of image (y=5..20)
    bg_top = arr[10, xc, :3]
    
    # Measure diff from bg
    diff = np.linalg.norm(col_mean - bg_top, axis=1)
    
    # Find head top (where diff > 25, ignoring red text for Blast Off)
    # Note: Blast Off has red text around y=20..40
    y_start = 50 if name == "BlastOff" else 20
    head_y = None
    for y in range(y_start, 120):
        if diff[y] > 20:
            head_y = y
            break
            
    print(f"{name:10s} (x={xc}): Head top Y = {head_y}")

# Let's also check shoulder tops
# Brawl shoulders are at x=105 and x=185
# Blast Off shoulders are at x=310 and x=385
# Onslaught shoulders are at x=505 and x=575
print("\nChecking shoulders:")
for name, xs in [("Brawl_L", 108), ("Brawl_R", 182), ("BlastOff_L", 310), ("BlastOff_R", 380), ("Onslaught_L", 505), ("Onslaught_R", 575)]:
    col_strip = arr[:, xs-3:xs+4, :3].mean(axis=1)
    diff = np.linalg.norm(col_strip - arr[10, xs, :3], axis=1)
    sy = None
    for y in range(25, 120):
        if diff[y] > 20:
            sy = y
            break
    print(f"  {name:12s} (x={xs}): Top Y = {sy}")
