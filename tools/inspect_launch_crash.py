# -*- coding: utf-8 -*-
import subprocess
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("=== Launching App and Capturing Logcat ===")
# 1. Clear logcat
subprocess.run(["adb", "logcat", "-c"])

# 2. Stop app
subprocess.run(["adb", "shell", "am", "force-stop", "com.kabam.bigrobot"])
time.sleep(1)

# 3. Start app
res = subprocess.run(["adb", "shell", "am", "start", "-n", "com.kabam.bigrobot/com.explodingbarrel.Activity"], capture_output=True, text=True)
print("Start command output:", res.stdout.strip())

# 4. Wait for launch
time.sleep(4)

# 5. Check if process is running
res_pid = subprocess.run(["adb", "shell", "pidof", "com.kabam.bigrobot"], capture_output=True, text=True)
pid = res_pid.stdout.strip()
print(f"Current PID of com.kabam.bigrobot: {pid if pid else 'NOT RUNNING (CRASHED)'}")

# 6. Dump logcat
res_log = subprocess.run(["adb", "logcat", "-d"], capture_output=True, text=True, encoding='utf-8', errors='replace')
lines = res_log.stdout.splitlines()

print(f"\nTotal log lines captured: {len(lines)}")
print("\n--- Key Log Lines (FATAL, CRASH, dothook, inapk, Unity, AndroidRuntime) ---")
matched = []
for line in lines:
    if any(k in line for k in ["FATAL", "DEBUG", "CRASH", "AndroidRuntime", "dothook", "inapk", "Kabam", "explodingbarrel", "Unity", "SEGV", "SIG"]):
        matched.append(line)

for l in matched[-80:]:
    print(l)
