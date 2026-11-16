import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess

res = subprocess.run(["adb", "logcat", "-d"], capture_output=True, text=True, encoding="utf-8", errors="replace")
lines = res.stdout.splitlines()

target_pid = " 6630 "
p_lines = [l for l in lines if target_pid in l]

print(f"Total lines for PID 6630: {len(p_lines)}")
for l in p_lines[-60:]:
    print(l)
