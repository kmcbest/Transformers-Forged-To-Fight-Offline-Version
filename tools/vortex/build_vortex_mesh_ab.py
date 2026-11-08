import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
SCRATCH = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d\scratch")
PACKER = SCRATCH / "unity_ab_packer"
UNITY_EXE = ROOT / "toolchain" / "Unity_2020.3.31f1" / "Editor" / "Unity.exe"

log_file = SCRATCH / "pack_vortex_mesh_ab.log"
cmd = [
    str(UNITY_EXE),
    "-batchmode",
    "-nographics",
    "-quit",
    "-projectPath", str(PACKER),
    "-buildTarget", "Android",
    "-executeMethod", "PackVortexMeshBundle.Build",
    "-logFile", str(log_file),
]

print("[*] Running headless Unity AssetBundle build for vortex_mesh.assetbundle...")
res = subprocess.run(cmd)
print(f"[*] Unity exited with code {res.returncode}")

if log_file.exists():
    log_text = log_file.read_text(encoding="utf-8", errors="replace")
    print(log_text[-2000:])

if res.returncode != 0:
    sys.exit(res.returncode)

ab_out = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "vortex_mesh.assetbundle"
assert ab_out.is_file(), f"Missing {ab_out} after Unity build!"
print(f"[✓] Successfully built {ab_out} ({ab_out.stat().st_size / 1024:.1f} KB)")
