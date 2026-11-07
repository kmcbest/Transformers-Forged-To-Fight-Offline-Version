using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class PackOnslaught30FingerBundle {
    public static void Build() {
        Debug.Log("=== [PackOnslaught30FingerBundle] Rebuilding 30-Finger Grafted Mesh & Compiling Android Bundle ===");
        AssetDatabase.ImportAsset("Assets/Onslaught/onslaught_prepared.fbx", ImportAssetOptions.ForceUpdate);
        EditorSceneManager.OpenScene("Assets/Scenes/Onslaught_Inspection.unity", OpenSceneMode.Single);
        OnslaughtHandFixer.RebuildFlexibleFingers();

        Mesh rMesh = AssetDatabase.LoadAssetAtPath<Mesh>("Assets/Onslaught/cha_onslaught_grafted.asset");
        Mesh vMesh = AssetDatabase.LoadAssetAtPath<Mesh>("Assets/Onslaught/cha_onslaught_vehicle_grafted.asset");
        if (rMesh == null || vMesh == null) {
            Debug.LogError("[PackOnslaught30FingerBundle] Missing grafted robot or vehicle mesh!");
            EditorApplication.Exit(1);
            return;
        }

        // Verify non-zero weights on articulated finger bones before packing!
        GameObject onsGo = GameObject.Find("Onslaught_Candidate");
        SkinnedMeshRenderer smr = null;
        foreach (var s in onsGo.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (s.name.Contains("_00") || s.name.Contains("cha_onslaught_gs_00")) { smr = s; break; }
        }
        int fingerWeightedVerts = 0;
        if (smr != null) {
            Transform[] bones = smr.bones;
            BoneWeight[] bws = rMesh.boneWeights;
            for (int i = 0; i < bws.Length; i++) {
                string bn = bones[bws[i].boneIndex0].name.ToLower();
                if (bn.Contains("thumb") || bn.Contains("index") || bn.Contains("middle") || bn.Contains("ring") || bn.Contains("pinky")) {
                    fingerWeightedVerts++;
                }
            }
        }
        Debug.Log($"[PackOnslaught30FingerBundle] Robot verts={rMesh.vertexCount}, FingerWeightedVerts={fingerWeightedVerts}, Vehicle verts={vMesh.vertexCount}");
        if (fingerWeightedVerts < 400) {
            Debug.LogError($"[PackOnslaught30FingerBundle] Expected >= 400 finger-weighted verts, got {fingerWeightedVerts}!");
            EditorApplication.Exit(1);
            return;
        }

        rMesh.name = "cha_onslaught_grafted";
        vMesh.name = "cha_onslaught_vehicle_grafted";
        EditorUtility.SetDirty(rMesh);
        EditorUtility.SetDirty(vMesh);
        AssetDatabase.SaveAssets();

        string outDir = "E:/Agent/TFTF-blender/toolchain/unity_build_project/AssetBundles";
        if (!Directory.Exists(outDir)) Directory.CreateDirectory(outDir);

        AssetBundleBuild[] builds = new AssetBundleBuild[1];
        builds[0].assetBundleName = "onslaught_mesh.assetbundle";
        builds[0].assetNames = new string[] {
            "Assets/Onslaught/cha_onslaught_grafted.asset",
            "Assets/Onslaught/cha_onslaught_vehicle_grafted.asset"
        };

        var manifest = BuildPipeline.BuildAssetBundles(
            outDir,
            builds,
            BuildAssetBundleOptions.ForceRebuildAssetBundle | BuildAssetBundleOptions.ChunkBasedCompression,
            BuildTarget.Android
        );
        if (manifest == null) {
            Debug.LogError("[PackOnslaught30FingerBundle] BuildAssetBundles returned null!");
            EditorApplication.Exit(1);
            return;
        }
        Debug.Log("[PackOnslaught30FingerBundle] Successfully built 30-finger onslaught_mesh.assetbundle!");
        EditorApplication.Exit(0);
    }
}
