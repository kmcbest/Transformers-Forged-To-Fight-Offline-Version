using UnityEngine;
using UnityEditor;
using System.IO;
using System.Collections.Generic;

public static class VerifyChromiaRealGameAnimator {
    public static void Run() {
        string charBundlePath = @"D:\Agent\tftf\extracted_apk\assets\assetpack\characters\characters.assetbundle";
        string chromiaBundlePath = @"D:\Agent\tftf\assets_redeco\chromia_gs_kabam.assetbundle";
        string texDir = @"D:\Agent\tftf\build\chromia_textures";
        string buildDir = @"D:\Agent\tftf\build";
        string artifactDir = @"C:\Users\lenovo\.gemini\antigravity\brain\53f7a531-b280-4beb-86e3-7bf7901b1f88";

        AssetBundle.UnloadAllAssetBundles(true);
        AssetBundle charBundle = AssetBundle.LoadFromFile(charBundlePath);
        AssetBundle chromiaBundle = AssetBundle.LoadFromFile(chromiaBundlePath);

        GameObject prefab = null;
        foreach (var n in chromiaBundle.GetAllAssetNames()) {
            if (n.EndsWith("_lw.prefab")) { prefab = chromiaBundle.LoadAsset<GameObject>(n); break; }
        }

        GameObject inst = Object.Instantiate(prefab);
        inst.name = "ChromiaRealGameModel";
        inst.transform.position = Vector3.zero;
        inst.transform.rotation = Quaternion.identity;

        Animator anim = inst.GetComponent<Animator>();
        anim.applyRootMotion = false;

        // Sample frame 0.05s under animator_char_lw (FE_Idle with iKOnFeet = True!)
        anim.Update(0.05f);
        float minY0 = GetMinMeshY(inst);
        Transform hips = FindChild(inst.transform, "Hips");
        Transform lf = FindChild(inst.transform, "LeftFoot");
        Transform rf = FindChild(inst.transform, "RightFoot");
        Transform lt = FindChild(inst.transform, "LeftToeBase");
        Transform rt = FindChild(inst.transform, "RightToeBase");
        Transform lh = FindChild(inst.transform, "LeftHand");
        Transform rh = FindChild(inst.transform, "RightHand");
        Transform chest = FindChild(inst.transform, "Spine1");

        Debug.Log(string.Format("[Chromia RealGame FE_Idle t=0.05] HipsY={0:F4}, LeftFootY={1:F4}, RightFootY={2:F4}, LeftToeY={3:F4}, RightToeY={4:F4}, minMeshY={5:F4}",
            hips.position.y, lf.position.y, rf.position.y, lt.position.y, rt.position.y, minY0));

        // Evaluate 20 frames across 2.5s breathing cycle
        Vector3 lh0 = lh.position, rh0 = rh.position, lf0 = lf.position;
        Vector3 prevLH = lh0, prevRH = rh0;
        float maxLHDisp = 0f, maxRHDisp = 0f, maxLHStep = 0f, maxRHStep = 0f, maxLFDisp = 0f;
        float minChestX = 999f, maxChestX = -999f;

        for (int s = 0; s < 20; s++) {
            anim.Update(0.125f);
            float dLH = Vector3.Distance(lh.position, lh0);
            float dRH = Vector3.Distance(rh.position, rh0);
            float stepLH = Vector3.Distance(lh.position, prevLH);
            float stepRH = Vector3.Distance(rh.position, prevRH);
            float dLF = Vector3.Distance(lf.position, lf0);
            if (dLH > maxLHDisp) maxLHDisp = dLH;
            if (dRH > maxRHDisp) maxRHDisp = dRH;
            if (stepLH > maxLHStep) maxLHStep = stepLH;
            if (stepRH > maxRHStep) maxRHStep = stepRH;
            if (dLF > maxLFDisp) maxLFDisp = dLF;
            float cx = chest.localEulerAngles.x;
            if (cx > 180f) cx -= 360f;
            if (cx < minChestX) minChestX = cx;
            if (cx > maxChestX) maxChestX = cx;
            prevLH = lh.position; prevRH = rh.position;
        }

        Debug.Log(string.Format("[Chromia MotionCheck 2.5s] maxLHDisp={0:F4} (step={1:F4}), maxRHDisp={2:F4} (step={3:F4}), maxLFDisp={4:F4}, chestPitchRange={5:F3}deg",
            maxLHDisp, maxLHStep, maxRHDisp, maxRHStep, maxLFDisp, maxChestX - minChestX));

        // Freeze and apply textures for studio multi-angle renders
        anim.Rebind();
        anim.Update(0.05f);
        anim.enabled = false;
        ApplyTextures(inst, texDir);

        // Render 4 key angles
        RenderStudio(inst, Path.Combine(buildDir, "chromia_realgame_180_frontleft.png"), Path.Combine(artifactDir, "chromia_realgame_180_frontleft.png"), 180f);
        RenderStudio(inst, Path.Combine(buildDir, "chromia_realgame_130_front.png"), Path.Combine(artifactDir, "chromia_realgame_130_front.png"), 130f);
        RenderStudio(inst, Path.Combine(buildDir, "chromia_realgame_060_frontright.png"), Path.Combine(artifactDir, "chromia_realgame_060_frontright.png"), 60f);
        RenderStudio(inst, Path.Combine(buildDir, "chromia_realgame_090_side.png"), Path.Combine(artifactDir, "chromia_realgame_090_side.png"), 90f);

        // Render chest and crossed-arms close-up
        RenderChestCloseup(inst, Path.Combine(buildDir, "chromia_realgame_chest_closeup.png"), Path.Combine(artifactDir, "chromia_realgame_chest_closeup.png"));

        // Render keyframe snapshot at t=1.25s (peak breath)
        anim.enabled = true;
        anim.Update(1.20f);
        anim.enabled = false;
        RenderStudio(inst, Path.Combine(buildDir, "chromia_realgame_t125_peak_breath.png"), Path.Combine(artifactDir, "chromia_realgame_t125_peak_breath.png"), 130f);

        Object.DestroyImmediate(inst);
        AssetBundle.UnloadAllAssetBundles(true);
        EditorApplication.Exit(0);
    }

