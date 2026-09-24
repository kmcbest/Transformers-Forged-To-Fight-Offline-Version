# -*- coding: utf-8 -*-
import sys
import shutil
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

root = Path(".")
src_large = root / "extracted_apk/assets/assetpack/portraits_odr/portraits/portrait_ironh_c_rotf_large.png"
src_small = root / "extracted_apk/assets/assetpack/portraits_odr/portraits/portrait_ironh_c_rotf_small.jpg"
src_quest = root / "extracted_apk/assets/assetpack/questboard_odr/questboard/portrait_ironh_c_rotf_quest.png"

assert src_large.exists(), f"Missing {src_large}"
assert src_small.exists(), f"Missing {src_small}"
assert src_quest.exists(), f"Missing {src_quest}"

targets = [
    Path("assets_redeco"),
    Path("demolishor_backup/assets/portraits")
]

for target_dir in targets:
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Large
    shutil.copy2(src_large, target_dir / "portrait_demolishor_gs_large.png")
    shutil.copy2(src_large, target_dir / "portrait_demolishor_large.png")
    shutil.copy2(src_large, target_dir / "demolishor.png")
    shutil.copy2(src_large, target_dir / "demolishor_gs.png")
    
    # Small
    shutil.copy2(src_small, target_dir / "portrait_demolishor_gs_small.jpg")
    shutil.copy2(src_small, target_dir / "portrait_demolishor_small.jpg")
    
    # Quest
    shutil.copy2(src_quest, target_dir / "portrait_demolishor_gs_quest.png")
    shutil.copy2(src_quest, target_dir / "portrait_demolishor_quest.png")
    
    print(f"[✓] Copied clean placeholder portraits to {target_dir}")
