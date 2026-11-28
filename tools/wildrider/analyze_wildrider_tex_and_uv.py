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
TEX_N = WR_DIR / "textures" / "Tx_Wildrider_N.png"
TEX_S = WR_DIR / "textures" / "Tx_Wildrider_S.png"
NPZ = ROOT / "scratch" / "wildrider_uv_dump.npz"

d = np.load(NPZ)
uv_wr = d["uv_wr"]
bi_wr = d["bi_wr"]
bn_wr = [str(x) for x in d["bn_wr"]]
uv_gun = d["uv_gun"]
uvs_all = np.vstack([uv_wr, uv_gun])

print(f"WildRider.001 UV range: U=[{uv_wr[:,0].min():.4f}, {uv_wr[:,0].max():.4f}], V=[{uv_wr[:,1].min():.4f}, {uv_wr[:,1].max():.4f}]")
print(f"WildRider_Gun UV range: U=[{uv_gun[:,0].min():.4f}, {uv_gun[:,0].max():.4f}], V=[{uv_gun[:,1].min():.4f}, {uv_gun[:,1].max():.4f}]")

im_d = Image.open(TEX_D)
arr_d = np.array(im_d)
w, h = im_d.size  # 1024, 1024

# 1. Find empty 64x64 pixel islands on 1024x1024
occ = np.zeros((h, w), dtype=bool)
px = np.clip(((uvs_all[:, 0] % 1.0) * w).astype(int), 0, w - 1)
py = np.clip(((1.0 - (uvs_all[:, 1] % 1.0)) * h).astype(int), 0, h - 1)
occ[py, px] = True

print("\nEmpty 64x64 pixel blocks (8px padding):")
empty_blocks = []
for by in range(0, h - 64 + 1, 64):
    for bx in range(0, w - 64 + 1, 64):
        if not np.any(occ[max(0, by-8):min(h, by+72), max(0, bx-8):min(w, bx+72)]):
            u0, u1 = bx / w, (bx + 64) / w
            v0, v1 = 1.0 - (by + 64) / h, 1.0 - by / h
            empty_blocks.append((bx, by, u0, u1, v0, v1))
for bx, by, u0, u1, v0, v1 in empty_blocks[:15]:
    print(f"  px X=[{bx}..{bx+64}] Y=[{by}..{by+64}] -> UV U=[{u0:.4f}..{u1:.4f}] V=[{v0:.4f}..{v1:.4f}]")
print(f"  Total empty 64x64 blocks: {len(empty_blocks)}")

# 2. Check Alpha > 0 regions in Tx_Wildrider_D.png
alpha = arr_d[:, :, 3]
wr_px = np.clip(((uv_wr[:, 0] % 1.0) * w).astype(int), 0, w - 1)
wr_py = np.clip(((1.0 - (uv_wr[:, 1] % 1.0)) * h).astype(int), 0, h - 1)
hit_a = alpha[wr_py, wr_px]
mask_a = hit_a > 10
hits = {}
colors_by_bone = {}
for bi, a_val, px_i, py_i in zip(bi_wr[mask_a], hit_a[mask_a], wr_px[mask_a], wr_py[mask_a]):
    bn = bn_wr[bi] if bi >= 0 else "None"
    hits[bn] = hits.get(bn, 0) + 1
    colors_by_bone.setdefault(bn, []).append(arr_d[py_i, px_i, :3])

print("\nAlpha > 10 UV hits by dominant bone & mean RGB:")
for bn, cnt in sorted(hits.items(), key=lambda x: -x[1]):
    mean_rgb = np.mean(colors_by_bone[bn], axis=0).round(1)
    print(f"  {bn:20s}: {cnt:5d} loops, mean RGB={mean_rgb.tolist()}")

# 3. Save UV overlay + raw texture preview to scratch for inspection
overlay = Image.fromarray(arr_d[:, :, :3]).convert("RGB")
draw = ImageDraw.Draw(overlay)
for x_i, y_i in zip(px[::3], py[::3]):
    draw.point((int(x_i), int(y_i)), fill=(0, 255, 0))
for x_i, y_i in zip(wr_px[mask_a], wr_py[mask_a]):
    draw.point((int(x_i), int(y_i)), fill=(255, 255, 0))
overlay.save(ROOT / "scratch" / "wildrider_uv_overlay.png")
Image.fromarray(arr_d[:, :, :3]).save(ROOT / "scratch" / "wildrider_d_rgb.png")
print("Saved scratch/wildrider_uv_overlay.png & scratch/wildrider_d_rgb.png")
