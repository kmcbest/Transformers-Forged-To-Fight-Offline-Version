import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
from pathlib import Path

unity_exe = Path(r"E:\Agent\TFTF-blender\toolchain\Unity_2020.3.31f1\Editor\Unity.exe")
project_dir = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project")
log_file = Path(r"E:\Agent\TFTF-blender\tools\vortex\unity_scene_build.log")

cmd = [
    str(unity_exe),
    "-batchmode",
    "-quit",
    "-projectPath", str(project_dir),
    "-executeMethod", "BuildVortexInspectionScene.Build",
    "-logFile", str(log_file)
]

print(f"[*] Running Unity command: {' '.join(cmd)}")
res = subprocess.run(cmd)
print(f"[*] Unity exited with code: {res.returncode}")

if log_file.exists():
    print(f"\n--- Unity Log (last 40 lines) ---")
    lines = log_file.read_text(encoding="utf-8", errors="ignore").splitlines()
    for l in lines[-40:]:
        print(l)
else:
    print("[!] Log file not found!")
