import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
import re

cmd = ["adb", "logcat", "-d", "-v", "time"]
res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

lines = res.stdout.splitlines()

pids = set()
for line in lines:
    if "com.kabam.bigrobot" in line:
        m = re.search(r"pid=(\d+)", line)
        if m:
            pids.add(int(m.group(1)))
        m2 = re.search(r"\(pid\s*(\d+)\)", line)
        if m2:
            pids.add(int(m2.group(1)))
        m3 = re.search(r"proc:com\.kabam\.bigrobot", line)
        # check line prefix
        parts = line.split()
        if len(parts) > 2 and parts[0] == "11-15":
            print(line)

print("Found PIDs:", pids)