    private static float GetMinMeshY(GameObject inst) {
        float minY = float.MaxValue;
        foreach (var smr in inst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (!smr.enabled) continue;
            Mesh m = new Mesh();
            smr.BakeMesh(m);
            foreach (var v in m.vertices) {
                Vector3 wp = smr.transform.TransformPoint(v);
                if (wp.y < minY) minY = wp.y;
            }
            Object.DestroyImmediate(m);
        }
        return minY;
    }

    private static Transform FindChild(Transform root, string name) {
        if (root.name == name) return root;
        foreach (Transform c in root) {
            Transform r = FindChild(c, name);
            if (r != null) return r;
        }
        return null;
    }

    private static void ApplyTextures(GameObject instance, string texDir) {
        Texture2D mainTex = null, mainNM = null, tformTex = null, tformNM = null;
        if (Directory.Exists(texDir)) {
            foreach (var f in Directory.GetFiles(texDir, "*.png")) {
                string fn = Path.GetFileNameWithoutExtension(f).ToLower();
                byte[] bytes = File.ReadAllBytes(f);
                Texture2D t = new Texture2D(2, 2, TextureFormat.RGBA32, true);
                t.LoadImage(bytes);
                if (fn.Contains("main_a")) mainTex = t; else if (fn.Contains("main_nm")) mainNM = t;
                else if (fn.Contains("tform_misc_a")) tformTex = t; else if (fn.Contains("tform_misc_nm")) tformNM = t;
            }
        }
        Shader stdShader = Shader.Find("Standard") ?? Shader.Find("Diffuse");
        foreach (var r in instance.GetComponentsInChildren<Renderer>(true)) {
            if (!r.enabled) continue;
            Material[] mats = new Material[r.sharedMaterials.Length];
            for (int i = 0; i < mats.Length; i++) {
                Material m = new Material(stdShader);
                Texture2D diff = (i == 1 && tformTex != null) ? tformTex : mainTex;
                Texture2D bump = (i == 1 && tformNM != null) ? tformNM : mainNM;
                if (diff != null) { m.mainTexture = diff; m.color = Color.white; }
                if (bump != null) { m.EnableKeyword("_NORMALMAP"); m.SetTexture("_BumpMap", bump); }
                m.SetFloat("_Glossiness", 0.50f);
                m.SetFloat("_Metallic", 0.40f);
                mats[i] = m;
            }
            r.sharedMaterials = mats;
        }
    }

