import subprocess
from pathlib import Path

unity_exe = Path(r"E:\Agent\TFTF-blender\toolchain\Unity_2020.3.31f1\Editor\Unity.exe")
project_dir = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project")
log_file = project_dir / "unity_check_mats.log"

cmd = [
    str(unity_exe),
    "-batchmode",
    "-quit",
    "-projectPath", str(project_dir),
    "-executeMethod", "CheckToxitronMaterials.Check",
    "-logFile", str(log_file)
]

res = subprocess.run(cmd, timeout=120)
if log_file.exists():
    lines = log_file.read_text(encoding='utf-8', errors='ignore').splitlines()
    for l in lines:
        if "SMR:" in l or "Mat:" in l or "Mesh vertexCount:" in l:
            print(l)
