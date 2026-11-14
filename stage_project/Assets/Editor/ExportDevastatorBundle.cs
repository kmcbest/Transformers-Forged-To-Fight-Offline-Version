using System.IO;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;

[InitializeOnLoad]
public class ExportDevastatorBundle {
    static ExportDevastatorBundle() {
        EditorApplication.delayCall += () => {
            string outBundle = "AssetBundles/devastator_stage.assetbundle";
            if (!File.Exists(outBundle)) {
                Export();
            }
        };
    }

    [MenuItem("TFTF/Export Devastator Bundle")]
    public static void Export() {
        Debug.Log("=== Exporting Devastator AssetBundle for Android ===");
        string scenePath = "Assets/Scenes/RustSea_Devastator_Stage.unity";
        EditorSceneManager.OpenScene(scenePath);

        GameObject dev = GameObject.Find("Devastator_Colossus");
        if (dev == null) {
            Debug.LogError("Devastator_Colossus not found in scene!");
            return;
        }

        // Save as Prefab
        string prefabPath = "Assets/Devastator/Devastator_Colossus.prefab";
        GameObject prefab = PrefabUtility.SaveAsPrefabAssetAndConnect(dev, prefabPath, InteractionMode.AutomatedAction);
        Debug.Log($"[✓] Saved Devastator Prefab to: {prefabPath}");

        // Set AssetBundle name
        AssetImporter importer = AssetImporter.GetAtPath(prefabPath);
        importer.assetBundleName = "devastator_stage.assetbundle";

        // Build AssetBundle for Android
        string outDir = "AssetBundles";
        if (!Directory.Exists(outDir)) Directory.CreateDirectory(outDir);

        BuildPipeline.BuildAssetBundles(outDir, BuildAssetBundleOptions.None, BuildTarget.Android);
        Debug.Log($"[✓] Built devastator_stage.assetbundle successfully in {outDir}!");
    }
}