    private static void RenderStudio(GameObject instance, string outBuild, string outArtifact, float angleY) {
        foreach (var c in Object.FindObjectsOfType<Camera>()) Object.DestroyImmediate(c.gameObject);
        foreach (var l in Object.FindObjectsOfType<Light>()) Object.DestroyImmediate(l.gameObject);

        instance.transform.rotation = Quaternion.Euler(0f, angleY, 0f);

        Bounds b = new Bounds(instance.transform.position, Vector3.zero);
        bool hasB = false;
        foreach (var r in instance.GetComponentsInChildren<Renderer>(true)) {
            if (r.enabled && r.gameObject.activeInHierarchy) {
                if (!hasB) { b = r.bounds; hasB = true; } else b.Encapsulate(r.bounds);
            }
        }

        GameObject camObj = new GameObject("Cam");
        Camera cam = camObj.AddComponent<Camera>();
        cam.clearFlags = CameraClearFlags.Color;
        cam.backgroundColor = new Color(0.12f, 0.13f, 0.15f, 1f);
        cam.fieldOfView = 28f;

        Vector3 center = b.center;
        float radius = Mathf.Max(b.extents.x, b.extents.y, b.extents.z);
        float dist = (radius / Mathf.Sin(cam.fieldOfView * 0.5f * Mathf.Deg2Rad)) * 1.15f;
        camObj.transform.position = center + new Vector3(0f, 0f, -dist);
        camObj.transform.LookAt(center);

        GameObject light1 = new GameObject("KeyLight"); Light l1 = light1.AddComponent<Light>(); l1.type = LightType.Directional; l1.color = new Color(1.0f, 0.98f, 0.95f); l1.intensity = 1.35f; light1.transform.rotation = Quaternion.Euler(24f, -28f, 0f);
        GameObject light2 = new GameObject("FillLight"); Light l2 = light2.AddComponent<Light>(); l2.type = LightType.Directional; l2.color = new Color(0.90f, 0.93f, 1.0f); l2.intensity = 0.65f; light2.transform.rotation = Quaternion.Euler(15f, 45f, 0f);
        GameObject light3 = new GameObject("RimLight"); Light l3 = light3.AddComponent<Light>(); l3.type = LightType.Directional; l3.color = new Color(0.85f, 0.95f, 1.0f); l3.intensity = 0.50f; light3.transform.rotation = Quaternion.Euler(-20f, 160f, 0f);

        int width = 1024, height = 1440;
        RenderTexture rt = new RenderTexture(width, height, 24, RenderTextureFormat.ARGB32);
        rt.antiAliasing = 4;
        cam.targetTexture = rt;
        cam.Render();
        RenderTexture.active = rt;
        Texture2D screenShot = new Texture2D(width, height, TextureFormat.RGB24, false);
        screenShot.ReadPixels(new Rect(0, 0, width, height), 0, 0);
        screenShot.Apply();
        cam.targetTexture = null;
        RenderTexture.active = null;
        Object.DestroyImmediate(rt);

        byte[] png = screenShot.EncodeToPNG();
        File.WriteAllBytes(outBuild, png);
        File.WriteAllBytes(outArtifact, png);
        Object.DestroyImmediate(screenShot);
        Object.DestroyImmediate(camObj);
        Object.DestroyImmediate(light1);
        Object.DestroyImmediate(light2);
        Object.DestroyImmediate(light3);
    }

    private static void RenderChestCloseup(GameObject instance, string outBuild, string outArtifact) {
        foreach (var c in Object.FindObjectsOfType<Camera>()) Object.DestroyImmediate(c.gameObject);
        foreach (var l in Object.FindObjectsOfType<Light>()) Object.DestroyImmediate(l.gameObject);

        instance.transform.rotation = Quaternion.Euler(0f, 155f, 0f); // 3/4 front view
        Transform chest = FindChild(instance.transform, "Spine1");
        Vector3 center = chest.position + new Vector3(0f, 0.35f, 0f);

        GameObject camObj = new GameObject("CamChest");
        Camera cam = camObj.AddComponent<Camera>();
        cam.clearFlags = CameraClearFlags.Color;
        cam.backgroundColor = new Color(0.12f, 0.13f, 0.15f, 1f);
        cam.fieldOfView = 22f;
        camObj.transform.position = center + new Vector3(0f, 0.15f, -3.8f);
        camObj.transform.LookAt(center);

        GameObject light1 = new GameObject("KeyLight"); Light l1 = light1.AddComponent<Light>(); l1.type = LightType.Directional; l1.color = new Color(1.0f, 0.98f, 0.95f); l1.intensity = 1.40f; light1.transform.rotation = Quaternion.Euler(24f, -28f, 0f);
        GameObject light2 = new GameObject("FillLight"); Light l2 = light2.AddComponent<Light>(); l2.type = LightType.Directional; l2.color = new Color(0.90f, 0.93f, 1.0f); l2.intensity = 0.70f; light2.transform.rotation = Quaternion.Euler(15f, 45f, 0f);
        GameObject light3 = new GameObject("RimLight"); Light l3 = light3.AddComponent<Light>(); l3.type = LightType.Directional; l3.color = new Color(0.85f, 0.95f, 1.0f); l3.intensity = 0.50f; light3.transform.rotation = Quaternion.Euler(-20f, 160f, 0f);

        int width = 1024, height = 1024;
        RenderTexture rt = new RenderTexture(width, height, 24, RenderTextureFormat.ARGB32);
        rt.antiAliasing = 4;
        cam.targetTexture = rt;
        cam.Render();
        RenderTexture.active = rt;
        Texture2D screenShot = new Texture2D(width, height, TextureFormat.RGB24, false);
        screenShot.ReadPixels(new Rect(0, 0, width, height), 0, 0);
        screenShot.Apply();
        cam.targetTexture = null;
        RenderTexture.active = null;
        Object.DestroyImmediate(rt);

        byte[] png = screenShot.EncodeToPNG();
        File.WriteAllBytes(outBuild, png);
        File.WriteAllBytes(outArtifact, png);
        Object.DestroyImmediate(screenShot);
        Object.DestroyImmediate(camObj);
        Object.DestroyImmediate(light1);
        Object.DestroyImmediate(light2);
        Object.DestroyImmediate(light3);
    }
}
