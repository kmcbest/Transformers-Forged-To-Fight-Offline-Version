import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path

p = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\cha_blitzwing_gs_00.asset")
lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
print(f"Total lines: {len(lines)}")
for i, line in enumerate(lines[:60]):
    print(f"{i+1}: {line}")
