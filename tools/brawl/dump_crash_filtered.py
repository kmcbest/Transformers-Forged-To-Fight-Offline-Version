import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess

res = subprocess.run(["adb", "logcat", "-d", "-t", "11-15 20:57:36.000"], capture_output=True, text=True, encoding="utf-8", errors="replace")
lines = res.stdout.splitlines()

for l in lines:
    if "11-15 20:57:37.250" in l:
        break
    # Filter for any log with 6630, or Unity, or Zygote, or DEBUG, or libc, or crash
    parts = l.split()
    if len(parts) >= 3:
        pid = parts[2]
        if pid == "6630":
            print(l)
        elif any(k in l for k in ["Zygote", "DEBUG", "crash", "signal", "fatal", "Fatal", "libc", "TFTFHOOK", "com.kabam.bigrobot"]):
            print(l)
