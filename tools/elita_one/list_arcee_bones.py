import json
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
REST_JSON = ROOT / "tools" / "elita_one" / "arcee_unity_rest_matrices.json"

with open(REST_JSON, "r") as f:
    data = json.load(f)

for b in data["bones"]:
    print(b["name"])
