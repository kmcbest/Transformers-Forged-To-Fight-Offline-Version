import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path

hier_file = Path(r"E:\Agent\TFTF-blender\tools\vortex\grindor_78_hierarchy.json")
hier_data = json.loads(hier_file.read_text(encoding="utf-8"))
print("Keys in hier_data:", list(hier_data.keys()))
print("Bone order count:", len(hier_data["bone_order"]))
print("First 15 bones in order:", hier_data["bone_order"][:15])
for b in hier_data["bone_order"][:10]:
    print(f"  {b:20s}: parent={hier_data['hierarchy'].get(b)}")
