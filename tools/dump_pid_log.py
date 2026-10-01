# -*- coding: utf-8 -*-
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

res = subprocess.run(["adb", "shell", "pidof", "com.kabam.bigrobot"], capture_output=True, text=True)
pid = res.stdout.strip()
print(f"Current PID: {pid}")

if not pid:
    print("Process not running!")
    sys.exit(0)

# Dump logcat for this PID
res_log = subprocess.run(["adb", "logcat", f"--pid={pid}", "-d"], capture_output=True, text=True, encoding='utf-8', errors='replace')
lines = res_log.stdout.splitlines()
print(f"Total lines for PID {pid}: {len(lines)}")
for l in lines[-100:]:
    print(l)
