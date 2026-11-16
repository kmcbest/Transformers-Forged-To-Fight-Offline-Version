import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess

res = subprocess.run(["adb", "logcat", "-d"], capture_output=True, text=True, encoding="utf-8", errors="replace")
lines = res.stdout.splitlines()

for pid in ["22416", "16745"]:
    print(f"=== PID {pid} ===")
    p_lines = [l for l in lines if f" {pid} " in l]
    for l in p_lines[-25:]:
        print(l)
