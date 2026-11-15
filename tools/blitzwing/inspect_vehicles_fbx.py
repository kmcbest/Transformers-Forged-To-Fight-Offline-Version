import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import json

ROOT = Path(r"E:\Agent\TFTF-blender")
tank_json = ROOT / "tools" / "blitzwing" / "megatron_tank_21_authoritative_bindposes.json"
jet_json = ROOT / "tools" / "blitzwing" / "ramjet_jet_29_authoritative_bindposes.json"

with open(tank_json, "r", encoding="utf-8") as f:
    td = json.load(f)
print(f"Tank mesh_name: {td['mesh_name']}, bone_count: {td['bone_count']}")
print("Tank bone_names:", td['bone_names'])

with open(jet_json, "r", encoding="utf-8") as f:
    jd = json.load(f)
print(f"\nJet mesh_name: {jd['mesh_name']}, bone_count: {jd['bone_count']}")
print("Jet bone_names:", jd['bone_names'])
