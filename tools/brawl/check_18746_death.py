import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess

cmd = ["adb", "logcat", "-d", "-v", "time"]
res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

lines = res.stdout.splitlines()

for i, line in enumerate(lines):
    if "18746" in line and ("died" in line or "exited" in line or "kill" in line or "dead" in line):
        print(f"Line {i}: {line}")
