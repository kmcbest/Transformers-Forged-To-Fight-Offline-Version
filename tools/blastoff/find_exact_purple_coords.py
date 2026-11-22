import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image
import numpy as np
from collections import deque

SRC = Path(r"O:\agent\transformers-fall-of-cybertron-combaticons\textures")

for fname in [
    "rb_blastoff_chest_cust_matinst.jpg",
    "rb_blastoff_legs_cust_matinst.jpg",
    "rb_blastoff_head_cust_matinst.jpg",
    "rb_blastoff_armlo_cust_matinst.jpg",
    "rb_blastoff_armup_cust_matinst.jpg",
    "vh_blastoff_cust_matinst.jpg",
]:
    arr = np.array(Image.open(SRC / fname).convert("RGB"), dtype=np.float32)
    h, w, _ = arr.shape
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    mask = (b > g + 10) & (b > r * 0.85) & (b > 35)
    # Find connected components (8-conn via coarse 4px grid for speed)
    step = 4
    cm = mask.reshape(h//step, step, w//step, step).any(axis=(1,3))
    ch, cw = cm.shape
    seen = np.zeros_like(cm, dtype=bool)
    comps = []
    for cy in range(ch):
        for cx in range(cw):
            if cm[cy, cx] and not seen[cy, cx]:
                q = deque([(cy, cx)])
                seen[cy, cx] = True
                pts = []
                while q:
                    y, x = q.popleft()
                    pts.append((x, y))
                    for dy in (-1,0,1):
                        for dx in (-1,0,1):
                            ny, nx = y+dy, x+dx
                            if 0 <= ny < ch and 0 <= nx < cw and cm[ny, nx] and not seen[ny, nx]:
                                seen[ny, nx] = True
                                q.append((ny, nx))
                xs = [p[0]*step for p in pts]
                ys = [p[1]*step for p in pts]
                if len(pts) >= 2:
                    comps.append((len(pts), min(xs), min(ys), max(xs)+step, max(ys)+step))
    comps.sort(reverse=True)
    print(f"\n=== {fname} ({w}x{h}) top components ===")
    for n, x0, y0, x1, y1 in comps[:18]:
        sub = arr[y0:y1, x0:x1]
        sm = mask[y0:y1, x0:x1]
        mrgb = sub[sm].mean(axis=0).round(0) if sm.any() else [0,0,0]
        print(f"  cells={n:4d} box=({x0:4d}, {y0:4d}, {x1:4d}, {y1:4d}) meanRGB={mrgb}")
