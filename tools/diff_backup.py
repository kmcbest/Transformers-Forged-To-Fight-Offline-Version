# -*- coding: utf-8 -*-
import sys
import os
import zipfile
import hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
ZIP_PATH = ROOT / "demolishor_backup.zip"

def md5_bytes(data):
    return hashlib.md5(data).hexdigest()

def md5_file(path):
    if not path.exists():
        return None
    return hashlib.md5(path.read_bytes()).hexdigest()

zf = zipfile.ZipFile(ZIP_PATH)

# Mapping from zip paths to potential destination paths in repo
mapping_rules = [
    # (zip_prefix, target_prefix, category_name)
    ("demolishor_backup/assets/portraits/", ROOT / "assets_redeco", "Portraits"),
    ("demolishor_backup/assets/demolishor_gs.assetbundle", ROOT / "assets_redeco" / "demolishor_gs.assetbundle", "Runtime Character Bundle"),
    ("demolishor_backup/unity_project/", ROOT / "toolchain" / "unity_build_project", "Unity Headless Build Project"),
    ("demolishor_backup/data/", ROOT / "tools" / "demolishor", "Ground Truth Data"),
    ("demolishor_backup/textures_processed/", ROOT / "tools" / "demolishor" / "textures_processed", "Processed Textures"),
    ("demolishor_backup/scripts/", ROOT / "tools" / "demolishor", "Python Pipelines & Scripts"),
    ("demolishor_backup/patches/", ROOT / "patches", "Code Patches"),
    ("demolishor_backup/README.md", ROOT / "tools" / "demolishor" / "BACKUP_README.md", "Documentation"),
]

analysis = {
    "identical": [],
    "different": [],
    "missing_in_repo": []
}

for item in zf.infolist():
    if item.is_dir() or item.filename.endswith('/'):
        continue
    fname = item.filename
    zip_bytes = zf.read(fname)
    zip_hash = md5_bytes(zip_bytes)
    
    # Determine destination
    dest = None
    category = "Other"
    
    if fname.startswith("demolishor_backup/assets/portraits/"):
        rel = fname[len("demolishor_backup/assets/portraits/"):]
        dest = ROOT / "assets_redeco" / rel
        category = "Portraits (assets_redeco/)"
    elif fname == "demolishor_backup/assets/demolishor_gs.assetbundle":
        dest = ROOT / "assets_redeco" / "demolishor_gs.assetbundle"
        category = "Character AssetBundle (assets_redeco/)"
    elif fname.startswith("demolishor_backup/unity_project/"):
        rel = fname[len("demolishor_backup/unity_project/"):]
        dest = ROOT / "toolchain" / "unity_build_project" / rel
        category = "Unity Headless Build Project (toolchain/unity_build_project/)"
    elif fname.startswith("demolishor_backup/data/"):
        rel = fname[len("demolishor_backup/data/"):]
        # Data might be in tools/demolishor or tools/demolishor/ironhide_extracted
        dest1 = ROOT / "tools" / "demolishor" / rel
        dest2 = ROOT / "tools" / "demolishor" / "ironhide_extracted" / rel
        if dest1.exists():
            dest = dest1
        elif dest2.exists():
            dest = dest2
        else:
            dest = dest1
        category = "Ground Truth Data (tools/demolishor/)"
    elif fname.startswith("demolishor_backup/textures_processed/"):
        rel = fname[len("demolishor_backup/textures_processed/"):]
        dest = ROOT / "tools" / "demolishor" / "textures_processed" / rel
        category = "Processed Textures (tools/demolishor/textures_processed/)"
    elif fname.startswith("demolishor_backup/scripts/"):
        rel = fname[len("demolishor_backup/scripts/"):]
        dest = ROOT / "tools" / "demolishor" / rel
        category = "Python Scripts (tools/demolishor/)"
    elif fname.startswith("demolishor_backup/patches/"):
        rel = fname[len("demolishor_backup/patches/"):]
        dest = ROOT / "patches" / rel
        category = "Patches (patches/)"
    elif fname == "demolishor_backup/README.md":
        dest = ROOT / "tools" / "demolishor" / "README.md"
        category = "Documentation"
        
    entry = {
        "zip_path": fname,
        "target_path": dest,
        "category": category,
        "size": item.file_size
    }
    
    if dest and dest.exists():
        target_hash = md5_file(dest)
        if target_hash == zip_hash:
            analysis["identical"].append(entry)
        else:
            entry["target_size"] = dest.stat().st_size
            analysis["different"].append(entry)
    else:
        analysis["missing_in_repo"].append(entry)

print(f"Total files in zip: {len(analysis['identical']) + len(analysis['different']) + len(analysis['missing_in_repo'])}")
print(f"Identical already in repo: {len(analysis['identical'])}")
print(f"Different content in repo: {len(analysis['different'])}")
print(f"Missing in repo:           {len(analysis['missing_in_repo'])}")

if analysis["different"]:
    print("\n=== Files with Different Content ===")
    for e in analysis["different"]:
        print(f"  [{e['category']}] {e['zip_path']} ({e['size']} B) vs {e['target_path']} ({e['target_size']} B)")

if analysis["missing_in_repo"]:
    print("\n=== Files Missing in Repo (Grouped by Category) ===")
    cats = {}
    for e in analysis["missing_in_repo"]:
        cats.setdefault(e['category'], []).append(e)
    for c, items in cats.items():
        print(f"\n--- {c} ({len(items)} files) ---")
        for e in items:
            print(f"  {e['zip_path']} -> {e['target_path']}")
