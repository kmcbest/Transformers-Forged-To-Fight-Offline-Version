import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess

res = subprocess.run(["adb", "logcat", "-d"], capture_output=True, text=True, encoding="utf-8", errors="replace")
lines = res.stdout.splitlines()

target_pids = [" 22416 ", " 16745 ", " 23633 "]

found_lines = {pid: [] for pid in target_pids}

for l in lines:
    for pid in target_pids:
        if pid in l:
            found_lines[pid].append(l)

for pid, plines in found_lines.items():
    print(f"\n=================== LOGS FOR PID {pid.strip()} (total: {len(plines)}) ===================")
    # print the last 40 lines
    for l in plines[-40:]:
        print(l)
