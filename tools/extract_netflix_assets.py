#!/usr/bin/env python3
"""
extract_netflix_assets.py

Extracts and transcodes exclusive Netflix edition characters (Chromia & Dead End)
and shared move/animation libraries from a user-supplied Netflix APK/XAPK to
Unity 2020 compatible AssetBundles for offline packaging.

Usage:
    python tools/extract_netflix_assets.py --input "path/to/default.apk"
    python tools/extract_netflix_assets.py --input "path/to/TRANSFORMERS.xapk"
"""

import argparse
import io
import os
import shutil
import sys
import zipfile
from pathlib import Path

try:
    import UnityPy
except ImportError:
    print("Error: UnityPy is required. Install it using: pip install UnityPy lz4")
    sys.exit(1)


def transcode_assetbundle_to_2020(bundle_bytes: bytes) -> bytes:
    """Transcodes a Unity 2021 AssetBundle to Unity 2020.3.31f1 format."""
    env = UnityPy.load(bundle_bytes)
    bf = env.file
    bf.version = 7
    bf.version_engine = "2020.3.31f1"
    bf.version_player = "5.x.x"

    for sub in bf.files.values():
        if hasattr(sub, "version"):
            sub.version = "2020.3f1"
        if hasattr(sub, "unity_version"):
            sub.unity_version = "2020.3.31f1"

    return bf.save(packer="lz4")


def patch_chromia_bundle(bundle_bytes: bytes) -> bytes:
    """Fixes Chromia S3 axe material pointer and projectile PrefabList for Unity 2020."""
    env = UnityPy.load(bundle_bytes)

    for obj in env.objects:
        # 1. Update S3 axe SkinnedMeshRenderer material from broken 5363102012143072554 to valid axe material 1952278396157663915
        if obj.type.name == "SkinnedMeshRenderer":
            tree = obj.read_typetree()
            if tree.get("m_Materials") == [{"m_FileID": 0, "m_PathID": 5363102012143072554}]:
                tree["m_Materials"] = [{"m_FileID": 0, "m_PathID": 1952278396157663915}]
                obj.save_typetree(tree)

        # 2. Update projectile_chromia_bullet PrefabList to 9.2.0 aqua projectile & impact PathIDs
        if obj.type.name == "MonoBehaviour" and obj.path_id == 7545326053262791197:
            tree = obj.read_typetree()
            tree["PrefabList"] = [
                {"Prefab": {"m_FileID": 0, "m_PathID": -6431503622299597799}, "Amount": 1},
                {"Prefab": {"m_FileID": 1, "m_PathID": 1710874057756880304}, "Amount": 1},  # fx_p_aqua_projectile
                {"Prefab": {"m_FileID": 1, "m_PathID": 8527048721734798431}, "Amount": 1},  # fx_p_aqua_projectile_impact
            ]
            obj.save_typetree(tree)

    bf = env.file
    bf.version = 7
    bf.version_engine = "2020.3.31f1"
    bf.version_player = "5.x.x"
    for sub in bf.files.values():
        if hasattr(sub, "version"):
            sub.version = "2020.3f1"
        if hasattr(sub, "unity_version"):
            sub.unity_version = "2020.3.31f1"

    return bf.save(packer="lz4")


def patch_deadend_bundle(bundle_bytes: bytes) -> bytes:
    """Fixes Dead End grenade material pointers for Unity 2020."""
    env = UnityPy.load(bundle_bytes)

    for obj in env.objects:
        if obj.type.name == "SkinnedMeshRenderer":
            tree = obj.read_typetree()
            mats = tree.get("m_Materials", [])
            modified = False
            for m in mats:
                if m.get("m_PathID") in [5840752304272669847, -8150449380963715650]:
                    m["m_PathID"] = 8990873932192355227
                    modified = True
            if modified:
                obj.save_typetree(tree)

    bf = env.file
    bf.version = 7
    bf.version_engine = "2020.3.31f1"
    bf.version_player = "5.x.x"
    for sub in bf.files.values():
        if hasattr(sub, "version"):
            sub.version = "2020.3f1"
        if hasattr(sub, "unity_version"):
            sub.unity_version = "2020.3.31f1"

    return bf.save(packer="lz4")


def patch_moves_bundle(bundle_bytes: bytes) -> bytes:
    """Transcodes moves.assetbundle and maps missing particle FX to base particles."""
    env = UnityPy.load(bundle_bytes)

    replacements = {
        "fx_p_chromia_muzzle_flash": "fx_p_aqua_muzzle_flash",
        "fx_p_dinobot_laser_flash": "fx_p_aqua_muzzle_flash",
        "fx_p_chromia_pink_projectile": "fx_p_aqua_projectile",
        "fx_p_Chromia_pink_projectile_impact": "fx_p_aqua_projectile_impact",
        "fx_l_hit_small_Chromia_perceptual_pink": "",
        "projectile_chromia_bullet_new": "projectile_chromia_bullet",
    }

    for obj in env.objects:
        if obj.type.name == "TextAsset":
            tree = obj.read_typetree()
            script = tree.get("m_Script", "")
            modified = False
            for k, v in replacements.items():
                if k in script:
                    script = script.replace(k, v)
                    modified = True
            if modified:
                tree["m_Script"] = script
                obj.save_typetree(tree)

    bf = env.file
    bf.version = 7
    bf.version_engine = "2020.3.31f1"
    bf.version_player = "5.x.x"
    for sub in bf.files.values():
        if hasattr(sub, "version"):
            sub.version = "2020.3f1"
        if hasattr(sub, "unity_version"):
            sub.unity_version = "2020.3.31f1"

    return bf.save(packer="lz4")


