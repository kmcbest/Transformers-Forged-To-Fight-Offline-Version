import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
import time
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
UNITY_EXE = ROOT / "toolchain" / "Unity_2020.3.31f1" / "Editor" / "Unity.exe"
PROJECT_DIR = ROOT / "toolchain" / "unity_build_project"
LOG_FILE = ROOT / "renders" / "brawl_sp3" / "calibrate.log"

cmd = [
    str(UNITY_EXE),
    "-batchmode",
    "-quit",
    "-projectPath", str(PROJECT_DIR),
    "-executeMethod", "CalibrateHitDistance.Run",
    "-logFile", str(LOG_FILE)
]

t0 = time.time()
res = subprocess.run(cmd)
print(f"Finished in {time.time()-t0:.1f}s, code={res.returncode}")

if LOG_FILE.exists():
    for line in LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        if "HIT DISTANCE" in line or "Brawl Right Hand" in line or "Rodimus Head" in line or "Delta:" in line:
            print(line)
