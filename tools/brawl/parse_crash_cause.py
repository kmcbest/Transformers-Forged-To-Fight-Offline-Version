import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess

def find_crashes():
    res = subprocess.run(["adb", "logcat", "-d"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    lines = res.stdout.splitlines()

    target_pids = ["22416", "16745", "23633"]
    # Let's also check for tombstone or crash dump in DEBUG / libc / Unity
    print("=== Searching for DEBUG / CRASH / FATAL in logcat ===")
    for idx, l in enumerate(lines):
        if any(x in l for x in ["DEBUG   :", "Fatal signal", "SIGSEGV", "SIGABRT", "tombstone", "backtrace:", "com.kabam.bigrobot"]):
            # Filter to relevant time 20:16 - 20:18
            if "20:16:" in l or "20:17:" in l or "20:18:" in l or "20:19:" in l or "20:20:" in l or "20:21:" in l:
                print(f"[{idx}] {l}")

if __name__ == "__main__":
    find_crashes()
