import subprocess

cmd = ["adb", "-s", "192.168.123.108:35023", "logcat", "-d"]
p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

pid_lines = []
for line in p.stdout.splitlines():
    if " 21437 " in line:
        pid_lines.append(line)

print(f"Total lines for PID 21437: {len(pid_lines)}")
for i, line in enumerate(pid_lines):
    if "FIXFIGHT" in line:
        print(f"Found FIXFIGHT at {i}:")
        for j in range(max(0, i-5), min(len(pid_lines), i+60)):
            print(f"[{j}] {pid_lines[j]}")
        break
