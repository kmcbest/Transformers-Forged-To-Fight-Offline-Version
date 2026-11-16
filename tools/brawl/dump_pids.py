import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess

cmd = ["adb", "logcat", "-d", "-v", "time"]
res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

lines = res.stdout.splitlines()

target_pids = {"18746", "20119"}

lines_18746 = []
lines_20119 = []

for line in lines:
    for pid in target_pids:
        # standard logcat format: MM-DD HH:MM:SS.mmm LEVEL/TAG( PID):
        if f"({pid})" in line or f"({int(pid):5d})" in line or f" {pid} " in line:
            if pid == "18746":
                lines_18746.append(line)
            else:
                lines_20119.append(line)

print(f"PID 18746 lines: {len(lines_18746)}")
print(f"PID 20119 lines: {len(lines_20119)}")

print("\n--- Last 60 lines of PID 18746 ---")
for l in lines_18746[-60:]:
    print(l)

print("\n--- Last 60 lines of PID 20119 ---")
for l in lines_20119[-60:]:
    print(l)
