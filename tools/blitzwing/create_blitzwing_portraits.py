#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
create_blitzwing_portraits.py
Derives the full set of Blitzwing (blitzwing_gs) portrait, questboard, and
dialogue icon files in assets_redeco/ from the user-prepared master images:
  - assets_redeco/portrait_blitzwing_large.png (256x256 RGBA PNG)
  - assets_redeco/portrait_blitzwing_gs_small.jpg (128x128 RGB JPEG)
"""
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from PIL import Image

ROOT = Path(r"E:\Agent\TFTF-blender")
OUT_DIR = ROOT / "assets_redeco"


def main():
    src_large = OUT_DIR / "portrait_blitzwing_large.png"
    src_small = OUT_DIR / "portrait_blitzwing_gs_small.jpg"

    assert src_large.is_file(), f"Missing master large portrait: {src_large}"
    assert src_small.is_file(), f"Missing master small portrait: {src_small}"

    with Image.open(src_large) as im_l:
        print(f"[*] Master large: {src_large.name} size={im_l.size} mode={im_l.mode}")
        assert im_l.size == (256, 256), f"Unexpected large size {im_l.size}"

    with Image.open(src_small) as im_s:
        print(f"[*] Master small: {src_small.name} size={im_s.size} mode={im_s.mode}")
        assert im_s.size == (128, 128), f"Unexpected small size {im_s.size}"

    large_targets = [
        "portrait_blitzwing_gs_large.png",
        "portrait_blitzwing_gs_quest.png",
        "portrait_blitzwing_quest.png",
        "blitzwing_gs.png",
        "blitzwing.png",
    ]
    for name in large_targets:
        dst = OUT_DIR / name
        shutil.copy2(src_large, dst)
        print(f"[✓] Generated {dst.name}")

    small_targets = [
        "portrait_blitzwing_small.jpg",
    ]
    for name in small_targets:
        dst = OUT_DIR / name
        shutil.copy2(src_small, dst)
        print(f"[✓] Generated {dst.name}")

    print("[+] All Blitzwing companion portrait/quest/dialogue files generated cleanly.")


if __name__ == "__main__":
    main()
