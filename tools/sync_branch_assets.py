import os
import shutil
from pathlib import Path

src_root = Path(r"E:\Agent\TFTF")
dst_root = Path(r"E:\Agent\TFTF-blender")

print("=== 1. Syncing assets_netflix ===")
src_netflix = src_root / "assets_netflix"
dst_netflix = dst_root / "assets_netflix"
dst_netflix.mkdir(exist_ok=True)

if src_netflix.exists():
    for f in src_netflix.iterdir():
        target = dst_netflix / f.name
        if not target.exists():
            print(f"Copying {f.name} ({f.stat().st_size} bytes)")
            shutil.copy2(f, target)
        else:
            print(f"Already exists: {f.name}")

print("\n=== 2. Syncing missing assets_redeco (excluding Demolishor) ===")
src_redeco = src_root / "assets_redeco"
dst_redeco = dst_root / "assets_redeco"

if src_redeco.exists():
    for f in src_redeco.iterdir():
        if "demolishor" in f.name.lower():
            continue  # NEVER touch Demolishor in blender repo
        target = dst_redeco / f.name
        if not target.exists():
            print(f"Copying {f.name} ({f.stat().st_size} bytes)")
            shutil.copy2(f, target)

print("\nDone syncing assets!")
