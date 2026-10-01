import subprocess
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Get current PID
res_pid = subprocess.run(["adb", "shell", "pidof", "com.kabam.bigrobot"], capture_output=True, text=True)
pid = res_pid.stdout.strip()
print(f"Current PID: {pid}")

if not pid:
    print("Process not running, exiting.")
    sys.exit(0)

# Dump logcat for this PID
res_log = subprocess.run(["adb", "logcat", "-d", "--pid", pid], capture_output=True, text=True, encoding='utf-8', errors='replace')
lines = res_log.stdout.splitlines()
print(f"Total lines for PID {pid}: {len(lines)}")
for l in lines[-100:]:
    print(l)

# Also capture screenshot
subprocess.run(["adb", "shell", "screencap", "-p", "/sdcard/screen.png"])
subprocess.run(["adb", "pull", "/sdcard/screen.png", "tools/current_screen.png"])
print("Screenshot pulled to tools/current_screen.png")
