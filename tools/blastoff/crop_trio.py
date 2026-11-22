import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image

img_path = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\5d3b25eb-29f0-44ca-b379-77e4974af4f3\.user_uploaded\media_1795357145861_83266dc0.jpg")
im = Image.open(img_path)

# Let's crop the three bots: Brawl, Blast Off, Onslaught
# x: 50 to 650, y: 0 to 205
crop_trio = im.crop((50, 0, 650, 205))
out_p = Path("renders/blastoff/trio_comparison.png")
crop_trio.save(out_p)
print(f"Saved {out_p}")
