import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
from pathlib import Path

unity_exe = Path(r"E:\Agent\TFTF-blender\toolchain\Unity_2020.3.31f1\Editor\Unity.exe")
project_dir = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project")
log_file = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d\scratch\unity_rebuild_meshes.log")

cmd = [
    str(unity_exe),
    "-batchmode",
    "-quit",
    "-projectPath", str(project_dir),
    "-executeMethod", "BuildStrongarmCorrectedMeshes.Run",
    "-logFile", str(log_file),
]

print(f"[*] Running Unity: {' '.join(cmd)}")
res = subprocess.run(cmd)
print(f"[*] Unity exited with code: {res.returncode}")

if log_file.exists():
    lines = log_file.read_text(encoding="utf-8", errors="ignore").splitlines()
    print("\n--- Key Lines ---")
    for l in lines:
        if any(k in l for k in ("[BuildStrongarmCorrectedMeshes]", "[VerifyShot]", "Error", "Exception", "CS0", "Shader")):
            print(" ", l)
    print("\n--- Tail (30 lines) ---")
    for l in lines[-30:]:
        print(" ", l)
else:
    print("[!] Log file not found!")
