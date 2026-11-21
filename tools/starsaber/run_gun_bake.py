import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
import os
from pathlib import Path

UNITY_EXE = Path(r"E:\Agent\TFTF-blender\toolchain\Unity_2020.3.31f1\Editor\Unity.exe")
PROJECT_DIR = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project")
LOG_FILE = Path(r"E:\Agent\TFTF-blender\scratch\unity_gun_bake.log")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def run_method(method_name: str):
    print(f"=== [StarSaber] Launching Unity Batchmode: {method_name} ===")
    cmd = [
        str(UNITY_EXE),
        "-batchmode",
        "-quit",
        "-projectPath", str(PROJECT_DIR),
        "-executeMethod", method_name,
        "-logFile", str(LOG_FILE)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Unity exit code: {res.returncode}")
    if LOG_FILE.exists():
        with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
            log_lines = f.readlines()
        print("--- Unity Log Highlights ---")
        for line in log_lines[-35:]:
            print(line.rstrip())

# 1. Extract gun mesh & bake starsaber_mesh.assetbundle
run_method("ExtractGunMeshAndBake.Execute")

import time
time.sleep(3)

# 2. Align gun in studio & render images & save config
run_method("AlignGunInStudio.Execute")
