import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image
import numpy as np

img_path = Path(r"renders/blastoff/trio_comparison.png")
im = Image.open(img_path)
arr = np.array(im)

# Let's inspect the vertical span of each character:
# In trio_comparison.png:
# Brawl: x roughly 0..170
# Blast Off: x roughly 200..360
# Onslaught: x roughly 400..580

# Ground line:
# Look at Brawl's foot: around y=150
# Blast Off's foot: around y=145
# Onslaught's foot: around y=150

# Head top:
# Brawl head top (excluding top smoke pipes):
# Brawl smoke pipes top:
# Blast Off head top:
# Onslaught head top:
# Onslaught back cannons top:

# Let's find for each bot the exact Y coordinate of:
# 1. Head top (crown)
# 2. Shoulder top
# 3. Ground / foot base

print("Measuring in trio_comparison:")

# 1. Blast Off:
# Head is at x ~ 285 in trio image
# Let's check vertical line at x=285
for y in range(40, 160):
    px = arr[y, 285, :3].tolist()
    # Check when it enters head
    # Blast off head is tan/brown [120..180, 80..140, 50..100]
    # background is [128, 117, 98]
    # print if distinctive
    pass

# Let's save an annotated image with horizontal lines at:
# - Onslaught Head
# - Brawl Head
# - Blast Off Head
# - Ground
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 4), dpi=150)
ax.imshow(arr)
# Let's add grid
ax.set_xticks(range(0, arr.shape[1], 25))
ax.set_yticks(range(0, arr.shape[0], 10))
ax.grid(color='cyan', linestyle='--', linewidth=0.5, alpha=0.7)
plt.savefig("renders/blastoff/trio_grid.png", bbox_inches='tight')
print("Saved renders/blastoff/trio_grid.png")
