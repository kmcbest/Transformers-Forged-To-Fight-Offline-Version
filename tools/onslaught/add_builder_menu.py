import sys
from pathlib import Path

cs_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Editor\AssetBundleBuilder.cs")
content = cs_path.read_text(encoding="utf-8")

onslaught_method = """
    [MenuItem("Build/Build Onslaught AssetBundle")]
    public static void BuildOnslaughtBundles() {
        Debug.Log("[AssetBundleBuilder] Setting Onslaught AssetBundle names...");
        
        string fbxPath = "Assets/Onslaught/onslaught_prepared.fbx";
        ModelImporter importer = AssetImporter.GetAtPath(fbxPath) as ModelImporter;
        if (importer != null) {
            importer.animationType = ModelImporterAnimationType.Generic;
            importer.useFileScale = false;
            importer.bakeAxisConversion = false;
            importer.globalScale = 1.0f;
            importer.isReadable = true;
            importer.assetBundleName = "onslaught_mesh.assetbundle";
            importer.SaveAndReimport();
        } else {
            AssetImporter rawImp = AssetImporter.GetAtPath(fbxPath);
            if (rawImp != null) {
                rawImp.assetBundleName = "onslaught_mesh.assetbundle";
            }
        }

        string vhFbxPath = "Assets/Onslaught/onslaught_vh_prepared.fbx";
        ModelImporter vhImporter = AssetImporter.GetAtPath(vhFbxPath) as ModelImporter;
        if (vhImporter != null) {
            vhImporter.animationType = ModelImporterAnimationType.Generic;
            vhImporter.useFileScale = false;
            vhImporter.bakeAxisConversion = false;
            vhImporter.globalScale = 1.0f;
            vhImporter.isReadable = true;
            vhImporter.assetBundleName = "onslaught_mesh.assetbundle";
            vhImporter.SaveAndReimport();
        } else {
            AssetImporter rawVhImp = AssetImporter.GetAtPath(vhFbxPath);
            if (rawVhImp != null) {
                rawVhImp.assetBundleName = "onslaught_mesh.assetbundle";
            }
        }
        
        if (Directory.Exists("Assets/Onslaught")) {
            foreach (string file in Directory.GetFiles("Assets/Onslaught", "*.png")) {
                AssetImporter texImp = AssetImporter.GetAtPath(file);
                if (texImp != null) {
                    texImp.assetBundleName = "onslaught_mesh.assetbundle";
                }
            }
        }
        
        string outDir = "AssetBundles";
        if (!Directory.Exists(outDir)) {
            Directory.CreateDirectory(outDir);
        }
        
        Debug.Log("[AssetBundleBuilder] Building Onslaught AssetBundles for Android...");
        BuildPipeline.BuildAssetBundles(
            outDir, 
            BuildAssetBundleOptions.None, 
            BuildTarget.Android
        );
        Debug.Log("[AssetBundleBuilder] Onslaught Build complete! Output to " + outDir);
    }
"""

# Insert before the last closing brace
last_brace = content.rfind("}")
if last_brace != -1:
    new_content = content[:last_brace] + onslaught_method + content[last_brace:]
    cs_path.write_text(new_content, encoding="utf-8")
    print("Successfully added BuildOnslaughtBundles to AssetBundleBuilder.cs!")
else:
    print("Error: Could not find closing brace.")
