import sys
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
PROJECT_DIR = ROOT / "toolchain" / "unity_build_project"
UNITY_EXE = ROOT / "toolchain" / "Unity_2020.3.31f1" / "Editor" / "Unity.exe"
LOG_FILE = PROJECT_DIR / "compare_bindposes.log"

cmd = [
    str(UNITY_EXE),
    "-batchmode",
    "-quit",
    "-projectPath", str(PROJECT_DIR),
    "-executeMethod", "CompareBindposes.Run",
    "-logFile", str(LOG_FILE)
]

res = subprocess.run(cmd)
if LOG_FILE.exists():
    for line in LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        if any(k in line for k in ["===", "Bone[", "Arcee Bindpose", "Elita Bindpose", "Error", "Exception"]):
            print(line)
