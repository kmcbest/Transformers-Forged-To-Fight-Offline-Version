import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import shutil
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
src_dir = ROOT / "3rd-party-models" / "BlastOff" / "00_donor_reference"
dst_dir = ROOT / "toolchain" / "unity_build_project" / "Assets" / "BlastOff" / "Megatronus"
dst_dir.mkdir(parents=True, exist_ok=True)

for f in src_dir.glob("*.png"):
    dst = dst_dir / f.name
    shutil.copy2(f, dst)
    print(f"Copied {f.name} -> {dst}")

print("Done copying Megatronus reference textures.")
