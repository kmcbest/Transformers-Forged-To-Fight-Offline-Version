# -*- coding: utf-8 -*-
import sys
import os
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
ZIP_PATH = ROOT / "demolishor_backup.zip"

zf = zipfile.ZipFile(ZIP_PATH)

extract_plan = [
    # (zip_path, target_path)
    # 1. Unity Project
    ("demolishor_backup/unity_project/AssetBundles/demolishor_mesh.assetbundle", 
     ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "demolishor_mesh.assetbundle"),
    ("demolishor_backup/unity_project/Assets/Demolishor/cha_demolishor_main_a.png",
     ROOT / "toolchain" / "unity_build_project" / "Assets" / "Demolishor" / "cha_demolishor_main_a.png"),
    ("demolishor_backup/unity_project/Assets/Demolishor/cha_demolishor_main_a.png.meta",
     ROOT / "toolchain" / "unity_build_project" / "Assets" / "Demolishor" / "cha_demolishor_main_a.png.meta"),
    ("demolishor_backup/unity_project/Assets/Demolishor/cha_demolishor_main_NM.png",
     ROOT / "toolchain" / "unity_build_project" / "Assets" / "Demolishor" / "cha_demolishor_main_NM.png"),
    ("demolishor_backup/unity_project/Assets/Demolishor/cha_demolishor_main_NM.png.meta",
     ROOT / "toolchain" / "unity_build_project" / "Assets" / "Demolishor" / "cha_demolishor_main_NM.png.meta"),
    ("demolishor_backup/unity_project/Assets/Demolishor/cha_demolishor_main_tform_misc_RAOE.png",
     ROOT / "toolchain" / "unity_build_project" / "Assets" / "Demolishor" / "cha_demolishor_main_tform_misc_RAOE.png"),
    ("demolishor_backup/unity_project/Assets/Demolishor/cha_demolishor_main_tform_misc_RAOE.png.meta",
     ROOT / "toolchain" / "unity_build_project" / "Assets" / "Demolishor" / "cha_demolishor_main_tform_misc_RAOE.png.meta"),
    ("demolishor_backup/unity_project/Assets/Demolishor/demolishor_prepared.fbx",
     ROOT / "toolchain" / "unity_build_project" / "Assets" / "Demolishor" / "demolishor_prepared.fbx"),
    ("demolishor_backup/unity_project/Assets/Demolishor/demolishor_prepared.fbx.meta",
     ROOT / "toolchain" / "unity_build_project" / "Assets" / "Demolishor" / "demolishor_prepared.fbx.meta"),
    ("demolishor_backup/unity_project/Assets/Editor/AssetBundleBuilder.cs",
     ROOT / "toolchain" / "unity_build_project" / "Assets" / "Editor" / "AssetBundleBuilder.cs"),
    
    # 2. Patches
    ("demolishor_backup/patches/demolishor_changes.patch",
     ROOT / "patches" / "demolishor_changes.patch"),
    ("demolishor_backup/patches/demolishor_code_changes.patch",
     ROOT / "patches" / "demolishor_code_changes.patch"),
     
    # 3. Documentation
    ("demolishor_backup/README.md",
     ROOT / "tools" / "demolishor" / "BACKUP_README.md"),
]

print("=== Extracting Selected Files from demolishor_backup.zip ===")
for zip_src, dest in extract_plan:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zf.open(zip_src) as src, open(dest, "wb") as out:
        out.write(src.read())
    print(f"[✓] Extracted: {zip_src} -> {dest} ({dest.stat().st_size} bytes)")

print("\n[✓] Extraction completed successfully without any compilation.")
