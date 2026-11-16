import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess, json

res = subprocess.run(["adb", "shell", "cat", "/sdcard/Android/data/com.kabam.bigrobot/files/last_bug_report.json"], capture_output=True, text=True, encoding="utf-8", errors="replace")
try:
    data = json.loads(res.stdout)
    logs = data.get("log", [])
    print(f"Total lines in last_bug_report.json: {len(logs)}")
    for l in logs[-50:]:
        print(l)
except Exception as e:
    print("Error parsing json:", e)
    print(res.stdout[:500])
