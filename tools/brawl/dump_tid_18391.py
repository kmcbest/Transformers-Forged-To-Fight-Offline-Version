import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess

res = subprocess.run(["adb", "logcat", "-d", "-t", "11-15 20:57:30.000"], capture_output=True, text=True, encoding="utf-8", errors="replace")
lines = res.stdout.splitlines()

print(f"Total lines: {len(lines)}")
tid_lines = []
for l in lines:
    if "18391" in l:
        tid_lines.append(l)

print(f"Total lines for TID 18391: {len(tid_lines)}")
for l in tid_lines:
    print(l)
