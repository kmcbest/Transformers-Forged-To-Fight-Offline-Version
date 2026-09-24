# -*- coding: utf-8 -*-
import sys
import shutil
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

backup_dir = Path("demolishor_backup")

# 1. Assets
assets_redeco = Path("assets_redeco")
assets_redeco.mkdir(parents=True, exist_ok=True)
bundle_src = backup_dir / "assets" / "demolishor_gs.assetbundle"
if bundle_src.exists():
    shutil.copy2(bundle_src, assets_redeco / bundle_src.name)
    print(f"[✓] Restored {bundle_src} -> {assets_redeco}")

for p in (backup_dir / "assets" / "portraits").glob("*"):
    shutil.copy2(p, assets_redeco / p.name)
    print(f"[✓] Restored portrait {p.name}")

# 2. Unity project assets
unity_demo_dir = Path("toolchain/unity_build_project/Assets/Demolishor")
unity_demo_dir.mkdir(parents=True, exist_ok=True)
for item in (backup_dir / "unity_project" / "Assets" / "Demolishor").glob("*"):
    shutil.copy2(item, unity_demo_dir / item.name)
    print(f"[✓] Restored Unity Asset: {item.name}")

unity_editor_dir = Path("toolchain/unity_build_project/Assets/Editor")
unity_editor_dir.mkdir(parents=True, exist_ok=True)
for item in (backup_dir / "unity_project" / "Assets" / "Editor").glob("*"):
    shutil.copy2(item, unity_editor_dir / item.name)
    print(f"[✓] Restored Unity Editor: {item.name}")

# 3. Apply git patch
patch_file = backup_dir / "patches" / "demolishor_code_changes.patch"
if patch_file.exists():
    res = subprocess.run(["git", "apply", str(patch_file)], capture_output=True, text=True)
    if res.returncode == 0:
        print("[✓] Successfully applied demolishor_code_changes.patch")
    else:
        print(f"[!] Git apply warning/error: {res.stderr}")
else:
    print(f"[!] Patch file not found: {patch_file}")

print("\n[✓] All Demolishor work restored to current branch.")
