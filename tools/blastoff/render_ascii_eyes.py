import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image
import numpy as np

SRC = Path(r"O:\agent\transformers-fall-of-cybertron-combaticons\textures")
im = Image.open(SRC / "rb_blastoff_head_cust_matinst.jpg")
arr = np.array(im)

print("Left eye (Y=201..220, X=190..225):")
for y in range(201, 221):
    line = f"{y:3d} "
    for x in range(191, 225):
        r, g, b = arr[y, x].tolist()
        # Is it eye visor?
        # In original texture, eye visor is dark violet/purple or dark slit
        # Frame is tan/brown (r ~ 130-170, g ~ 130-160, b ~ 130-160)
        is_frame = (r > 120 and g > 115 and abs(r - g) < 20 and abs(r - b) < 25)
        is_visor = not is_frame and (b > g + 10 or (r < 100 and g < 100 and b < 100))
        line += "##" if is_visor else ".."
    print(line)

print("\nRight eye (Y=201..220, X=288..322):")
for y in range(201, 221):
    line = f"{y:3d} "
    for x in range(288, 322):
        r, g, b = arr[y, x].tolist()
        is_frame = (r > 120 and g > 115 and abs(r - g) < 20 and abs(r - b) < 25)
        is_visor = not is_frame and (b > g + 10 or (r < 100 and g < 100 and b < 100))
        line += "##" if is_visor else ".."
    print(line)
