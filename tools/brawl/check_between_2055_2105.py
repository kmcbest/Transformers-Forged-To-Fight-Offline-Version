import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess

res = subprocess.run(["adb", "logcat", "-d", "-t", "11-15 20:55:00.000"], capture_output=True, text=True, encoding="utf-8", errors="replace")
lines = res.stdout.splitlines()

print(f"Total lines since 20:55:00: {len(lines)}")
for l in lines:
    if "bigrobot" in l or "TFTFHOOK" in l or "6630" in l or "5577" in l:
        print(l)
