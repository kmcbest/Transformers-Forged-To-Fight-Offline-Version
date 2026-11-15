import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import shutil
from pathlib import Path

SRC_DIR = Path(r"E:\Agent\TFTF-blender\tools\blitzwing\renders")
DST_DIR = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\2b682fd7-944e-4212-8d1f-cd18b91688cb\renders")
DST_DIR.mkdir(parents=True, exist_ok=True)

for p in SRC_DIR.glob("*.png"):
    dst_p = DST_DIR / p.name
    shutil.copy2(p, dst_p)
    print(f"[✓] Copied {p.name} -> {dst_p}")
