import subprocess
import os

unity_exe = r"E:\Agent\TFTF-blender\toolchain\Unity_2020.3.31f1\Editor\Unity.exe"

print("Unity exe:", unity_exe)
cmd = [
    unity_exe,
    "-batchmode",
    "-quit",
    "-projectPath", r"E:\Agent\TFTF-blender\toolchain\unity_build_project",
    "-executeMethod", "SampleVehicleAnimation.Run",
    "-logFile", r"E:\Agent\TFTF-blender\unity_sample.log"
]
print("Running Unity...")
res = subprocess.run(cmd)
print("Exit code:", res.returncode)

log_path = r"E:\Agent\TFTF-blender\unity_sample.log"
if os.path.exists(log_path):
    with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            if "Sample at t=" in line or "Bone8" in line or "transformed pos=" in line:
                print(line.strip())
