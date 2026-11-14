using System;
using System.IO;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;

public class ExportKarnakBundle {
    [MenuItem("TFTF/Export Karnak Combiners Bundle (Android)")]
    public static void Export() {
        Debug.Log("=== [TFTF] 开始构建卡纳克双巨神 AssetBundle (Android) ===");
        string scenePath = "Assets/Scenes/Karnak_Combiners_Stage.unity";
        EditorSceneManager.OpenScene(scenePath);

        GameObject volc = GameObject.Find("Volcanicus_Colossus");
        GameObject vic = GameObject.Find("Victorion_Colossus");

        if (volc == null || vic == null) {
            Debug.LogError($"[!] 缺少双巨神物体: Volc={volc != null}, Vic={vic != null}");
            return;
        }

        // Clean any existing Karnak_Combiners root
        GameObject oldRoot = GameObject.Find("Karnak_Combiners");
        if (oldRoot != null) UnityEngine.Object.DestroyImmediate(oldRoot);

        // Create container root at (0, 0, 0)
        GameObject root = new GameObject("Karnak_Combiners");
        root.transform.position = Vector3.zero;
        root.transform.rotation = Quaternion.identity;
        root.transform.localScale = Vector3.one;

        volc.transform.SetParent(root.transform, true);
        vic.transform.SetParent(root.transform, true);

        // Set Layer 11 recursively
        SetLayerRecursive(root, 11);

        // Set SMR updateWhenOffscreen = true
        foreach (var smr in root.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            smr.updateWhenOffscreen = true;
        }

        // Save as Prefab
        string prefabDir = "Assets/Combiners";
        if (!Directory.Exists(prefabDir)) Directory.CreateDirectory(prefabDir);
        string prefabPath = "Assets/Combiners/Karnak_Combiners.prefab";
        GameObject prefab = PrefabUtility.SaveAsPrefabAssetAndConnect(root, prefabPath, InteractionMode.AutomatedAction);
        Debug.Log($"[✓] Saved Karnak_Combiners Prefab to: {prefabPath}");

        // Set AssetBundle name
        AssetImporter importer = AssetImporter.GetAtPath(prefabPath);
        importer.assetBundleName = "karnak_combiners.assetbundle";

        // Build AssetBundle for Android
        string outDir = "AssetBundles";
        if (!Directory.Exists(outDir)) Directory.CreateDirectory(outDir);

        BuildPipeline.BuildAssetBundles(outDir, BuildAssetBundleOptions.None, BuildTarget.Android);
        Debug.Log($"[✓] Built karnak_combiners.assetbundle successfully in {outDir}!");

        // Restore scene
        EditorSceneManager.MarkSceneDirty(EditorSceneManager.GetActiveScene());
        EditorSceneManager.SaveScene(EditorSceneManager.GetActiveScene());
        AssetDatabase.SaveAssets();
    }

    private static void SetLayerRecursive(GameObject go, int layer) {
        go.layer = layer;
        foreach (Transform child in go.transform) {
            SetLayerRecursive(child.gameObject, layer);
        }
    }
}
