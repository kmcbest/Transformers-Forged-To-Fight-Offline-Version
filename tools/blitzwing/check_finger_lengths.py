import sys
import json
from pathlib import Path
from mathutils import Vector

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
MEG_JSON = ROOT / "tools" / "blitzwing" / "megatron_51_authoritative_bindposes.json"
data = json.loads(MEG_JSON.read_text(encoding="utf-8"))

def u_to_b(pos):
    return Vector((-float(pos[0]), -float(pos[2]), float(pos[1])))

for pfx in ["Left", "Right"]:
    print(f"\nMegatron {pfx} Hand Thumb:")
    t1 = u_to_b(data["bones"][f"{pfx}HandThumb1"]["unity_world_pos"])
    t2 = u_to_b(data["bones"][f"{pfx}HandThumb2"]["unity_world_pos"])
    t3 = u_to_b(data["bones"][f"{pfx}HandThumb3"]["unity_world_pos"])
    print(f"  Thumb1: {t1}")
    print(f"  Thumb2: {t2} (len1-2: {(t2-t1).length:.3f}m)")
    print(f"  Thumb3: {t3} (len2-3: {(t3-t2).length:.3f}m)")

    for fn in ["Index", "Middle", "Ring", "Pinky"]:
        f1 = u_to_b(data["bones"][f"{pfx}Hand{fn}1"]["unity_world_pos"])
        f2 = u_to_b(data["bones"][f"{pfx}Hand{fn}2"]["unity_world_pos"])
        f3 = u_to_b(data["bones"][f"{pfx}Hand{fn}3"]["unity_world_pos"])
        print(f"  {fn}: len1-2: {(f2-f1).length:.3f}m, len2-3: {(f3-f2).length:.3f}m")
