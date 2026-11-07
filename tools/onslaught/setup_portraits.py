import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import shutil
from pathlib import Path

root = Path(r"E:\Agent\TFTF-blender")
redeco_dir = root / "assets_redeco"
redeco_dir.mkdir(parents=True, exist_ok=True)

portraits_dir = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\portraits_odr\portraits")
quest_dir = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\questboard_odr\questboard")

# Search for ironh_c_rotf portraits
p_large = portraits_dir / "portrait_ironh_c_rotf_large.png"
p_small = portraits_dir / "portrait_ironh_c_rotf_small.jpg"
p_quest = quest_dir / "portrait_ironh_c_rotf_quest.png"

targets = [
    (p_large, redeco_dir / "portrait_onslaught_gs_large.png"),
    (p_large, redeco_dir / "portrait_onslaught_large.png"),
    (p_large, redeco_dir / "onslaught_gs.png"),
    (p_small, redeco_dir / "portrait_onslaught_gs_small.jpg"),
    (p_quest, redeco_dir / "portrait_onslaught_gs_quest.png"),
]

for src, dst in targets:
    if src.exists():
        shutil.copy2(src, dst)
        print(f"[✓] Copied placeholder {src.name} -> {dst.name}")
    else:
        print(f"[!] Source portrait not found: {src}")
