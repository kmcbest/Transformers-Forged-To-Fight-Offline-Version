import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import json
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np

ROOT = Path(r"E:\Agent\TFTF-blender")
SRC_TEX = Path(r"O:\agent\transformers-fall-of-cybertron-combaticons\textures")
records = json.loads((ROOT / "renders/blastoff/uv_islands_dump.json").read_text(encoding="utf-8"))

TEX_MAP = {
    "RB_Blastoff_Chest_Cust_MatINST": "rb_blastoff_chest_cust_matinst.jpg",
    "RB_Blastoff_Legs_Cust_MatINST": "rb_blastoff_legs_cust_matinst.jpg",
    "RB_Blastoff_Head_Cust_MatINST": "rb_blastoff_head_cust_matinst.jpg",
    "RB_Blastoff_ArmLo_Cust_MatINST": "rb_blastoff_armlo_cust_matinst.jpg",
    "RB_Blastoff_ArmUp_Cust_MatINST": "rb_blastoff_armup_cust_matinst.jpg",
    "VH_Blastoff_Cust_MatINST": "vh_blastoff_cust_matinst.jpg",
}

for mname, fname in TEX_MAP.items():
    im = Image.open(SRC_TEX / fname).convert("RGB")
    w, h = im.size
    draw = ImageDraw.Draw(im)
    # Draw UV grid + highlight specific regions in bright color
    for r in records:
        if r["mat"] != mname:
            continue
        fwd, left, up = r["w"]
        bone = r["bone"]
        pts = [(p[0] * w, (1.0 - p[1]) * h) for p in r["uv"]]
        if len(pts) < 3:
            continue
        color = None
        if mname == "RB_Blastoff_Chest_Cust_MatINST":
            if "pelvis" in bone:
                color = (255, 0, 0)       # RED = pelvis (matte!)
            elif "Robo02" in bone and up > 4.4:
                color = (255, 128, 0)     # ORANGE = collar (matte!)
            elif fwd > 0.25 and 3.4 < up < 4.5:
                color = (0, 255, 0)       # GREEN = Front Chest Grille & Lower Vents!
        elif mname == "RB_Blastoff_ArmUp_Cust_MatINST":
            if "Pad" in bone:
                color = (0, 255, 0)       # GREEN = Shoulder pad
        elif mname == "RB_Blastoff_Legs_Cust_MatINST":
            if "pelvis" in bone:
                color = (255, 0, 0)       # RED = pelvis/thighs
            elif fwd > 0.15 and 0.4 < up < 2.3:
                color = (0, 255, 0)       # GREEN = Front Shin
        elif mname == "RB_Blastoff_Head_Cust_MatINST":
            if fwd > 0.05 and 4.82 < up < 4.98:
                color = (0, 255, 0)       # GREEN = Eyes / Face
        elif mname == "RB_Blastoff_ArmLo_Cust_MatINST":
            if "Elbow" in bone:
                color = (0, 255, 0)
        elif mname == "VH_Blastoff_Cust_MatINST":
            if "VH_Blastoff" in r["obj"]:
                color = (0, 255, 255)
        if color:
            draw.polygon(pts, outline=color)

    # Draw 128px coordinate ruler grid
    for gx in range(0, w, 128):
        draw.line([(gx, 0), (gx, h)], fill=(100, 100, 100), width=1)
        draw.text((gx + 2, 2), str(gx), fill=(255, 255, 0))
    for gy in range(0, h, 128):
        draw.line([(0, gy), (w, gy)], fill=(100, 100, 100), width=1)
        draw.text((2, gy + 2), str(gy), fill=(255, 255, 0))

    out_f = ROOT / "renders/blastoff" / f"uv_map_{mname}.png"
    im.save(out_f)
    print(f"Saved {out_f.name} ({w}x{h})")
