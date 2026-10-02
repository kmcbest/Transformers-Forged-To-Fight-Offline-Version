import sys
import shutil
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
SRC_TEX_DIR = ROOT / "tools" / "elita_one" / "processed_textures"
DST_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "ElitaOne"
EDITOR_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Editor"

DST_DIR.mkdir(parents=True, exist_ok=True)
EDITOR_DIR.mkdir(parents=True, exist_ok=True)

# Texture mapping:
tex_mapping = {
    "elita_main_diffuse.png": "cha_elita_one_main_a.png",
    "elita_main_normal.png":  "cha_elita_one_main_NM.png",
    "elita_main_raoe.png":    "cha_elita_one_main_tform_misc_RAOE.png",
    "elita_vh_diffuse.png":   "cha_elita_one_vh_a.png",
    "elita_vh_normal.png":    "cha_elita_one_vh_NM.png",
    "elita_vh_raoe.png":      "cha_elita_one_vh_tform_misc_RAOE.png",
}

for src_name, dst_name in tex_mapping.items():
    src_file = SRC_TEX_DIR / src_name
    dst_file = DST_DIR / dst_name
    shutil.copy2(src_file, dst_file)
    print(f"[✓] Copied {src_name} -> Assets/ElitaOne/{dst_name}")

# Update AssetBundleBuilder.cs
cs_content = """using UnityEditor;
using System.IO;
using UnityEngine;

public class AssetBundleBuilder {
    [MenuItem("Build/Build Demolishor AssetBundle")]
    public static void BuildBundles() {
        Debug.Log("[AssetBundleBuilder] Setting Demolishor AssetBundle names...");
        
        string fbxPath = "Assets/Demolishor/demolishor_prepared.fbx";
        AssetImporter importer = AssetImporter.GetAtPath(fbxPath);
        if (importer != null) {
            importer.assetBundleName = "demolishor_mesh.assetbundle";
        }
        
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
        
        Debug.Log("[AssetBundleBuilder] Building Demolishor AssetBundles for Android...");
        BuildPipeline.BuildAssetBundles(
            outDir, 
            BuildAssetBundleOptions.None, 
            BuildTarget.Android
        );
        Debug.Log("[AssetBundleBuilder] Demolishor Build complete!");
    }

    [MenuItem("Build/Build Elita One AssetBundle")]
    public static void BuildElitaOneBundles() {
        Debug.Log("[AssetBundleBuilder] Setting Elita One AssetBundle names...");
        
        string fbxPath = "Assets/ElitaOne/elita_one_prepared.fbx";
        ModelImporter importer = AssetImporter.GetAtPath(fbxPath) as ModelImporter;
        if (importer != null) {
            importer.animationType = ModelImporterAnimationType.Generic;
            importer.useFileScale = false;
            importer.bakeAxisConversion = false;
            importer.globalScale = 1.0f;
            importer.assetBundleName = "elita_one_mesh.assetbundle";
            importer.SaveAndReimport();
        } else {
            AssetImporter rawImp = AssetImporter.GetAtPath(fbxPath);
            if (rawImp != null) {
                rawImp.assetBundleName = "elita_one_mesh.assetbundle";
            }
        }
        
        if (Directory.Exists("Assets/ElitaOne")) {
            foreach (string file in Directory.GetFiles("Assets/ElitaOne", "*.png")) {
                AssetImporter texImp = AssetImporter.GetAtPath(file);
                if (texImp != null) {
                    texImp.assetBundleName = "elita_one_mesh.assetbundle";
                }
            }
        }
        
        string outDir = "AssetBundles";
        if (!Directory.Exists(outDir)) {
            Directory.CreateDirectory(outDir);
        }
        
        Debug.Log("[AssetBundleBuilder] Building Elita One AssetBundles for Android...");
        BuildPipeline.BuildAssetBundles(
            outDir, 
            BuildAssetBundleOptions.None, 
            BuildTarget.Android
        );
        Debug.Log("[AssetBundleBuilder] Elita One Build complete!");
    }
}
"""

cs_path = EDITOR_DIR / "AssetBundleBuilder.cs"
cs_path.write_text(cs_content, encoding="utf-8")
print(f"[✓] Written updated {cs_path}")
