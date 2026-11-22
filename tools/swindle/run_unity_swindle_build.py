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
RENDERS_DIR = ROOT / "renders" / "swindle"
RENDERS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = RENDERS_DIR / "unity_build.log"

lock_file = PROJECT_DIR / "Temp" / "UnityLockfile"
if lock_file.exists():
    try:
        lock_file.unlink()
        print(f"  [+] Cleared stale lock: {lock_file}")
    except Exception as e:
        print(f"  [!] Failed to clear lock: {e}")

print(f"=== [Swindle] Running Unity Batchmode to Build Inspection Scene & AssetBundles ===")
print(f"  Unity: {UNITY_EXE}")
print(f"  Project: {PROJECT_DIR}")
print(f"  Log: {LOG_FILE}")

cmd = [
    str(UNITY_EXE),
    "-batchmode",
    "-quit",
    "-projectPath", str(PROJECT_DIR),
    "-executeMethod", "BuildSwindleInspectionScene.Build",
    "-logFile", str(LOG_FILE)
]

t0 = time.time()
res = subprocess.run(cmd, capture_output=True, text=True)
dt = time.time() - t0
print(f"Unity finished with exit code {res.returncode} in {dt:.1f}s")
if LOG_FILE.exists():
    log_text = LOG_FILE.read_text(encoding="utf-8", errors="replace")
    for line in log_text.splitlines()[-40:]:
        print("  [log]", line)
