import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path

bones = json.loads(Path(r"E:\Agent\TFTF-blender\tools\vortex\grindor_78_bones.json").read_text(encoding="utf-8"))
for i, b in enumerate(bones):
    print(f"[{i:2d}] {b}")
