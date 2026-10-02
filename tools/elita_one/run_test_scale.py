import subprocess
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
PROJECT_DIR = ROOT / "toolchain" / "unity_build_project"
UNITY_EXE = ROOT / "toolchain" / "Unity_2020.3.31f1" / "Editor" / "Unity.exe"
LOG_FILE = PROJECT_DIR / "test_scale.log"

cmd = [
    str(UNITY_EXE),
    "-batchmode",
    "-quit",
    "-projectPath", str(PROJECT_DIR),
    "-executeMethod", "TestCheckElitaScale.Run",
    "-logFile", str(LOG_FILE)
]

res = subprocess.run(cmd)
print("Finished with return code:", res.returncode)
if LOG_FILE.exists():
    for line in LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        if "Importer properties" in line or "bounds" in line or "localScale" in line or "Error" in line:
            print(line)
