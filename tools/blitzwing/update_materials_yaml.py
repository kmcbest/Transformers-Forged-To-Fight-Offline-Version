import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import re
from pathlib import Path

MAT_DIR = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\Materials")
MEG_MAT_DIR = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\Megatron")

SPECS = {
    "Mat_Blitzwing_Body.mat": (0.65, 0.78),
    "Mat_Blitzwing_Legs.mat": (0.65, 0.78),
    "Mat_Blitzwing_Hands.mat": (0.60, 0.75),
    "Mat_Blitzwing_Tank.mat": (0.65, 0.78),
    "Mat_Blitzwing_Jet.mat": (0.70, 0.82),
    "Mat_Blitzwing_Treads.mat": (0.35, 0.35),
    "M_Meg_Main.mat": (0.62, 0.72),
    "M_Meg_Misc.mat": (0.62, 0.72),
}

for mat_name, (gloss, metallic) in SPECS.items():
    p = MAT_DIR / mat_name
    if not p.exists():
        p = MEG_MAT_DIR / mat_name
    if not p.exists():
        print(f"Skipping {mat_name}: not found")
        continue
        
    text = p.read_text(encoding="utf-8")
    text = re.sub(r"- _Glossiness: [0-9.]+", f"- _Glossiness: {gloss}", text)
    text = re.sub(r"- _Metallic: [0-9.]+", f"- _Metallic: {metallic}", text)
    p.write_text(text, encoding="utf-8")
    print(f"[✓] Updated {mat_name}: Glossiness={gloss}, Metallic={metallic}")

print("All materials updated successfully!")
