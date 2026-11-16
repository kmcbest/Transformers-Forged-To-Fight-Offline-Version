import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
import re

def search_game_logs():
    res = subprocess.run(["adb", "logcat", "-d"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    lines = res.stdout.splitlines()
    print(f"Total lines in full logcat: {len(lines)}")

    # Find all PIDs associated with com.kabam.bigrobot
    pids = set()
    for l in lines:
        if "com.kabam.bigrobot" in l:
            # Match PID
            m = re.search(r'\s+(\d+)\s+\d+\s+[VDIWEF]\s+', l)
            if m:
                pids.add(m.group(1))
    print(f"Found bigrobot PIDs: {pids}")

    # For each PID or any line containing Unity or dothook or brawl, collect relevant lines
    game_lines = []
    for l in lines:
        if any(f" {pid} " in l for pid in pids) or "dothook" in l or "brawl" in l.lower():
            game_lines.append(l)

    print(f"Total game-related lines: {len(game_lines)}")
    # Print the last 200 lines
    for l in game_lines[-200:]:
        print(l)

if __name__ == "__main__":
    search_game_logs()
