import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess

def dump_range():
    res = subprocess.run(["adb", "logcat", "-d"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    lines = res.stdout.splitlines()

    target_pids = {"22416", "16745", "23633"}
    captured = []
    for l in lines:
        # Check if line time is between 20:16:20 and 20:17:25
        if ("11-15 20:16:" in l or "11-15 20:17:" in l):
            # If from target pid or mentions bigrobot or crash or signal or unity
            if any(f" {pid} " in l for pid in target_pids) or any(k in l.lower() for k in ["bigrobot", "dothook", "sigsegv", "fault", "crash", "fatal", "backtrace", "abort", "exception"]):
                captured.append(l)

    print(f"Captured {len(captured)} lines during crash window 20:16..20:17")
    for l in captured:
        print(l)

if __name__ == "__main__":
    dump_range()
