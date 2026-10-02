import sys
import shutil
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

tftf_extracted = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack")
assets_redeco = Path(r"E:\Agent\TFTF-blender\assets_redeco")

large_src = tftf_extracted / "portraits_odr" / "portraits" / "portrait_arcee_gs_large.png"
small_src = tftf_extracted / "portraits_odr" / "portraits" / "portrait_arcee_gs_small.jpg"
quest_src = tftf_extracted / "questboard_odr" / "questboard" / "portrait_acree_gs_quest.png"

assert large_src.exists(), f"Missing {large_src}"
assert small_src.exists(), f"Missing {small_src}"
assert quest_src.exists(), f"Missing {quest_src}"

# Large PNGs
for name in ["portrait_elita_one_gs_large.png", "portrait_elita_one_large.png", "elita_one_gs.png", "elita_one.png"]:
    dest = assets_redeco / name
    shutil.copy2(large_src, dest)
    print(f"[✓] Created {dest.name}")

# Small JPGs
for name in ["portrait_elita_one_gs_small.jpg", "portrait_elita_one_small.jpg"]:
    dest = assets_redeco / name
    shutil.copy2(small_src, dest)
    print(f"[✓] Created {dest.name}")

# Quest PNGs
for name in ["portrait_elita_one_gs_quest.png", "portrait_elita_one_quest.png"]:
    dest = assets_redeco / name
    shutil.copy2(quest_src, dest)
    print(f"[✓] Created {dest.name}")

print("Portrait placeholder setup complete.")
