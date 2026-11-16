import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess

res = subprocess.run(["adb", "logcat", "-d"], capture_output=True, text=True, encoding="utf-8", errors="replace")
lines = res.stdout.splitlines()

for i, l in enumerate(lines):
    if "Process com.kabam.bigrobot (pid 22416) has died" in l or "Process com.kabam.bigrobot (pid 16745) has died" in l or "Process com.kabam.bigrobot (pid 23633) has died" in l:
        print(f"==================== DIE AT LINE {i} ====================")
        start = max(0, i - 40)
        end = min(len(lines), i + 10)
        for j in range(start, end):
            print(f"{j}: {lines[j]}")
