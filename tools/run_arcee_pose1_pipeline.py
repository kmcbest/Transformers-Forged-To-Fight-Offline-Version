import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
from pathlib import Path
import inject_arcee_showroom_pose1

UNITY = r"D:\Agent\tftf\toolchain\Unity_2020.3.31f1\Editor\Unity.exe"
PROJ = r"D:\Agent\tftf\unity_lifeline"

def main():
    subprocess.run(["taskkill", "/F", "/IM", "Unity.exe"], capture_output=True)

    print("[1/3] Exporting refined Arcee Pose 1 JSON via Unity...")
    r1 = subprocess.run([
        UNITY, "-batchmode", "-quit", "-projectPath", PROJ,
        "-executeMethod", "ExportArceePose1Data.Run",
        "-logFile", r"D:\Agent\tftf\build\unity_export_pose1_v2.log"
    ], timeout=120)
    if r1.returncode != 0:
        raise RuntimeError(f"ExportArceePose1Data failed with code {r1.returncode}")

    print("[2/3] Injecting 130 native channels into TeamSelect_Female_idle...")
    inject_arcee_showroom_pose1.main()

    print("[3/3] Verifying under real game animator_char_lw (FE_Idle, iKOnFeet=True)...")
    r2 = subprocess.run([
        UNITY, "-batchmode", "-quit", "-projectPath", PROJ,
        "-executeMethod", "VerifyRealGameAnimator.Run",
        "-logFile", r"D:\Agent\tftf\build\unity_verify_realgame_v2.log"
    ], timeout=120)
    if r2.returncode != 0:
        raise RuntimeError(f"VerifyRealGameAnimator failed with code {r2.returncode}")

    print("[OK] Full pipeline completed cleanly!")

if __name__ == "__main__":
    main()
