import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess

cmd = ["adb", "logcat", "-d", "-v", "time"]
res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

lines = res.stdout.splitlines()

# Find where Process 20119 exited
exit_idx = -1
for i, line in enumerate(lines):
    if "Process 20119 exited" in line:
        exit_idx = i
        break

if exit_idx != -1:
    print(f"Found exit at line {exit_idx}:")
    for j in range(max(0, exit_idx - 100), min(len(lines), exit_idx + 10)):
        print(lines[j])
else:
    print("Not found!")
