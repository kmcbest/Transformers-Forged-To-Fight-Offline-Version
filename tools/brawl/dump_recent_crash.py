import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess

cmd = ["adb", "logcat", "-d", "-v", "time"]
res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

lines = res.stdout.splitlines()
target_lines = []
for line in lines:
    if line.startswith("11-15 21:5"):
        # Lines between 21:50:00 and 21:59:59
        if any(k in line.lower() for k in ["kabam", "bigrobot", "zygote", "fatal", "crash", "unity", "sig", "died", "kill"]):
            target_lines.append(line)

print(f"Found {len(target_lines)} matching lines:")
for l in target_lines[-50:]:
    print(l)
