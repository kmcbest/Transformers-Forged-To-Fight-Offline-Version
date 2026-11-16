import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess

def run():
    print("Checking ADB devices...")
    res = subprocess.run(["adb", "devices"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(res.stdout)

    print("Fetching last 500 lines of logcat with crash/exception/Unity/DEBUG filters...")
    log_res = subprocess.run(["adb", "logcat", "-d", "-t", "800"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    lines = log_res.stdout.splitlines()
    print(f"Total lines retrieved: {len(lines)}")
    
    # Filter interesting lines
    interesting = []
    for line in lines:
        lower = line.lower()
        if any(k in lower for k in ["fatal", "crash", "sigsegv", "nullreference", "exception", "brawl", "error", "tftf", "unity", "dothook"]):
            interesting.append(line)
            
    print(f"Filtered lines: {len(interesting)}")
    for l in interesting[-100:]:
        print(l)

if __name__ == "__main__":
    run()
