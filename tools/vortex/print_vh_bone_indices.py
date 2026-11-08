import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json

with open(r"E:\Agent\TFTF-blender\tools\vortex\grindor_45_vh_bones.json", "r", encoding="utf-8") as f:
    bones = json.load(f)

for idx, b in enumerate(bones):
    print(f"[{idx:2d}] {b}")
