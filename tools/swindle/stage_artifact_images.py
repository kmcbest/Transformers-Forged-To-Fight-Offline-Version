import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import shutil
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
ART_DIR = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\1b3e2346-c476-4b81-91bd-36befdadb0e5")

images = [
    ROOT / "assets_redeco" / "portrait_swindle_gs_large.png",
    ROOT / "assets_redeco" / "portrait_swindle_gs_small.jpg",
    ROOT / "renders" / "swindle" / "unity_sbs_01_combat_idle_front.png",
    ROOT / "renders" / "swindle" / "unity_sbs_06_vehicle_mode_sbs.png",
    ROOT / "renders" / "swindle" / "unity_sbs_06b_vehicle_side.png",
    ROOT / "renders" / "swindle" / "unity_10a_left_hand_open.png",
    ROOT / "renders" / "swindle" / "unity_10b_left_hand_curled.png",
    ROOT / "renders" / "swindle" / "unity_10c_right_hand_open.png",
    ROOT / "renders" / "swindle" / "unity_10d_right_hand_curled.png",
    ROOT / "renders" / "swindle" / "unity_sbs_07_high_kick_action.png",
    ROOT / "renders" / "swindle" / "unity_sbs_08_victory_pose.png",
]

for src in images:
    if src.exists():
        dst = ART_DIR / src.name
        shutil.copy2(src, dst)
        print(f"[✓] Copied {src.name} to artifact directory")
