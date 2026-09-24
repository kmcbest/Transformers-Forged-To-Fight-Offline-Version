import sys
import shutil
from pathlib import Path
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

redeco = Path("assets_redeco")

# Source portrait
src_img = Image.open(redeco / "portrait_demolishor_large.png").convert("RGBA")

# 1. portrait_demolishor_gs_large.png (256x256 RGBA)
large_img = src_img.resize((256, 256), Image.Resampling.LANCZOS)
large_img.save(redeco / "portrait_demolishor_gs_large.png", "PNG")
large_img.save(redeco / "portrait_demolishor_large.png", "PNG")

# 2. portrait_demolishor_gs_small.jpg (128x128 RGB JPEG)
# Note: small portraits in TFTF are RGB JPEGs!
small_img = src_img.resize((128, 128), Image.Resampling.LANCZOS).convert("RGB")
small_img.save(redeco / "portrait_demolishor_gs_small.jpg", "JPEG", quality=95)
small_img.save(redeco / "portrait_demolishor_small.jpg", "JPEG", quality=95)

# 3. portrait_demolishor_gs_quest.png (128x128 RGBA PNG)
quest_img = src_img.resize((128, 128), Image.Resampling.LANCZOS)
quest_img.save(redeco / "portrait_demolishor_gs_quest.png", "PNG")
quest_img.save(redeco / "portrait_demolishor_quest.png", "PNG")

# 4. Dialogue / Story icons
src_img.save(redeco / "demolishor.png", "PNG")
src_img.save(redeco / "demolishor_gs.png", "PNG")

print("[✓] Generated all Demolishor portraits:")
for p in redeco.glob("*demolishor*"):
    print(f"  {p.name} ({p.stat().st_size} bytes)")
