import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import shutil
from pathlib import Path

src_dir = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Vortex")
dst_dir = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d\scratch\unity_ab_packer\Assets\Vortex")

for fn in ["cha_vortex_grafted.asset", "cha_vortex_vh_grafted.asset"]:
    src = src_dir / fn
    dst = dst_dir / fn
    shutil.copy2(src, dst)
    print(f"[✓] Copied {src.name} -> {dst}")
