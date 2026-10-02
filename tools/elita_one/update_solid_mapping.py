import json
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
MAPPING_FILE = ROOT / "tools" / "elita_one" / "elita_to_arcee_mapping.json"

with open(MAPPING_FILE, "r", encoding="utf-8") as f:
    mapping = json.load(f)

# Fold all fingers cleanly into Hand
for k in list(mapping.keys()):
    if k.startswith("l_thumb") or k.startswith("l_index") or k.startswith("l_middle") or k.startswith("l_ring") or k.startswith("l_pinky"):
        mapping[k] = "LeftHand"
    elif k.startswith("r_thumb") or k.startswith("r_index") or k.startswith("r_middle") or k.startswith("r_ring") or k.startswith("r_pinky"):
        mapping[k] = "RightHand"

# Wheels
mapping["l_lower_cover_wheel_skin"] = "LeftArm"
mapping["l_lower_wheel_skin"] = "LeftArm"
mapping["l_lower_wheel_skin_end"] = "LeftArm"
mapping["r_lower_cover_wheel_skin"] = "RightArm"
mapping["r_lower_wheel_skin"] = "RightArm"
mapping["r_lower_wheel_skin_end"] = "RightArm"

mapping["l_upper_cover_wheel_skin"] = "Spine1"
mapping["l_upper_wheel_skin"] = "Spine1"
mapping["l_upper_wheel_skin_end"] = "Spine1"
mapping["r_upper_cover_wheel_skin"] = "Spine1"
mapping["r_upper_wheel_skin"] = "Spine1"
mapping["r_upper_wheel_skin_end"] = "Spine1"

# Sockets and pistons
mapping["SOCKET_weapon"] = "LeftHand"
mapping["SOCKET_weapon_end"] = "LeftHand"
mapping["SOCKET_skill"] = "RightHand"
mapping["SOCKET_skill_end"] = "RightHand"

mapping["l_shoulder_pistons_skin"] = "LeftShoulder"
mapping["l_shoulder_pistons_skin_end"] = "LeftShoulder"
mapping["r_shoulder_pistons_skin"] = "RightShoulder"
mapping["r_shoulder_pistons_skin_end"] = "RightShoulder"

mapping["l_piston_lower_arm_start_skin"] = "LeftForeArm"
mapping["l_piston_lower_arm_start_skin_end"] = "LeftForeArm"
mapping["l_piston_lower_arm_end_skin"] = "LeftForeArm"
mapping["l_piston_lower_arm_end_skin_end"] = "LeftForeArm"

mapping["r_piston_lower_arm_start_skin"] = "RightForeArm"
mapping["r_piston_lower_arm_start_skin_end"] = "RightForeArm"
mapping["r_piston_lower_arm_end_skin"] = "RightForeArm"
mapping["r_piston_lower_arm_end_skin_end"] = "RightForeArm"

# Feet
mapping["l_foot_heel_skin"] = "LeftFoot"
mapping["l_foot_heel_skin_end"] = "LeftFoot"
mapping["r_foot_heel_skin"] = "RightFoot"
mapping["r_foot_heel_skin_end"] = "RightFoot"

with open(MAPPING_FILE, "w", encoding="utf-8") as f:
    json.dump(mapping, f, indent=2)

print("[OK] Successfully updated elita_to_arcee_mapping.json with solid hands & fixed wheels!")
