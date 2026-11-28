import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json, numpy as np
from PIL import Image, ImageDraw
from pathlib import Path

TEX_DIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\DragStrip\source\textures")
print("=== 1. Dragstrip Texture Audit ===")
for tp in sorted(TEX_DIR.glob("*.png")):
    im = Image.open(tp)
    arr = np.array(im)
    msg = f"  {tp.name:28s}: size={im.size} mode={im.mode}"
    if arr.ndim == 3 and arr.shape[2] == 4:
        a = arr[:, :, 3]
        msg += f" Alpha min={a.min()} max={a.max()} mean={a.mean():.2f} >0={(a>0).mean()*100:.2f}%"
    elif arr.ndim == 3 and arr.shape[2] == 3:
        msg += f" R={arr[:,:,0].mean():.1f} G={arr[:,:,1].mean():.1f} B={arr[:,:,2].mean():.1f}"
    print(msg)

# Print exact RGB values at non-zero Alpha pixels of Tx_Dragstrip_D & Weapon_D
for name in ("Tx_Dragstrip_D.png", "Tx_Dragstrip_Weapon_D.png"):
    im = Image.open(TEX_DIR / name).convert("RGBA")
    arr = np.array(im)
    m = arr[:, :, 3] > 20
    if m.any():
        ys, xs = np.where(m)
        print(f"  {name} Alpha>20: cnt={m.sum()} bbox X=[{xs.min()},{xs.max()}] Y=[{ys.min()},{ys.max()}] meanRGB={arr[m,:3].mean(axis=0).round(1)}")
    else:
        print(f"  {name} Alpha>20: NONE!")

# Rasterize UV triangles if dragstrip_uv_tris.json exists
uv_json = Path(r"E:\Agent\TFTF-blender\scratch\dragstrip_uv_tris.json")
if uv_json.exists():
    uv_tris = json.loads(uv_json.read_text(encoding="utf-8"))
    for mname, tris in uv_tris.items():
        # Rasterize on 1024x1024 grid
        canvas = Image.new("L", (1024, 1024), 0)
        draw = ImageDraw.Draw(canvas)
        for tri in tris:
            pts = [(u * 1023.0, (1.0 - v) * 1023.0) for u, v in tri]
            draw.polygon(pts, fill=255)
        occ = np.array(canvas) > 0
        print(f"\n  UV Occupancy '{mname}' ({len(tris)} tris): {occ.mean()*100:.2f}% covered")
        # Find 2 free 32x32 squares (with 8px safety margin = 48x48 empty!)
        free_blocks = []
        for y in range(24, 1000, 32):
            for x in range(24, 1000, 32):
                if not occ[y-24:y+24, x-24:x+24].any():
                    free_blocks.append((x, y, round(x/1024.0, 6), round(1.0 - y/1024.0, 6)))
                    if len(free_blocks) >= 4:
                        break
            if len(free_blocks) >= 4:
                break
        print(f"    Safe free 48x48 UV islands (first 4): {free_blocks}")
