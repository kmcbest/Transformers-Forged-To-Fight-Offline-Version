import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json

with open("tools/swoop/ramjet_jet_29_authoritative_bindposes.json", "r", encoding="utf-8") as f:
    jet_data = json.load(f)

print("Ramjet 29 jet bones:")
for i, bname in enumerate(jet_data["bone_names"]):
    binfo = jet_data["bones"][bname]
    print(f"  [{i:2d}] {bname:25s} parent: {binfo['parent']}")
