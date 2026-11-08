import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
from pathlib import Path

UNITY_EXE = Path(r"E:\Agent\TFTF-blender\toolchain\Unity_2020.3.31f1\Editor\Unity.exe")
PACKER = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d\scratch\unity_ab_packer")
LOG = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d\scratch\export_vh_obj.log")

cmd = [
    str(UNITY_EXE),
    "-batchmode",
    "-nographics",
    "-quit",
    "-projectPath", str(PACKER),
    "-executeMethod", "ExportVhObj.Run",
    "-logFile", str(LOG)
]

print("Running ExportVhObj in Unity...")
res = subprocess.run(cmd)
print("Exit code:", res.returncode)
if LOG.exists():
    lines = LOG.read_text(encoding="utf-8", errors="replace").splitlines()
    for l in lines[-30:]:
        print(l)
