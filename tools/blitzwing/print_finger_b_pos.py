import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
from mathutils import Vector

ROOT = Path(r"E:\Agent\TFTF-blender")
MEG_51_JSON = ROOT / "tools" / "blitzwing" / "megatron_51_authoritative_bindposes.json"
meg_data = json.loads(MEG_51_JSON.read_text(encoding="utf-8"))

def u_to_b(pos):
    return Vector((-float(pos[0]), -float(pos[2]), float(pos[1])))

meg_b_pos = {b: u_to_b(meg_data["bones"][b]["unity_world_pos"]) for b in meg_data["bones"]}

for side in ["Left", "Right"]:
    print(f"\n=== {side} Hand Bones in meg_b_pos (Blender coords) ===")
    print("  Hand:", meg_b_pos[f"{side}Hand"])
    for fi in ["Thumb", "Index", "Middle", "Ring", "Pinky"]:
        for k in [1, 2, 3]:
            bname = f"{side}Hand{fi}{k}"
            print(f"  {bname:16s}: {meg_b_pos[bname]}")