def main():
    parser = argparse.ArgumentParser(description="Extract and transcode Netflix character assets.")
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to Netflix edition default.apk or .xapk"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="assets_netflix",
        help="Output directory for extracted and transcoded assets (default: assets_netflix)"
    )

    args = parser.parse_args()
    input_path = Path(args.input)
    out_dir = Path(args.output_dir)

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)

    # Determine if input is XAPK or APK
    apk_zip = None
    if input_path.suffix.lower() == ".xapk":
        print(f"Opening XAPK archive: {input_path}")
        xapk_zip = zipfile.ZipFile(input_path)
        if "default.apk" in xapk_zip.namelist():
            print("Found default.apk inside XAPK, extracting...")
            apk_bytes = xapk_zip.read("default.apk")
            apk_zip = zipfile.ZipFile(io.BytesIO(apk_bytes))
        else:
            apk_zip = xapk_zip
    else:
        apk_zip = zipfile.ZipFile(input_path)

    print("Extracting and transcoding character AssetBundles...")

    # 1. Chromia and Dead End character bundles
    char_bundles = [
        ("assets/assetpack/chromia_gs_kabam_odr/chromia_gs_kabam.assetbundle", "chromia_gs_kabam.assetbundle"),
        ("assets/assetpack/chromia_gs_kabam_odr/chromia_gs_kabam.assetbundle.manifest", "chromia_gs_kabam.assetbundle.manifest"),
        ("assets/assetpack/deadend_gs_deluxe2015_odr/deadend_gs_deluxe2015.assetbundle", "deadend_gs_deluxe2015.assetbundle"),
        ("assets/assetpack/deadend_gs_deluxe2015_odr/deadend_gs_deluxe2015.assetbundle.manifest", "deadend_gs_deluxe2015.assetbundle.manifest"),
    ]

    for zpath, fname in char_bundles:
        if zpath in apk_zip.namelist():
            data = apk_zip.read(zpath)
            dst_file = out_dir / fname
            if fname.endswith(".assetbundle"):
                print(f"  Transcoding {fname} to Unity 2020 format...")
                if fname == "chromia_gs_kabam.assetbundle":
                    data = patch_chromia_bundle(data)
                elif fname == "deadend_gs_deluxe2015.assetbundle":
                    data = patch_deadend_bundle(data)
                else:
                    data = transcode_assetbundle_to_2020(data)
            dst_file.write_bytes(data)
            print(f"  Wrote {dst_file} ({len(data)} bytes)")
        else:
            print(f"  Warning: {zpath} not found in APK")

    # 2. Shared move and procedural animation libraries
    shared_bundles = [
        ("assets/assetpack/characters/moves.assetbundle", "moves.assetbundle", True),
        ("assets/assetpack/characters_procedural_odr/character_anim_procedural.assetbundle", "character_anim_procedural.assetbundle", False),
        ("assets/assetpack/characters_procedural_odr/character_audio_procedural.assetbundle", "character_audio_procedural.assetbundle", False),
        ("assets/assetpack/characters_procedural_odr/character_matinee_procedural.assetbundle", "character_matinee_procedural.assetbundle", False),
    ]

    for zpath, fname, is_moves in shared_bundles:
        if zpath in apk_zip.namelist():
            data = apk_zip.read(zpath)
            dst_file = out_dir / fname
            print(f"  Transcoding shared library {fname} to Unity 2020 format...")
            if is_moves:
                data = patch_moves_bundle(data)
            else:
                data = transcode_assetbundle_to_2020(data)
            dst_file.write_bytes(data)
            print(f"  Wrote {dst_file} ({len(data)} bytes)")

    # 3. 2D Portraits and dialogue sprites
    sprites = [
        ("assets/assetpack/portraits_odr/portraits/portrait_chromia_gs_large.png", "portrait_chromia_gs_large.png"),
        ("assets/assetpack/portraits_odr/portraits/portrait_chromia_gs_small.jpg", "portrait_chromia_gs_small.jpg"),
        ("assets/assetpack/portraits_odr/portraits/portrait_deadend_gs_large.png", "portrait_deadend_gs_large.png"),
        ("assets/assetpack/portraits_odr/portraits/portrait_deadend_gs_small.jpg", "portrait_deadend_gs_small.jpg"),
        ("assets/assetpack/dialogue_odr/dialogue/chromia_gs.png", "chromia_gs.png"),
        ("assets/assetpack/dialogue_odr/dialogue/deadend_gs.png", "deadend_gs.png"),
    ]

    for zpath, fname in sprites:
        if zpath in apk_zip.namelist():
            data = apk_zip.read(zpath)
            dst_file = out_dir / fname
            dst_file.write_bytes(data)
            print(f"  Wrote {dst_file} ({len(data)} bytes)")

    print("\nExtraction and transcoding complete!")
    print(f"Assets prepared in '{out_dir}'. You can now build the offline APK using Server/build_phone_apk.py.")


if __name__ == "__main__":
    main()
