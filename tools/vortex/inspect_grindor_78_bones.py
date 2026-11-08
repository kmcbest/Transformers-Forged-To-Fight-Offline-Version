import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path

bones_file = Path(r"E:\Agent\TFTF-blender\tools\vortex\grindor_78_bones.json")
data = json.loads(bones_file.read_text(encoding="utf-8"))
print(f"Data type: {type(data)}, length: {len(data)}")
print("First 10 items:", data[:10])
