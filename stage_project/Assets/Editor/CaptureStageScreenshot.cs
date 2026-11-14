using System.IO;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;

public class CaptureStageScreenshot {
    [MenuItem("TFTF/Capture Stage Screenshot")]
    public static void Capture() {
        string scenePath = "Assets/Scenes/RustSea_Devastator_Stage.unity";
        EditorSceneManager.OpenScene(scenePath);

        GameObject dev = GameObject.Find("Devastator_Colossus");
        if (dev != null) {
            // Sample combine animation mid-pose
            AnimationClip combineClip = null;
            UnityEngine.Object[] assets = AssetDatabase.LoadAllAssetsAtPath("Assets/Devastator/Devastator.fbx");
            foreach (var a in assets) {
                if (a is AnimationClip && a.name.IndexOf("combine", System.StringComparison.OrdinalIgnoreCase) >= 0) {
                    combineClip = a as AnimationClip;
                    break;
                }
            }
            if (combineClip != null) {
                // Sample at 3.0s (around frame 90-100 when parts have assembled)
                combineClip.SampleAnimation(dev, 3.2f);
                Debug.Log($"[✓] Sampled animation '{combineClip.name}' at 3.2s!");
            }
        }

        Camera cam = Camera.main;
        if (cam == null) cam = Object.FindObjectOfType<Camera>();
        if (cam == null) {
            Debug.LogError("No camera found in scene!");
            return;
        }

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
        Object.DestroyImmediate(rt);

        byte[] bytes = screenShot.EncodeToPNG();
        string outPath = "E:/Agent/TFTF-blender/stage_devastator_preview.png";
        File.WriteAllBytes(outPath, bytes);
        Debug.Log($"[✓] Captured stage preview screenshot to: {outPath}");
    }
}
