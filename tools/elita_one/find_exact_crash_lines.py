import subprocess

cmd = ["adb", "-s", "192.168.123.108:35023", "logcat", "-d"]
p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

collect = False
for line in p.stdout.splitlines():
    if "11:48:11.136" in line:
        collect = True
    if collect:
        print(line)
        if "CRASH" in line:
            break
