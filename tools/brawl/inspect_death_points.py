import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess

def inspect_deaths():
    res = subprocess.run(["adb", "logcat", "-d"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    lines = res.stdout.splitlines()

    death_indices = []
    for idx, l in enumerate(lines):
        if "Process com.kabam.bigrobot" in l and "has died" in l:
            death_indices.append((idx, l))

    print(f"Found {len(death_indices)} death points:")
    for idx, dl in death_indices:
        print(f"\n=================== DEATH: {dl} (line {idx}) ===================")
        start = max(0, idx - 60)
        end = min(len(lines), idx + 10)
        for i in range(start, end):
            print(lines[i])

if __name__ == "__main__":
    inspect_deaths()
