import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np

SRC = Path(r"O:\agent\transformers-fall-of-cybertron-combaticons\textures")
OUT = Path(r"E:\Agent\TFTF-blender\renders\blastoff\debug_textures_sheet.png")

pairs = [
    ("Chest", "rb_blastoff_chest_cust_matinst.jpg", "chest_e.jpg"),
    ("Legs", "rb_blastoff_legs_cust_matinst.jpg", "legs_e.jpg"),
    ("Head", "rb_blastoff_head_cust_matinst.jpg", "head_e.jpg"),
    ("ArmLo", "rb_blastoff_armlo_cust_matinst.jpg", "armlo_e.jpg"),
    ("ArmUp", "rb_blastoff_armup_cust_matinst.jpg", "armup_e.jpg"),
    ("Veh", "vh_blastoff_cust_matinst.jpg", "vh.jpg"),
]

W = 512
canvas = Image.new("RGB", (W * 3, W * len(pairs)), (20, 20, 20))
draw = ImageDraw.Draw(canvas)

for row, (label, d_name, e_name) in enumerate(pairs):
    im_d = Image.open(SRC / d_name).convert("RGB").resize((W, W))
    im_e = Image.open(SRC / e_name).convert("RGB").resize((W, W))
    # Highlight where diffuse itself has purple/bright pixels (e.g. b > r or purple/magenta)
    arr_d = np.array(im_d, dtype=np.float32)
    # Create overlay: diffuse darkened + bright emissive in green/red
    arr_e = np.array(im_e, dtype=np.float32)
    overlay = np.clip(arr_d * 0.45 + np.stack([arr_e.max(axis=2), np.zeros((W,W)), arr_e.max(axis=2)], axis=2) * 1.5, 0, 255).astype(np.uint8)
    im_ov = Image.fromarray(overlay)

    y0 = row * W
    canvas.paste(im_d, (0, y0))
    canvas.paste(im_e, (W, y0))
    canvas.paste(im_ov, (W * 2, y0))
    draw.text((10, y0 + 10), f"{label}: {d_name}", fill=(255, 255, 0))
    draw.text((W + 10, y0 + 10), f"{e_name}", fill=(255, 100, 255))
    draw.text((W * 2 + 10, y0 + 10), "Overlay (Magenta=E)", fill=(0, 255, 255))

canvas.save(OUT)
print(f"Saved {OUT}")
