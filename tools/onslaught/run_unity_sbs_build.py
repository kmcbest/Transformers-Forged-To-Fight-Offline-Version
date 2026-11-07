import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
from pathlib import Path

UNITY_EXE = r"E:\Agent\TFTF-blender\toolchain\Unity_2020.3.31f1\Editor\Unity.exe"
PROJ_DIR = r"E:\Agent\TFTF-blender\toolchain\unity_build_project"
LOG_FILE = Path(r"E:\Agent\TFTF-blender\tools\onslaught\unity_sbs_scene.log")

cmd = [
    UNITY_EXE,
    "-batchmode",
    "-quit",
    "-projectPath", PROJ_DIR,
    "-executeMethod", "BuildOnslaughtInspectionScene.Build",
    "-logFile", str(LOG_FILE),
]

print(f"[*] Running Unity headless scene builder & multi-pose renderer...")
res = subprocess.run(cmd)
print(f"[*] Unity exited with code: {res.returncode}")

if LOG_FILE.exists():
    txt = LOG_FILE.read_text(encoding="utf-8", errors="replace")
    for line in txt.splitlines():
        if any(k in line for k in ["[Onslaught]", "[Ironhide]", "[VehWorldAudit]", "[VehChosen]", "[SP3", "[✓]", "Error", "Exception", "CS0", "CS1", "ALL DONE"]):
            print(" ", line)
