import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(r"E:\Agent\TFTF-blender")

print("=== 1. RAOE.B intensity distributions in Combaticons ===")
for bname in ["vortex_gs.assetbundle", "onslaught_gs.assetbundle", "brawl_gs.assetbundle", "swindle_gs.assetbundle", "blastoff_gs.assetbundle"]:
    bp = ROOT / "assets_redeco" / bname
    if not bp.exists():
        continue
    env = UnityPy.load(str(bp))
    for o in env.objects:
        if o.type.name == "Texture2D":
            t = o.read()
            if "raoe" in t.m_Name.lower():
                arr = np.array(t.image)
                if arr.ndim == 3 and arr.shape[2] >= 3:
                    b = arr[:, :, 2]
                    nz = b[b > 15]
                    if len(nz) > 0:
                        print(f"  {bname:25s} {t.m_Name:32s}: nz_pct={len(nz)/b.size*100:.2f}%, p50={np.percentile(nz,50):.0f}, p90={np.percentile(nz,90):.0f}, p99={np.percentile(nz,99):.0f}, max={nz.max()}")

print("\n=== 2. Analyzing purple/violet emissive pixels directly inside Blast Off source diffuse textures ===")
SRC = Path(r"O:\agent\transformers-fall-of-cybertron-combaticons\textures")
src_files = [
    ("Chest", "rb_blastoff_chest_cust_matinst.jpg"),
    ("Legs", "rb_blastoff_legs_cust_matinst.jpg"),
    ("Head", "rb_blastoff_head_cust_matinst.jpg"),
    ("ArmLo", "rb_blastoff_armlo_cust_matinst.jpg"),
    ("ArmUp", "rb_blastoff_armup_cust_matinst.jpg"),
    ("Veh", "vh_blastoff_cust_matinst.jpg"),
]

W = 512
canvas = Image.new("RGB", (W * 2, W * len(src_files)), (15, 15, 15))
draw = ImageDraw.Draw(canvas)

for row, (label, fname) in enumerate(src_files):
    im = Image.open(SRC / fname).convert("RGB")
    arr = np.array(im, dtype=np.float32)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    # Note: Blast Off armor is brown/orange (R > G > B) or grey steel (R ~ G ~ B).
    # Purple/violet glowing parts have B > G + threshold AND B >= R * 0.85 (or strong blue-violet excess over green)!
    b_over_g = b - g
    r_over_g = r - g
    # Measure purple score: blue significantly above green, and not plain grey, and not dark brown (where R >> B)
    is_purple = (b > g + 12) & (b > r * 0.88) & (b > 40)
    pct = is_purple.mean() * 100.0
    print(f"  {label:6s} ({fname:36s}): purple pixels={pct:.2f}%, max(B-G)={b_over_g.max():.1f}, mean_rgb_purple={arr[is_purple].mean(axis=0).round(1) if is_purple.any() else None}")

    vis_d = im.resize((W, W))
    mask_vis = np.zeros_like(arr, dtype=np.uint8)
    mask_vis[is_purple] = [255, 60, 255]
    im_m = Image.fromarray(mask_vis).resize((W, W))
    y0 = row * W
    canvas.paste(vis_d, (0, y0))
    canvas.paste(im_m, (W, y0))
    draw.text((10, y0 + 10), f"{label}: {fname}", fill=(255, 255, 0))
    draw.text((W + 10, y0 + 10), f"Detected Purple/Violet Mask ({pct:.2f}%)", fill=(0, 255, 255))

out_path = ROOT / "renders/blastoff/debug_detected_purple.png"
canvas.save(out_path)
print(f"Saved {out_path}")
