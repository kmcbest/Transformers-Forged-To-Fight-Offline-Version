import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess

cmd = ["adb", "logcat", "-d", "-v", "time"]
res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

lines = res.stdout.splitlines()

capture = False
collected = []
for line in lines:
    if "11-15 21:53:30" in line:
        capture = True
    if "11-15 21:56:00" in line:
        capture = False
    if capture:
        # print if it involves kabam, bigrobot, ActivityManager, Unity, or AndroidRuntime
        if any(w in line for w in ["bigrobot", "kabam", "Unity", "AndroidRuntime", "ActivityManager", "Zygote", "DEBUG", "CRASH"]):
            collected.append(line)

print(f"Collected {len(collected)} lines:")
for c in collected:
    print(c)
