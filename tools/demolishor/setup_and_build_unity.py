# -*- coding: utf-8 -*-
import sys
import os
import shutil
from pathlib import Path
import subprocess

sys.stdout.reconfigure(encoding='utf-8')

PROJECT_DIR = Path(r"d:\Agent\tftf\toolchain\unity_build_project")
UNITY_EXE = Path(r"d:\Agent\tftf\toolchain\Unity_2020.3.31f1\Editor\Unity.exe")

print("=== Setting up Unity Build Project ===")

# Create directories
assets_dir = PROJECT_DIR / "Assets"
editor_dir = assets_dir / "Editor"
demolishor_assets = assets_dir / "Demolishor"
output_bundles_dir = PROJECT_DIR / "AssetBundles"
project_settings_dir = PROJECT_DIR / "ProjectSettings"

editor_dir.mkdir(parents=True, exist_ok=True)
demolishor_assets.mkdir(parents=True, exist_ok=True)
output_bundles_dir.mkdir(parents=True, exist_ok=True)
project_settings_dir.mkdir(parents=True, exist_ok=True)

# 1. ProjectVersion.txt
version_file = project_settings_dir / "ProjectVersion.txt"
version_file.write_text("m_EditorVersion: 2020.3.31f1\n", encoding="utf-8")

# 2. Copy FBX and Textures
src_fbx = Path(r"d:\Agent\tftf\tools\demolishor\demolishor_prepared.fbx")
shutil.copy2(src_fbx, demolishor_assets / "demolishor_prepared.fbx")

tex_dir = Path(r"d:\Agent\tftf\tools\demolishor\textures_processed")
for img in tex_dir.glob("*.png"):
    shutil.copy2(img, demolishor_assets / img.name)

print("[✓] Copied FBX and textures to Unity project Assets/Demolishor")

# 3. Create AssetBundleBuilder.cs
cs_content = """using UnityEditor;
using System.IO;
using UnityEngine;

public class AssetBundleBuilder {
    public static void BuildBundles() {
        Debug.Log("[AssetBundleBuilder] Setting AssetBundle names...");
        
        string fbxPath = "Assets/Demolishor/demolishor_prepared.fbx";
        AssetImporter importer = AssetImporter.GetAtPath(fbxPath);
        if (importer != null) {
            importer.assetBundleName = "demolishor_mesh.assetbundle";
        }
        
        // Also tag textures
        foreach (string file in Directory.GetFiles("Assets/Demolishor", "*.png")) {
            AssetImporter texImp = AssetImporter.GetAtPath(file);
            if (texImp != null) {
                texImp.assetBundleName = "demolishor_mesh.assetbundle";
            }
        }
        
        string outDir = "AssetBundles";
        if (!Directory.Exists(outDir)) {
            Directory.CreateDirectory(outDir);
        }
        
        Debug.Log("[AssetBundleBuilder] Building AssetBundles for Android...");
        BuildPipeline.BuildAssetBundles(
            outDir, 
            BuildAssetBundleOptions.None, 
            BuildTarget.Android
        );
        Debug.Log("[AssetBundleBuilder] Build complete!");
    }
}
"""
(editor_dir / "AssetBundleBuilder.cs").write_text(cs_content, encoding="utf-8")
print("[✓] Created Editor/AssetBundleBuilder.cs")

# 4. Run Unity Editor in batchmode
log_file = PROJECT_DIR / "unity_build.log"
print(f"[*] Running Unity Editor headless build (logging to {log_file.name})...")

cmd = [
    str(UNITY_EXE),
    "-batchmode",
    "-quit",
    "-projectPath", str(PROJECT_DIR),
    "-executeMethod", "AssetBundleBuilder.BuildBundles",
    "-logFile", str(log_file)
]

res = subprocess.run(cmd)
print(f"[+] Unity process finished with return code: {res.returncode}")

bundle_out = output_bundles_dir / "demolishor_mesh.assetbundle"
if bundle_out.exists():
    print(f"\n[✓] SUCCESS: AssetBundle built: {bundle_out} ({bundle_out.stat().st_size / 1024:.1f} KB)")
else:
    print(f"\n[!] AssetBundle not found at {bundle_out}. Checking log...")
    if log_file.exists():
        lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in lines[-30:]:
            print("  ", line)
