# -*- coding: utf-8 -*-
import sys
import os
import zipfile
from pathlib import Path
import subprocess

sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = Path(__file__).resolve().parent.parent
TOOLCHAIN_DIR = ROOT_DIR / "toolchain"
UNITY_EXE = TOOLCHAIN_DIR / "Unity_2020.3.31f1" / "Editor" / "Unity.exe"
BLENDER_EXE = TOOLCHAIN_DIR / "blender" / "blender.exe"
BACKUP_ZIP = ROOT_DIR / "demolishor_backup.zip"

print("=== 1. Checking Toolchain Invocation & License ===")
# Test Blender
print(f"Blender binary: {BLENDER_EXE} (Exists: {BLENDER_EXE.exists()})")
try:
    res = subprocess.run([str(BLENDER_EXE), "-b", "--version"], capture_output=True, text=True, timeout=15)
    print(f"[✓] Blender headless execution success:\n    {res.stdout.splitlines()[0]}")
except Exception as e:
    print(f"[!] Blender headless execution failed: {e}")

# Test Unity headless execution and license
print(f"\nUnity binary: {UNITY_EXE} (Exists: {UNITY_EXE.exists()})")
test_proj = TOOLCHAIN_DIR / "unity_license_check"
test_proj.mkdir(parents=True, exist_ok=True)
test_log = test_proj / "unity_check.log"

try:
    cmd = [
        str(UNITY_EXE),
        "-batchmode",
        "-quit",
        "-createProject", str(test_proj),
        "-logFile", str(test_log)
    ]
    print(f"[*] Running Unity headless test with log: {test_log}...")
    res = subprocess.run(cmd, timeout=60)
    print(f"[*] Unity process exited with code: {res.returncode}")
    if test_log.exists():
        content = test_log.read_text(encoding='utf-8', errors='ignore')
        lines = content.splitlines()
        print(f"[*] Log total lines: {len(lines)}")
        # Check for licensing keywords
        license_lines = [l for l in lines if any(k in l.lower() for k in ["license", "licensing", "batchmode", "exiting", "error"])]
        print("--- Key Log Snippets ---")
        for l in license_lines[:20]:
            print("   ", l)
        if any("no valid license found" in l.lower() for l in lines):
            print("[!] WARNING: Unity reported no valid license found!")
        elif res.returncode == 0:
            print("[✓] Unity headless project creation and batchmode initialization SUCCEEDED!")
    else:
        print("[!] test_log not found!")
except Exception as e:
    print(f"[!] Unity test failed: {e}")

print("\n=== 2. Inspecting demolishor_backup.zip ===")
if not BACKUP_ZIP.exists():
    print(f"[!] Backup zip not found at: {BACKUP_ZIP}")
    sys.exit(1)

print(f"Backup file: {BACKUP_ZIP} ({BACKUP_ZIP.stat().st_size / (1024*1024):.2f} MB)")
with zipfile.ZipFile(BACKUP_ZIP, 'r') as zf:
    infolist = zf.infolist()
    print(f"Total entries in zip: {len(infolist)}")
    print("\n--- Zip File Entries ---")
    for info in infolist:
        is_dir = info.is_dir() or info.filename.endswith('/')
        size_str = f"{info.file_size:>10,d} B" if not is_dir else "     <DIR>   "
        print(f"{size_str}  {info.filename}")
