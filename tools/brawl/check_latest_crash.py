import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess

res = subprocess.run(["adb", "logcat", "-d"], capture_output=True, text=True, encoding="utf-8", errors="replace")
lines = res.stdout.splitlines()

death_indices = []
for idx, l in enumerate(lines):
    if "Process com.kabam.bigrobot" in l and "has died" in l:
        death_indices.append((idx, l))

print(f"Total death points found: {len(death_indices)}")
# Print the last 3 death points with context
for idx, dl in death_indices[-3:]:
    print(f"\n=================== DEATH: {dl} (line {idx}) ===================")
    start = max(0, idx - 80)
    end = min(len(lines), idx + 10)
    for i in range(start, end):
        print(f"[{i}] {lines[i]}")
