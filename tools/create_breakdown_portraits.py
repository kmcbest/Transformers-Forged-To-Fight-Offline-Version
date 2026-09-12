from pathlib import Path
from PIL import Image

src_path = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\d633472c-6af9-4876-ba8e-7c2b6d54f933\breakdown_portrait_1789206827949.jpg")
img = Image.open(src_path).convert("RGB")

# Crop upper bust for close-up TFTF portrait
# Center of head is ~512, 160
crop_box = (320, 50, 700, 430)
crop = img.crop(crop_box)

out_dir = Path("assets_redeco")
out_dir.mkdir(exist_ok=True)

# 1. Large portrait (256x256)
p_large = crop.resize((256, 256), Image.Resampling.LANCZOS)
p_large.save(out_dir / "portrait_breakdown_large.png")
p_large.save(out_dir / "portrait_breakdown_gs_large.png")

# 2. Small portrait (70x70)
p_small = crop.resize((70, 70), Image.Resampling.LANCZOS)
p_small.save(out_dir / "portrait_breakdown_small.jpg", quality=95)
p_small.save(out_dir / "portrait_breakdown_gs_small.jpg", quality=95)

# 3. Quest portrait (128x128)
p_quest = crop.resize((128, 128), Image.Resampling.LANCZOS)
p_quest.save(out_dir / "portrait_breakdown_quest.png")
p_quest.save(out_dir / "portrait_breakdown_gs_quest.png")

# 4. Dialogue bust (128x128)
p_quest.save(out_dir / "breakdown.png")
p_quest.save(out_dir / "breakdown_gs.png")

print("[+] All Breakdown portraits successfully created!")
