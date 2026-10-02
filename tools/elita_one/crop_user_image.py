from PIL import Image
from pathlib import Path

IMG_PATH = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\db8b7cf0-602b-4ceb-a715-2db112ce44ce\.user_uploaded\media_1790917717110.png")
OUT_DIR = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\db8b7cf0-602b-4ceb-a715-2db112ce44ce")

img = Image.open(IMG_PATH)
w, h = img.size
print(f"Image size: {w}x{h}")

# Box 1: Bottom left
# In the image, bottom-left red box:
# x in [0, 150], y in [700, 880] approximately (relative to w, h)
box_bl = img.crop((int(w * 0.0), int(h * 0.7), int(w * 0.16), int(h * 0.90)))
box_bl.save(OUT_DIR / "crop_box_bl.png")

# Box 2: Mid right
box_mr = img.crop((int(w * 0.6), int(h * 0.25), int(w * 0.9), int(h * 0.50)))
box_mr.save(OUT_DIR / "crop_box_mr.png")

# Box 3: Top right
box_tr = img.crop((int(w * 0.53), int(h * 0.01), int(w * 0.85), int(h * 0.25)))
box_tr.save(OUT_DIR / "crop_box_tr.png")

print("Saved crop boxes.")
