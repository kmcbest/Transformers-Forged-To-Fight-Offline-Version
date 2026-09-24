# -*- coding: utf-8 -*-
import sys
import os
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

HUB_URL = "https://public-cdn.cloud.unitychina.cn/hub/prod/UnityHubSetup.exe"
DEST_EXE = Path(r"d:\Agent\tftf\toolchain\downloads\UnityHubSetup.exe")
INSTALL_DIR = Path(r"d:\Agent\tftf\toolchain\UnityHub")

print("=== Downloading and Installing Unity Hub ===")
if not DEST_EXE.exists() or DEST_EXE.stat().st_size < 100 * 1024 * 1024:
    print(f"Downloading from {HUB_URL}...")
    cmd = ["curl.exe", "-L", "-C", "-", "-o", str(DEST_EXE), HUB_URL]
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print("[!] curl failed")
        sys.exit(1)

print(f"[✓] Downloaded UnityHubSetup.exe ({DEST_EXE.stat().st_size / (1024*1024):.2f} MB)")
print(f"Installing silently to: {INSTALL_DIR}...")
INSTALL_DIR.mkdir(parents=True, exist_ok=True)

# Install silently to D: drive
cmd_inst = [str(DEST_EXE), "/S", f"/D={INSTALL_DIR}"]
res_i = subprocess.run(cmd_inst)
print(f"[+] Installer exit code: {res_i.returncode}")

hub_bin = INSTALL_DIR / "Unity Hub.exe"
if hub_bin.exists():
    print(f"[✓] Successfully installed Unity Hub: {hub_bin}")
else:
    print(f"[!] Unity Hub.exe not found in {INSTALL_DIR}")
