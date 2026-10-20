import subprocess
from pathlib import Path

unity_exe = Path(r"E:\Agent\TFTF-blender\toolchain\Unity_2020.3.31f1\Editor\Unity.exe")
project_dir = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project")
log_file = project_dir / "unity_showcase.log"

cmd = [
    str(unity_exe),
    "-batchmode",
    "-quit",
    "-projectPath", str(project_dir),
    "-executeMethod", "SetupAndRenderToxitron.Execute",
    "-logFile", str(log_file)
]

print(f"Running: {' '.join(cmd)}")
res = subprocess.run(cmd, timeout=120)
print(f"Unity exit code: {res.returncode}")

brain_dir = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\76f5ec0f-a15b-490d-aeb0-5237fdbedbfa")
fullbody = brain_dir / "toxitron_unity_fullbody.png"
closeup = brain_dir / "toxitron_unity_torso_closeup.png"
persp = brain_dir / "toxitron_unity_perspective.png"

for p in [fullbody, closeup, persp]:
    if p.exists():
        print(f"[OK] Captured {p.name}: {p.stat().st_size} bytes")
    else:
        print(f"[ERR] {p.name} not found!")
