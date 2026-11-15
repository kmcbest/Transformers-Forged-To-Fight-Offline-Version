import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path

p = Path(r"E:\Agent\TFTF-blender\tools\blitzwing\ramjet_jet_29_authoritative_bindposes.json")
with open(p, "r", encoding="utf-8") as f:
    d = json.load(f)

print("Mesh name:", d.get("mesh_name"))
print("Bone count:", len(d.get("bone_names", [])))
print("Bones:")
for bname in d.get("bone_names", [])[:8]:
    pos = d["bones"][bname]["unity_world_pos"]
    print(f"  {bname:30s} pos: {pos}")
