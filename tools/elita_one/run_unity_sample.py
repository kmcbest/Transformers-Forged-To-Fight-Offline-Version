import subprocess
import os

unity_exe = r"E:\Agent\TFTF-blender\toolchain\Unity_2020.3.31f1\Editor\Unity.exe"
project_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project"
log_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\sample_arcee.log"

cmd = [
    unity_exe,
    "-quit",
    "-batchmode",
    "-projectPath", project_path,
    "-executeMethod", "ExportArceeFullMesh.Export",
    "-logFile", log_path
]

print("Launching Unity to sample Arcee animations...")
res = subprocess.run(cmd)
print("Finished with returncode:", res.returncode)

if os.path.exists(log_path):
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        for line in lines[-30:]:
            print(line.rstrip())
