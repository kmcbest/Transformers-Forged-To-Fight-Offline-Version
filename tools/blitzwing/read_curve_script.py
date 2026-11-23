import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
p = Path(r"E:\Agent\TFTF-blender\tools\blitzwing\check_clip_finger_curves.py")
if p.exists():
    print(p.read_text(encoding="utf-8"))
else:
    print("Not found")
