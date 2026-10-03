import subprocess
import json

cmd = ["adb", "-s", "192.168.123.108:35023", "logcat", "-d"]
p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

lines = p.stdout.splitlines()
for i, line in enumerate(lines):
    if "11:48:11" in line:
        print(line)
        if "MiSight" in line or "CRASH" in line or "SIGSEGV" in line or "backtrace" in line:
            # print surrounding lines
            for j in range(max(0, i-5), min(len(lines), i+30)):
                print(f"[{j}] {lines[j]}")
            break
