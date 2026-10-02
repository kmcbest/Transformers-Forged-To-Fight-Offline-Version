import json
from pathlib import Path

ANIM_JSON = Path(r"E:\Agent\TFTF-blender\tools\elita_one\arcee_attackLight_01.json")
with open(ANIM_JSON, "r") as f:
    data = json.load(f)

frame0 = data["frames"][0]["bones"]
bone_names = [b["name"] for b in frame0]

print("Finger bones in anim:")
for b in bone_names:
    if any(k in b.lower() for k in ["thumb", "index", "middle", "ring", "pinky"]):
        print(" ", b)
