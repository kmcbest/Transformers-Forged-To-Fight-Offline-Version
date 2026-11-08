import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path

with open(r"E:\Agent\TFTF-blender\tools\vortex\grindor_45_vh_authoritative_bindposes.json", "r", encoding="utf-8") as f:
    bp_data = json.load(f)

print("Type of bp_data:", type(bp_data))
if isinstance(bp_data, dict):
    print("Keys sample:", list(bp_data.keys())[:10])
    if "RotorMain" in bp_data:
        print("RotorMain in bp_data:", bp_data["RotorMain"])
    elif "3" in bp_data:
        print("Key '3':", bp_data["3"])
elif isinstance(bp_data, list):
    print("List len:", len(bp_data))
