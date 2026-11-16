import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
import re

def search():
    res = subprocess.run(["adb", "logcat", "-d"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    lines = res.stdout.splitlines()

    print("=== 1. Checking process deaths for com.kabam.bigrobot ===")
    for l in lines:
        if "com.kabam.bigrobot" in l and any(k in l for k in ["died", "kill", "force", "crash", "stop", "exit", "fatal", "exception", "abort", "sig"]):
            print("  ", l)

    print("\n=== 2. Checking lines containing 'brawl' ===")
    brawl_lines = [l for l in lines if "brawl" in l.lower()]
    print(f"Total 'brawl' lines: {len(brawl_lines)}")
    for l in brawl_lines[-50:]:
        print("  ", l)

    print("\n=== 3. Checking [dothook] logs ===")
    dothook_lines = [l for l in lines if "dothook" in l.lower()]
    print(f"Total dothook lines: {len(dothook_lines)}")
    for l in dothook_lines[-50:]:
        print("  ", l)

    print("\n=== 4. Checking Unity logs around the time of death ===")
    unity_lines = [l for l in lines if " Unity " in l]
    print(f"Total Unity lines: {len(unity_lines)}")
    for l in unity_lines[-50:]:
        print("  ", l)

if __name__ == "__main__":
    search()
