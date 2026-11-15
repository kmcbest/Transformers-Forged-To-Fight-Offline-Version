import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
MEG_51_JSON = ROOT / "tools" / "blitzwing" / "megatron_51_authoritative_bindposes.json"
data = json.loads(MEG_51_JSON.read_text(encoding="utf-8"))

print("=== Megatron Left Hand Finger Bindposes ===")
for fname in ["Thumb", "Index", "Middle", "Ring", "Pinky"]:
    for k in [1, 2, 3]:
        b = f"LeftHand{fname}{k}"
        pos = data["bones"][b]["unity_world_pos"]
        print(f"{b:20s}: ({pos[0]:8.4f}, {pos[1]:8.4f}, {pos[2]:8.4f})")

print("\n=== Megatron Right Hand Finger Bindposes ===")
for fname in ["Thumb", "Index", "Middle", "Ring", "Pinky"]:
    for k in [1, 2, 3]:
        b = f"RightHand{fname}{k}"
        pos = data["bones"][b]["unity_world_pos"]
        print(f"{b:20s}: ({pos[0]:8.4f}, {pos[1]:8.4f}, {pos[2]:8.4f})")
