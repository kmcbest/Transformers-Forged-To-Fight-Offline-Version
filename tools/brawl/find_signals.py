import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess

res = subprocess.run(["adb", "logcat", "-d"], capture_output=True, text=True, encoding="utf-8", errors="replace")
lines = res.stdout.splitlines()

for i, line in enumerate(lines):
    if "Fatal signal" in line or "DEBUG   :" in line or "SIGSEGV" in line or "SIGABRT" in line or "Crashlytics" in line:
        # print context around it
        start = max(0, i - 5)
        end = min(len(lines), i + 25)
        print(f"--- MATCH AT LINE {i} ---")
        for j in range(start, end):
            print(lines[j])
        print("------------------------\n")
