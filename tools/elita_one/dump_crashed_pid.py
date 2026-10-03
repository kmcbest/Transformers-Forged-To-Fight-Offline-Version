import subprocess

cmd = ["adb", "-s", "192.168.123.108:35023", "logcat", "-d"]
p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

pid_lines = []
for line in p.stdout.splitlines():
    if " 22217 " in line:
        pid_lines.append(line)

print(f"Total lines for PID 22217: {len(pid_lines)}")
for line in pid_lines[-350:-180]:
    print(line)
