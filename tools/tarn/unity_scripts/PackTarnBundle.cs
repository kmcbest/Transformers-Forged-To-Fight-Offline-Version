using System.IO;
using UnityEditor;
using UnityEngine;

public static class PackTarnBundle {
    [MenuItem("TFTF/Pack Tarn Mesh AssetBundle")]
    public static void Build() {
        Debug.Log("=== [PackTarnBundle] Compiling Android AssetBundle (cha_tarn_gs_00 & cha_tarn_gs_01) ===");
        Mesh rMesh = AssetDatabase.LoadAssetAtPath<Mesh>("Assets/Tarn/cha_tarn_gs_00.asset");
        Mesh vMesh = AssetDatabase.LoadAssetAtPath<Mesh>("Assets/Tarn/cha_tarn_gs_01.asset");
        if (rMesh == null || vMesh == null) {
            Debug.LogError("[PackTarnBundle] Missing cha_tarn_gs_00.asset or cha_tarn_gs_01.asset!");
            EditorApplication.Exit(1);
            return;
        }
        if (rMesh.vertexCount > 65535 || vMesh.vertexCount > 65535) {
            Debug.LogError($"[PackTarnBundle] 16-bit vertex overflow: robot={rMesh.vertexCount}, veh={vMesh.vertexCount}");
            EditorApplication.Exit(1);
            return;
        }

        string outDir = "E:/Agent/TFTF-blender/toolchain/unity_build_project/AssetBundles";
        if (!Directory.Exists(outDir)) Directory.CreateDirectory(outDir);

        AssetBundleBuild[] builds = new AssetBundleBuild[1];
        builds[0].assetBundleName = "tarn_mesh.assetbundle";
        builds[0].assetNames = new string[] {
            "Assets/Tarn/cha_tarn_gs_00.asset",
            "Assets/Tarn/cha_tarn_gs_01.asset"
        };

        var manifest = BuildPipeline.BuildAssetBundles(
            outDir,
            builds,
            BuildAssetBundleOptions.ForceRebuildAssetBundle | BuildAssetBundleOptions.ChunkBasedCompression,
            BuildTarget.Android
        );
        if (manifest == null) {
            Debug.LogError("[PackTarnBundle] BuildAssetBundles returned null!");
            EditorApplication.Exit(1);
            return;
        }
        Debug.Log($"[PackTarnBundle] Built tarn_mesh.assetbundle cleanly! robotVerts={rMesh.vertexCount}, vehVerts={vMesh.vertexCount}");
        EditorApplication.Exit(0);
    }
}
