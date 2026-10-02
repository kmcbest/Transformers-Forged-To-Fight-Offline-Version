import sys
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
PROJECT_DIR = ROOT / "toolchain" / "unity_build_project"
UNITY_EXE = ROOT / "toolchain" / "Unity_2020.3.31f1" / "Editor" / "Unity.exe"
LOG_FILE = PROJECT_DIR / "unity_build_elita.log"
OUT_BUNDLE = PROJECT_DIR / "AssetBundles" / "elita_one_mesh.assetbundle"

print(f"[*] Running Unity Editor headless build for Elita One...")
cmd = [
    str(UNITY_EXE),
    "-batchmode",
    "-quit",
    "-projectPath", str(PROJECT_DIR),
    "-executeMethod", "AssetBundleBuilder.BuildElitaOneBundles",
    "-logFile", str(LOG_FILE)
]

res = subprocess.run(cmd)
print(f"[+] Unity process finished with return code: {res.returncode}")

if OUT_BUNDLE.exists():
    print(f"\n[✓] SUCCESS: AssetBundle built: {OUT_BUNDLE} ({OUT_BUNDLE.stat().st_size / (1024*1024):.2f} MB)")
else:
    print(f"\n[!] AssetBundle not found at {OUT_BUNDLE}. Checking log...")
    if LOG_FILE.exists():
        lines = LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in lines[-40:]:
            print("  ", line)
