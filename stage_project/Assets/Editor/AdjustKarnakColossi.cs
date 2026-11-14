using System;
using System.IO;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;

public class AdjustKarnakColossi {
    [MenuItem("TFTF/Adjust Karnak Colossi Scale and Grounding")]
    public static void Adjust() {
        Debug.Log("=== [TFTF] 调整卡纳克双巨神真实 Colossus 比例与地面接地 ===");
        string scenePath = "Assets/Scenes/Karnak_Combiners_Stage.unity";
        var scene = EditorSceneManager.OpenScene(scenePath);

        GameObject p1 = GameObject.Find("Fighter_P1_Autobot (Reference)");
        GameObject p2 = GameObject.Find("Fighter_P2_Decepticon (Reference)");

        if (p1 != null) {
            p1.transform.position = new Vector3(-3.0f, 4.5f, 0.0f);
            p1.transform.localScale = new Vector3(2.2f, 4.5f, 2.2f); // 9.0m height
        }
        if (p2 != null) {
            p2.transform.position = new Vector3(3.0f, 4.5f, 0.0f);
            p2.transform.localScale = new Vector3(2.2f, 4.5f, 2.2f); // 9.0m height
        }

        GameObject volc = GameObject.Find("Volcanicus_Colossus");
        GameObject vic = GameObject.Find("Victorion_Colossus");

        if (volc == null || vic == null) {
            Debug.LogError("Missing Volcanicus or Victorion in scene!");
            return;
        }

        // 1. Scale Volcanicus to ~25.0m
        volc.transform.localScale = new Vector3(480.0f, 480.0f, 480.0f);
        volc.transform.position = new Vector3(-22.0f, 0.0f, 20.0f);
        Vector3 dirVolc = (Vector3.zero - volc.transform.position).normalized;
        dirVolc.y = 0;
        volc.transform.rotation = Quaternion.LookRotation(dirVolc, Vector3.up);

        // 2. Scale Victorion to ~25.0m
        vic.transform.localScale = new Vector3(102.0f, 102.0f, 102.0f);
        // Compute feet bounds to ground flush at Y = 0
        vic.transform.position = new Vector3(22.0f, 0.0f, 20.0f);
        Vector3 dirVic = (Vector3.zero - vic.transform.position).normalized;
        dirVic.y = 0;
        vic.transform.rotation = Quaternion.LookRotation(dirVic, Vector3.up);

        // Calculate bottom vertex/bounds of Victorion
        Bounds vicBounds = new Bounds(vic.transform.position, Vector3.zero);
        bool first = true;
        foreach (var smr in vic.GetComponentsInChildren<SkinnedMeshRenderer>()) {
            if (first) {
                vicBounds = smr.bounds;
                first = false;
            } else {
                vicBounds.Encapsulate(smr.bounds);
            }
        }
        float minY = vicBounds.min.y;
        Debug.Log($"Victorion initial minY={minY}, height={vicBounds.size.y}");
        if (minY < -0.01f || minY > 0.01f) {
            vic.transform.position = new Vector3(22.0f, vic.transform.position.y - minY, 20.0f);
        }

        // Re-check Volcanicus bounds
        Bounds volcBounds = new Bounds(volc.transform.position, Vector3.zero);
        first = true;
        foreach (var smr in volc.GetComponentsInChildren<SkinnedMeshRenderer>()) {
            if (first) {
                volcBounds = smr.bounds;
                first = false;
            } else {
                volcBounds.Encapsulate(smr.bounds);
            }
        }
        float volcMinY = volcBounds.min.y;
        Debug.Log($"Volcanicus initial minY={volcMinY}, height={volcBounds.size.y}");
        if (volcMinY < -0.01f || volcMinY > 0.01f) {
            volc.transform.position = new Vector3(-22.0f, volc.transform.position.y - volcMinY, 20.0f);
        }

        Debug.Log($"[✓] Volcanicus: Pos={volc.transform.position}, Scale={volc.transform.localScale}, Height={volcBounds.size.y:F2}m");
        Debug.Log($"[✓] Victorion: Pos={vic.transform.position}, Scale={vic.transform.localScale}, Height={vicBounds.size.y:F2}m");

        // Save Scene
        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        AssetDatabase.SaveAssets();

        // Render Screenshot from Main Camera
        Camera cam = GameObject.Find("Main Camera (TFTF Combat View)").GetComponent<Camera>();
        int width = 1280;
        int height = 720;
        RenderTexture rt = new RenderTexture(width, height, 24);
        cam.targetTexture = rt;
        Texture2D screenShot = new Texture2D(width, height, TextureFormat.RGB24, false);
        cam.Render();
        RenderTexture.active = rt;
        screenShot.ReadPixels(new Rect(0, 0, width, height), 0, 0);
        screenShot.Apply();
        cam.targetTexture = null;
        RenderTexture.active = null;
        UnityEngine.Object.DestroyImmediate(rt);

        byte[] bytes = screenShot.EncodeToPNG();
        string outPath = "E:/Agent/TFTF-blender/scratch/karnak_colossi_preview_25m.png";
        File.WriteAllBytes(outPath, bytes);
        Debug.Log($"[✓] Rendered combat camera preview to: {outPath}");
    }
}
