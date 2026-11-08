import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path

bp_file = Path(r"E:\Agent\TFTF-blender\tools\vortex\grindor_78_authoritative_bindposes.json")
data = json.loads(bp_file.read_text(encoding="utf-8"))
print("Keys in bp_file:", list(data.keys())[:10])
first_k = list(data.keys())[0]
print("First item:", first_k, data[first_k])
