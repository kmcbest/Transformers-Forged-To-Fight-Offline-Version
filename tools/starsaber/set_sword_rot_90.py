import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path

CONFIG_PATHS = [
    Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\StarSaber\starsaber_grip_config.json"),
    Path(r"E:\Agent\TFTF-blender\tools\starsaber\unity_scripts\starsaber_grip_config.json"),
]

for p in CONFIG_PATHS:
    with open(p, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    # Set exact 90 deg rotated Euler
    cfg["swordLocalRotationEuler"]["x"] = 357.17840576171877
    cfg["swordLocalRotationEuler"]["y"] = 357.2474365234375
    cfg["swordLocalRotationEuler"]["z"] = 89.57763671875

    with open(p, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4)
    print(f"[✓] Updated {p} with swordLocalRotationEuler.z = 89.5776")
