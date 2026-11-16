import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess

res = subprocess.run(["adb", "logcat", "-d"], capture_output=True, text=True, encoding="utf-8", errors="replace")
lines = res.stdout.splitlines()

for i, l in enumerate(lines):
    if any(k in l for k in ["lmkd", "lowmemorykiller", "am_kill", "Killing 6630", "kill: send 9", "191", "SIGKILL", "OutOfMemory"]):
        if "20:57:" in l:
            print(f"[{i}] {l}")
