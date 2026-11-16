import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import shutil
from pathlib import Path

src_dir = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Brawl\00_donor_reference")
dst_dir = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Brawl\Megatron")
dst_dir.mkdir(parents=True, exist_ok=True)

for f in src_dir.glob("*.png"):
    dst = dst_dir / f.name
    shutil.copy2(f, dst)
    print(f"Copied {f.name} -> {dst}")

print("Done copying Megatron reference textures.")
