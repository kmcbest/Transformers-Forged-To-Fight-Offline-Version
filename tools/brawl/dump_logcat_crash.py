import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess

def check_crash():
    print("=== Checking adb logcat -b crash ===")
    res = subprocess.run(["adb", "logcat", "-b", "crash", "-d"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(res.stdout[-3000:] if len(res.stdout) > 3000 else res.stdout)

    print("\n=== Checking logcat for com.kabam.hook or transformer or Unity ===")
    res2 = subprocess.run(["adb", "logcat", "-d", "-t", "5000"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    lines = res2.stdout.splitlines()
    matches = []
    for l in lines:
        if any(w in l.lower() for w in ["kabam", "transformer", "brawl", "dothook", "sigsegv", "backtrace", "fatal signal", "aborting"]):
            matches.append(l)
    print(f"Total matching lines found: {len(matches)}")
    for l in matches[-80:]:
        print(l)

if __name__ == "__main__":
    check_crash()
