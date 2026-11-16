import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess

cmd = ["adb", "logcat", "-d", "-v", "time"]
res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

lines = res.stdout.splitlines()

for line in lines:
    if "(20119)" in line or " 20119 " in line:
        if "21:55:28" in line or "21:55:29" in line:
            print(line)
