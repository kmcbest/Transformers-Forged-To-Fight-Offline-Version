#!/usr/bin/env python3
"""
unpack_and_index_apk.py

Unpacks the official Kabam 9.2.0 APK into `extracted_apk/` and builds a fast,
comprehensive JSON index `tools/apk_asset_index.json`.
Allows all subsequent tools, recoloring scripts, and analysis workflows to
read assets directly from local storage with millisecond lookup speeds.
"""

import argparse
import glob
import json
import os
import sys
import zipfile
from pathlib import Path

try:
    import UnityPy
except ImportError:
    print("Error: UnityPy is required. Install it using: pip install UnityPy")
    sys.exit(1)


def unpack_and_index(apk_path: str, extract_dir: str = "extracted_apk", index_file: str = "tools/apk_asset_index.json") -> None:
    apk_file = Path(apk_path)
    if not apk_file.is_file():
        raise FileNotFoundError(f"Input APK not found: {apk_path}")

    out_dir = Path(extract_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] Step 1: Unpacking {apk_file.name} to {out_dir}/ ...")
    with zipfile.ZipFile(apk_file, "r") as z:
        z.extractall(out_dir)

    print("[+] APK unpacked successfully!")

    print(f"[*] Step 2: Indexing all AssetBundles and assets in {out_dir}/assets/assetpack/ ...")
    assetpack_dir = out_dir / "assets" / "assetpack"

    index = {
        "apk_source": apk_file.name,
        "bundles_count": 0,
        "assets_count": 0,
        "bundles": {},
        "characters": {},
        "environments": {},
        "portraits": []
    }

    bundle_files = list(assetpack_dir.glob("**/*.assetbundle"))
    index["bundles_count"] = len(bundle_files)
    print(f"[*] Found {len(bundle_files)} AssetBundles to index...")

    total_assets = 0
    for idx, bpath in enumerate(bundle_files):
        rel_path = bpath.relative_to(out_dir).as_posix()
        bundle_name = bpath.stem
        
        bundle_entry = {
            "rel_path": rel_path,
            "size_bytes": bpath.stat().st_size,
            "assets": []
        }

        try:
            env = UnityPy.load(str(bpath))
            for obj in env.objects:
                total_assets += 1
                try:
                    tree = obj.read_typetree()
                    aname = tree.get("m_Name", "")
                except Exception:
                    aname = ""

                asset_info = {
                    "path_id": obj.path_id,
                    "type": obj.type.name,
                    "name": aname
                }
                bundle_entry["assets"].append(asset_info)

                # Classify into characters, environments, or portraits
                if "cha_" in aname or "_gs_" in aname or "_bw_" in aname or "_cin_" in aname:
                    parts = aname.split("_")
                    if len(parts) >= 2:
                        char_key = "_".join(parts[:2])
                        if char_key not in index["characters"]:
                            index["characters"][char_key] = []
                        index["characters"][char_key].append({
                            "bundle": bundle_name,
                            "type": obj.type.name,
                            "name": aname,
                            "path_id": obj.path_id
                        })
                elif any(k in aname.lower() for k in ["terrain", "ground", "bldg", "theme", "ruined", "unicron", "quintessa", "primordial"]):
                    theme_key = bundle_name
                    if theme_key not in index["environments"]:
                        index["environments"][theme_key] = []
                    index["environments"][theme_key].append({
                        "type": obj.type.name,
                        "name": aname,
                        "path_id": obj.path_id
                    })
        except Exception as e:
            print(f"  [!] Warning loading bundle {bpath.name}: {e}")

        index["bundles"][bundle_name] = bundle_entry
        if (idx + 1) % 15 == 0 or (idx + 1) == len(bundle_files):
            print(f"  [{idx+1}/{len(bundle_files)}] Indexed {bundle_name} ...")

    # Index all loose portraits in portraits_odr, questboard_odr, dialogue_odr
    for ppath in (out_dir / "assets" / "assetpack").glob("**/*portrait*.*"):
        index["portraits"].append(ppath.relative_to(out_dir).as_posix())

    index["assets_count"] = total_assets

    index_out = Path(index_file)
    index_out.parent.mkdir(parents=True, exist_ok=True)
    with open(index_out, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print(f"[+] Successfully generated index with {len(index['bundles'])} bundles and {total_assets} assets!")
    print(f"[+] Output index written to: {index_out}")


def main():
    parser = argparse.ArgumentParser(description="Unpack APK and index all assets.")
    candidates = glob.glob("com.kabam.bigrobot*.apk") + glob.glob("*.apk")
    default_apk = candidates[0] if candidates else None
    parser.add_argument("--input", "-i", default=default_apk, help="Base Kabam APK")
    parser.add_argument("--output", "-o", default="extracted_apk", help="Output directory")
    parser.add_argument("--index", default="tools/apk_asset_index.json", help="Output index JSON")
    args = parser.parse_args()

    if not args.input:
        print("Error: Base APK not found.")
        sys.exit(1)

    unpack_and_index(args.input, args.output, args.index)


if __name__ == "__main__":
    main()
