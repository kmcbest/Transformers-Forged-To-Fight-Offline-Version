import json
from pathlib import Path

data = json.loads(Path("tools/elita_one/arcee_extracted/arcee_bindposes.json").read_text(encoding="utf-8"))
print(f"Total bindposes: {len(data)}")
for i, bp in enumerate(data[:10]):
    name = bp.get("name")
    m = bp.get("m")
    print(f"Bone {i}: {name}")
    print(f"  [ {m[0]:.3f}, {m[1]:.3f}, {m[2]:.3f}, {m[3]:.3f} ]")
    print(f"  [ {m[4]:.3f}, {m[5]:.3f}, {m[6]:.3f}, {m[7]:.3f} ]")
    print(f"  [ {m[8]:.3f}, {m[9]:.3f}, {m[10]:.3f}, {m[11]:.3f} ]")
    print(f"  [ {m[12]:.3f}, {m[13]:.3f}, {m[14]:.3f}, {m[15]:.3f} ]")
