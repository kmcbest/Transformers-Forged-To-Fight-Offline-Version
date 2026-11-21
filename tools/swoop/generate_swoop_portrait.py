import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from PIL import Image, ImageDraw
import numpy as np
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
RAW_IMG = ROOT / "scratch/swoop_portrait_raw.png"
REDECO_DIR = ROOT / "assets_redeco"

assert RAW_IMG.is_file(), f"Missing raw render: {RAW_IMG}"

# Load raw 512x512 rendered character with alpha
raw_im = Image.open(RAW_IMG).convert("RGBA")

# 1. Large 256x256 RGBA (transparent background for battle/dialogue/versus)
large_256 = raw_im.resize((256, 256), Image.Resampling.LANCZOS)

# 2. Small 128x128 RGB JPEG (with Autobot tech gradient background for roster tile)
small_128_rgba = raw_im.resize((128, 128), Image.Resampling.LANCZOS)

# Create a sleek Autobot Tech dark-blue radial gradient background
bg = Image.new("RGBA", (128, 128))
draw = ImageDraw.Draw(bg)
for y in range(128):
    for x in range(128):
        # Radial distance from upper center (64, 45)
        dist = np.hypot(x - 64, y - 45)
        factor = np.clip(1.0 - dist / 80.0, 0.0, 1.0)
        # Deep sci-fi blue highlight in center-top, fading to dark navy
        r = int(12 + 25 * factor)
        g = int(24 + 45 * factor)
        b = int(48 + 75 * factor)
        draw.point((x, y), fill=(r, g, b, 255))

# Composite character over background
small_composite = Image.alpha_composite(bg, small_128_rgba).convert("RGB")

# Dialogue icon: 256x256 RGBA
dialogue_256 = large_256.copy()

# Save all variants to assets_redeco
targets = [
    # Primary "swoop" keys
    (REDECO_DIR / "portrait_swoop_large.png", large_256, "PNG"),
    (REDECO_DIR / "portrait_swoop_small.jpg", small_composite, "JPEG"),
    (REDECO_DIR / "portrait_swoop_quest.png", large_256, "PNG"),
    (REDECO_DIR / "swoop.png", dialogue_256, "PNG"),

    # Full bot_id "swoop_gs_deluxe2008" fallback keys
    (REDECO_DIR / "portrait_swoop_gs_deluxe2008_large.png", large_256, "PNG"),
    (REDECO_DIR / "portrait_swoop_gs_deluxe2008_small.jpg", small_composite, "JPEG"),
    (REDECO_DIR / "portrait_swoop_gs_deluxe2008_quest.png", large_256, "PNG"),
    (REDECO_DIR / "swoop_gs_deluxe2008.png", dialogue_256, "PNG"),
]

for out_path, img_obj, fmt in targets:
    if fmt == "JPEG":
        img_obj.save(out_path, format="JPEG", quality=95)
    else:
        img_obj.save(out_path, format="PNG")
    print(f"Saved [{fmt}] -> {out_path.name} ({img_obj.size})")

print("All Swoop portraits generated successfully!")
