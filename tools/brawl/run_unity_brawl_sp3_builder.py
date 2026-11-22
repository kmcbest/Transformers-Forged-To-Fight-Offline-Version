import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
UNITY_EXE = ROOT / "toolchain" / "Unity_2020.3.31f1" / "Editor" / "Unity.exe"
PROJECT_DIR = ROOT / "toolchain" / "unity_build_project"
RENDERS_DIR = ROOT / "renders" / "brawl_sp3"
RENDERS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = RENDERS_DIR / "unity_build.log"

lock_file = PROJECT_DIR / "Temp" / "UnityLockfile"
if lock_file.exists():
    try:
        lock_file.unlink()
        print(f"  [+] Cleared stale lock: {lock_file}")
    except Exception as e:
        print(f"  [!] Failed to clear lock: {e}")

print(f"=== Running Unity Batchmode to Build Brawl vs Rodimus SP3 Scene ===")
print(f"  Unity: {UNITY_EXE}")
print(f"  Project: {PROJECT_DIR}")
print(f"  Log: {LOG_FILE}")

cmd = [
    str(UNITY_EXE),
    "-batchmode",
    "-quit",
    "-projectPath", str(PROJECT_DIR),
    "-executeMethod", "BuildBrawlVsRodimusSP3Scene.Build",
    "-logFile", str(LOG_FILE)
]

t0 = time.time()
res = subprocess.run(cmd)
dt = time.time() - t0

print(f"\n[+] Unity finished in {dt:.1f}s with return code {res.returncode}")

if LOG_FILE.exists():
    log_text = LOG_FILE.read_text(encoding="utf-8", errors="replace")
    lines = log_text.splitlines()
    print(f"\n--- Unity Log (last 60 lines) ---")
    for l in lines[-60:]:
        print("  ", l)
else:
    print("[!] No log file produced!")

if res.returncode != 0:
    print(f"[!] Unity failed with code {res.returncode}")
    sys.exit(res.returncode)
