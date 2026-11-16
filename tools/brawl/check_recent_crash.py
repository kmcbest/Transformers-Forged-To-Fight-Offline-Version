import sys
import subprocess
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

cmd = ["adb", "logcat", "-d", "-t", "3000"]
p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
lines = p.stdout.splitlines()

keywords = ["brawl", "Unity", "DEBUG", "CRASH", "Fatal", "backtrace", "SIGSEGV", "kabam"]
matches = []
for line in lines:
    if any(k.lower() in line.lower() for k in ["brawl", "crashpad", "sigsegv", "fatal signal", "exited cleanly"]):
        matches.append(line)

print(f"Total lines: {len(lines)}, matched: {len(matches)}")
for m in matches[-30:]:
    print(m)
