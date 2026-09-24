# -*- coding: utf-8 -*-
import sys
import shutil
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

data_dir = Path("demolishor_backup/data")
data_dir.mkdir(parents=True, exist_ok=True)

files_to_data = [
    Path("tools/demolishor/ironhide_80_bones.json"),
    Path("tools/demolishor/ironhide_extracted/ironhide_transforms.json"),
    Path("tools/demolishor/ironhide_extracted/ironhide.obj"),
]

for src in files_to_data:
    if src.exists():
        dst = data_dir / src.name
        shutil.copy2(src, dst)
        print(f"[✓] Copied {src} -> {dst} ({dst.stat().st_size} bytes)")
    else:
        print(f"[!] Source not found: {src}")

tex_dir = Path("demolishor_backup/textures_processed")
tex_dir.mkdir(parents=True, exist_ok=True)

src_tex_dir = Path("demolishor_backup/unity_project/Assets/Demolishor")
for p in src_tex_dir.glob("*.png"):
    dst = tex_dir / p.name
    shutil.copy2(p, dst)
    print(f"[✓] Copied {p} -> {dst} ({dst.stat().st_size} bytes)")

print("\n--- Summary of demolishor_backup contents ---")
for sub in ["assets", "unity_project", "scripts", "data", "textures_processed", "patches"]:
    d = Path("demolishor_backup") / sub
    count = len(list(d.rglob("*")))
    total_size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
    print(f"  {sub:20s}: {count:3d} items, {total_size / (1024*1024):.2f} MB")
