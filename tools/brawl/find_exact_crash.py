import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess

def inspect():
    # 1. Check current process of bigrobot
    res = subprocess.run(["adb", "shell", "pidof", "com.kabam.bigrobot"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(f"Current com.kabam.bigrobot PID: {res.stdout.strip()}")

    # 2. Check tombstones if accessible
    res_t = subprocess.run(["adb", "shell", "ls", "-lt", "/data/tombstones"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(f"Tombstones:\n{res_t.stdout.strip()[:1000]}")

    # 3. Pull last 20000 lines of logcat and search for crash traces from bigrobot
    print("\nScanning logcat for crash events...")
    res_log = subprocess.run(["adb", "logcat", "-d", "-t", "30000"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    lines = res_log.stdout.splitlines()
    print(f"Total lines: {len(lines)}")

    crashes = []
    capture = False
    count = 0
    for l in lines:
        if "FATAL SIGNAL" in l or "DEBUG   : *** ***" in l or "crash_dump" in l or "SIGSEGV" in l or "NullReferenceException" in l or "dothook" in l:
            capture = True
            count = 40
        if capture:
            crashes.append(l)
            count -= 1
            if count <= 0:
                capture = False

    print(f"\nCrash / Signal / dothook log count: {len(crashes)}")
    for l in crashes[-120:]:
        print(l)

if __name__ == "__main__":
    inspect()
