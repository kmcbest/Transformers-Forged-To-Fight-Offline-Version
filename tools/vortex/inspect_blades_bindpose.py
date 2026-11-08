import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json

with open(r"E:\Agent\TFTF-blender\tools\vortex\grindor_45_vh_authoritative_bindposes.json", "r", encoding="utf-8") as f:
    bp_data = json.load(f)

for k in ["RotorMain", "RotorMainBlade1", "RotorMainBlade2", "RotorMainBlade3", "RotorMainBlade4"]:
    if k in bp_data:
        info = bp_data[k]
        print(f"{k:18s}: index={info['index']:2d}, world_pos={info['world_pos']}")
