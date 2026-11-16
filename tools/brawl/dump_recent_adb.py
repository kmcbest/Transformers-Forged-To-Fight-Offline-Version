import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess

res = subprocess.run(["adb", "logcat", "-d"], capture_output=True, text=True, encoding="utf-8", errors="replace")
lines = res.stdout.splitlines()

bigrobot_lines = [l for l in lines if "bigrobot" in l or "TFTFHOOK" in l or "DEBUG" in l or "CRASH" in l]
print(f"Total relevant lines: {len(bigrobot_lines)}")
for l in bigrobot_lines[-50:]:
    print(l)
