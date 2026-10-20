import subprocess
from pathlib import Path

unity_exe = Path(r"E:\Agent\TFTF-blender\toolchain\Unity_2020.3.31f1\Editor\Unity.exe")
project_dir = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project")
log_file = project_dir / "unity_run.log"

cmd = [
    str(unity_exe),
    "-batchmode",
    "-quit",
    "-projectPath", str(project_dir),
    "-executeMethod", "SetupToxitronScene.Setup",
    "-logFile", str(log_file)
]

print(f"Running: {' '.join(cmd)}")
res = subprocess.run(cmd, timeout=120)
print(f"Unity exit code: {res.returncode}")

if log_file.exists():
    lines = log_file.read_text(encoding='utf-8', errors='ignore').splitlines()
    print(f"Log lines: {len(lines)}")
    for line in lines[-25:]:
        print(line)
else:
    print("Log file was not created!")
