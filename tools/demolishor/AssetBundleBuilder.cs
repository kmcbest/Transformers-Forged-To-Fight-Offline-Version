using UnityEditor;
using System.IO;
using UnityEngine;

public class AssetBundleBuilder {
    [MenuItem("Build/Build Demolishor AssetBundle")]
    public static void BuildBundles() {
        Debug.Log("[AssetBundleBuilder] Setting AssetBundle names...");
        
        string[] fbxFiles = new string[] {
            "Assets/Demolishor/demolishor_prepared.fbx",
            "Assets/Demolishor/demolishor_vh_prepared.fbx"
        };
        
        foreach (string fbxPath in fbxFiles) {
            ModelImporter importer = AssetImporter.GetAtPath(fbxPath) as ModelImporter;
            if (importer != null) {
                importer.animationType = ModelImporterAnimationType.Generic;
                importer.useFileScale = false;
                importer.bakeAxisConversion = false;
                importer.globalScale = 1.0f;
                importer.assetBundleName = "demolishor_mesh.assetbundle";
                importer.SaveAndReimport();
                
                GameObject go = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
                if (go != null) {
                    SkinnedMeshRenderer smr = go.GetComponentInChildren<SkinnedMeshRenderer>();
                    if (smr != null && smr.sharedMesh != null) {
                        Bounds b = smr.sharedMesh.bounds;
                        Debug.Log(string.Format("[AssetBundleBuilder] {0} bounds: Center=({1:F2}, {2:F2}, {3:F2}), Size=({4:F2}, {5:F2}, {6:F2})",
                            Path.GetFileName(fbxPath), b.center.x, b.center.y, b.center.z, b.size.x, b.size.y, b.size.z));
                    }
                }
            }
        }
        
        // Tag textures
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
        Debug.Log("[AssetBundleBuilder] Build complete! Output located at: " + Path.GetFullPath(outDir));
        EditorUtility.DisplayDialog("Build Complete", "Demolishor AssetBundle built successfully!", "OK");
    }
}
