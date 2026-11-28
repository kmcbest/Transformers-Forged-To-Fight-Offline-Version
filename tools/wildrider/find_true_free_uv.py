import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np

ROOT = Path(r"E:\Agent\TFTF-blender")
WR_DIR = ROOT / "3rd-party-models" / "WildRider"
TEX_D = WR_DIR / "textures" / "Tx_Wildrider_D.png"
TEX_S = WR_DIR / "textures" / "Tx_Wildrider_S.png"
NPZ = ROOT / "scratch" / "wildrider_uv_dump.npz"

d = np.load(NPZ)
uv_wr = d["uv_wr"]   # loops (3*N_tris, 2)
uv_gun = d["uv_gun"] # loops (3*N_tris, 2)
uvs_all = np.vstack([uv_wr, uv_gun])

w, h = 1024, 1024
mask_img = Image.new("L", (w, h), 0)
draw = ImageDraw.Draw(mask_img)

# Rasterize ALL triangles (note: verify polys are triangles or dump indices; all in Alliance FBX might be quads or tris!)
# Wait: earlier wr loops=48636, polys=16212 -> 48636 / 16212 = 3.000! gun loops=1962, polys=654 -> 1962 / 654 = 3.000! Every poly is a triangle!
tris = uvs_all.reshape((-1, 3, 2))
for tri in tris:
    pts = [(float(tri[i, 0] * w), float((1.0 - tri[i, 1]) * h)) for i in range(3)]
    draw.polygon(pts, fill=255, outline=255)

occ = np.array(mask_img) > 0
print(f"True UV triangle coverage: {100.0 * np.sum(occ) / occ.size:.2f}%")

# Find completely unused 32x32 and 48x48 blocks with 4px safety padding
print("\nTrue triangle-free 32x32 blocks (with 4px padding):")
free_blocks = []
for by in range(0, h - 32 + 1, 16):
    for bx in range(0, w - 32 + 1, 16):
        if not np.any(occ[max(0, by-4):min(h, by+36), max(0, bx-4):min(w, bx+36)]):
            free_blocks.append((bx, by))
# Coalesce / print best non-overlapping ones
seen = []
for bx, by in free_blocks:
    if any(abs(bx - sx) < 40 and abs(by - sy) < 40 for sx, sy in seen):
        continue
    seen.append((bx, by))
    u0, u1 = bx / w, (bx + 32) / w
    v0, v1 = 1.0 - (by + 32) / h, 1.0 - by / h
    print(f"  px X=[{bx:4d}..{bx+32:4d}] Y=[{by:4d}..{by+32:4d}] -> UV U=[{u0:.4f}..{u1:.4f}] V=[{v0:.4f}..{v1:.4f}]")

# Save triangle mask overlay + Alpha + Specular images
im_d = Image.open(TEX_D)
arr_d = np.array(im_d)
Image.fromarray(arr_d[:, :, 3]).save(ROOT / "scratch" / "wildrider_d_alpha.png")
Image.open(TEX_S).save(ROOT / "scratch" / "wildrider_s.png")

tri_vis = Image.fromarray(arr_d[:, :, :3]).convert("RGB")
tv_arr = np.array(tri_vis)
# Tint unused areas bright green so we visually spot safe islands!
tv_arr[~occ] = [0, 220, 80]
Image.fromarray(tv_arr).save(ROOT / "scratch" / "wildrider_free_uv_map.png")
print("Saved wildrider_d_alpha.png, wildrider_s.png, wildrider_free_uv_map.png")
