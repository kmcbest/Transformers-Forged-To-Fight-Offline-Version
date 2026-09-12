from pathlib import Path
from PIL import Image

src_path = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\d633472c-6af9-4876-ba8e-7c2b6d54f933\wildrider_portrait_1789196404046.jpg")
img = Image.open(src_path)

# Crop to focus nicely on head and upper chest
# Original is 1024x1024
# Head center is at x=512, y=280
# Crop x: 100 to 924 (width 824), y: 40 to 864 (height 824)
crop_box = (100, 40, 924, 864)
cropped = img.crop(crop_box)

out_dir = Path("assets_redeco")
out_dir.mkdir(parents=True, exist_ok=True)

# 1. portrait_wildrider_large.png (256x256)
p_large = cropped.resize((256, 256), Image.Resampling.LANCZOS)
p_large.save(out_dir / "portrait_wildrider_large.png")
print("Saved portrait_wildrider_large.png")

# Also save quest portrait (128x128)
p_quest = cropped.resize((128, 128), Image.Resampling.LANCZOS)
p_quest.save(out_dir / "portrait_wildrider_quest.png")
print("Saved portrait_wildrider_quest.png")

# Also save dialogue icon (128x128)
p_quest.save(out_dir / "wildrider.png")
print("Saved wildrider.png")

# 2. portrait_wildrider_small.jpg (70x70)
p_small = cropped.resize((70, 70), Image.Resampling.LANCZOS).convert("RGB")
p_small.save(out_dir / "portrait_wildrider_small.jpg", quality=92)
print("Saved portrait_wildrider_small.jpg")
