using UnityEngine;
using UnityEditor;
using System.IO;

public static class VerifyWindbladeAnimationPlayback {
    public static void Run() {
        string charBundlePath = @"D:\Agent\tftf\extracted_apk\assets\assetpack\characters\characters.assetbundle";
        string windbladeBundlePath = @"D:\Agent\tftf\assets_redeco\windblade_gs.assetbundle";
        string texDir = @"D:\Agent\tftf\build\windblade_textures";
        string buildDir = @"D:\Agent\tftf\build";
        string artifactDir = @"C:\Users\lenovo\.gemini\antigravity\brain\53f7a531-b280-4beb-86e3-7bf7901b1f88";

        AssetBundle.UnloadAllAssetBundles(true);
        AssetBundle charBundle = AssetBundle.LoadFromFile(charBundlePath);
        AssetBundle windbladeBundle = AssetBundle.LoadFromFile(windbladeBundlePath);

        GameObject prefab = null;
        foreach (var n in windbladeBundle.GetAllAssetNames()) {
            if (n.EndsWith("_lw.prefab")) { prefab = windbladeBundle.LoadAsset<GameObject>(n); break; }
        }

        GameObject inst = Object.Instantiate(prefab);
        inst.transform.position = Vector3.zero;
        inst.transform.rotation = Quaternion.identity;

        Animator anim = inst.GetComponent<Animator>();
        anim.applyRootMotion = false;

        Transform hips = FindChild(inst.transform, "Hips");
        Transform lf = FindChild(inst.transform, "LeftFoot");
        Transform rf = FindChild(inst.transform, "RightFoot");
        Transform rh = FindChild(inst.transform, "RightHand");
        Transform lh = FindChild(inst.transform, "LeftHand");

        float minMeshY_overall = float.MaxValue;
        float maxMeshY_overall = float.MinValue;
        bool hasNaN = false;

        // Log initial renderer minY at step 0
        anim.Update(0.05f);
        foreach (var smr in inst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (!smr.enabled) continue;
            Mesh m = new Mesh();
            smr.BakeMesh(m);
            float rMinY = float.MaxValue;
            foreach (var v in m.vertices) {
                Vector3 wp = smr.transform.TransformPoint(v);
                if (wp.y < rMinY) rMinY = wp.y;
            }
            Object.DestroyImmediate(m);
            Debug.Log(string.Format("[RendererMinY] {0}: {1:F4}", smr.name, rMinY));
        }

        // Sample across the 2.5s animation in 0.1s increments (26 steps)
        for (int i = 0; i <= 25; i++) {
            float dt = (i == 0) ? 0.05f : 0.1f;
            anim.Update(dt);

            float minY = GetMinMeshY(inst);
            if (minY < minMeshY_overall) minMeshY_overall = minY;
            if (minY > maxMeshY_overall) maxMeshY_overall = minY;

            if (float.IsNaN(hips.position.y) || float.IsNaN(lf.position.y) || float.IsNaN(rf.position.y) || float.IsNaN(rh.position.y)) {
                hasNaN = true;
                Debug.LogError($"[VerifyWindblade] NaN detected at step {i}!");
                break;
            }

            if (i % 5 == 0) {
                Debug.Log(string.Format("[VerifyWindblade] Step {0} (t~{1:F2}s): HipsY={2:F3}, LF_Y={3:F3}, RF_Y={4:F3}, RH_Pos={5}, minMeshY={6:F4}",
                    i, i * 0.1f, hips.position.y, lf.position.y, rf.position.y, rh.position.ToString("F2"), minY));
            }
        }

        Debug.Log(string.Format("[VerifyWindblade SUMMARY] hasNaN={0}, minMeshY={1:F4}, maxMeshY={2:F4}",
            hasNaN, minMeshY_overall, maxMeshY_overall));

        // Sample at peak pose t=1.25s for rendering
        anim.Update(1.25f);
        anim.enabled = false;

        ApplyTextures(inst, texDir);

        // 1. Full body front
        RenderStudio(inst, Path.Combine(buildDir, "windblade_v2_front.png"), Path.Combine(artifactDir, "windblade_v2_front.png"), -15f);
        // 2. Full body back (matching user's screenshot angle)
        RenderStudio(inst, Path.Combine(buildDir, "windblade_v2_back.png"), Path.Combine(artifactDir, "windblade_v2_back.png"), 160f);
        // 3. Left hand on hip closeup
        RenderHipCloseup(inst, lh, Path.Combine(buildDir, "windblade_v2_waist.png"), Path.Combine(artifactDir, "windblade_v2_waist.png"));
        // 4. Feet grounding closeup
        RenderFeetCloseup(inst, Path.Combine(buildDir, "windblade_v2_feet.png"), Path.Combine(artifactDir, "windblade_v2_feet.png"));
        // 5. Sword grip closeup
        RenderSwordGrip(inst, rh, Path.Combine(buildDir, "windblade_v2_sword.png"), Path.Combine(artifactDir, "windblade_v2_sword.png"));

        Object.DestroyImmediate(inst);
        AssetBundle.UnloadAllAssetBundles(true);
        EditorApplication.Exit(hasNaN ? 1 : 0);
    }

    private static void RenderHipCloseup(GameObject inst, Transform lh, string outBuildPath, string outArtifactPath) {
        GameObject camGo = new GameObject("RenderCamHip");
        Camera cam = camGo.AddComponent<Camera>();
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color(0.08f, 0.09f, 0.12f, 1.0f);
        cam.fieldOfView = 26f;

        Vector3 focus = lh != null ? lh.position : new Vector3(-1.9f, 4.8f, 0.2f);
        float rad = -40f * Mathf.Deg2Rad;
        float dist = 2.8f;
        camGo.transform.position = focus + new Vector3(Mathf.Sin(rad) * dist, 0.1f, Mathf.Cos(rad) * dist);
        camGo.transform.LookAt(focus);

        SetupLights();

        RenderTexture rt = new RenderTexture(1080, 1080, 24);
        cam.targetTexture = rt;
        cam.Render();

        SaveRT(rt, outBuildPath, outArtifactPath);

        cam.targetTexture = null;
        Object.DestroyImmediate(rt);
        Object.DestroyImmediate(camGo);
        CleanupLights();
    }

    private static void RenderFeetCloseup(GameObject inst, string outBuildPath, string outArtifactPath) {
        GameObject camGo = new GameObject("RenderCamFeet");
        Camera cam = camGo.AddComponent<Camera>();
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color(0.08f, 0.09f, 0.12f, 1.0f);
        cam.fieldOfView = 30f;

        Vector3 focus = new Vector3(0f, 0.8f, 0f);
        float rad = -15f * Mathf.Deg2Rad;
        float dist = 6.0f;
        camGo.transform.position = focus + new Vector3(Mathf.Sin(rad) * dist, 0.2f, Mathf.Cos(rad) * dist);
        camGo.transform.LookAt(focus);

        SetupLights();

        RenderTexture rt = new RenderTexture(1080, 1080, 24);
        cam.targetTexture = rt;
        cam.Render();

        SaveRT(rt, outBuildPath, outArtifactPath);

        cam.targetTexture = null;
        Object.DestroyImmediate(rt);
        Object.DestroyImmediate(camGo);
        CleanupLights();
    }

    private static void ApplyTextures(GameObject inst, string texDir) {
        Shader standardShader = Shader.Find("Standard");
        Texture2D mainTex = LoadPNG(Path.Combine(texDir, "cha_windblade_gs_deluxe2014_main_a.png"));
        Texture2D wpnsTex = LoadPNG(Path.Combine(texDir, "cha_windblade_gs_deluxe2014_wpns_a.png"));

        foreach (var r in inst.GetComponentsInChildren<Renderer>(true)) {
            Material[] mats = r.sharedMaterials;
            for (int i = 0; i < mats.Length; i++) {
                Material m = new Material(standardShader);
                string mName = mats[i] != null ? mats[i].name.ToLower() : "";
                string rName = r.name.ToLower();
                if (mName.Contains("wpn") || mName.Contains("weapon") || mName.Contains("sword") || rName.Contains("sword") || rName.Contains("wpn")) {
                    if (wpnsTex != null) m.mainTexture = wpnsTex;
                } else {
                    if (mainTex != null) m.mainTexture = mainTex;
                }
                m.SetFloat("_Glossiness", 0.45f);
                m.SetFloat("_Metallic", 0.35f);
                mats[i] = m;
            }
            r.sharedMaterials = mats;
        }
    }

    private static Texture2D LoadPNG(string path) {
        if (!File.Exists(path)) return null;
        byte[] bytes = File.ReadAllBytes(path);
        Texture2D tex = new Texture2D(2, 2);
        tex.LoadImage(bytes);
        return tex;
    }

    private static void RenderStudio(GameObject inst, string outBuildPath, string outArtifactPath, float camAngleDeg) {
        GameObject camGo = new GameObject("RenderCam");
        Camera cam = camGo.AddComponent<Camera>();
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color(0.08f, 0.09f, 0.12f, 1.0f);
        cam.fieldOfView = 36f;

        float rad = camAngleDeg * Mathf.Deg2Rad;
        float dist = 16.5f;
        Vector3 focus = new Vector3(0f, 4.3f, 0f);
        camGo.transform.position = focus + new Vector3(Mathf.Sin(rad) * dist, 0.5f, Mathf.Cos(rad) * dist);
        camGo.transform.LookAt(focus);

        SetupLights();

        RenderTexture rt = new RenderTexture(1080, 1920, 24);
        cam.targetTexture = rt;
        cam.Render();

        SaveRT(rt, outBuildPath, outArtifactPath);

        cam.targetTexture = null;
        Object.DestroyImmediate(rt);
        Object.DestroyImmediate(camGo);
        CleanupLights();
    }

    private static void RenderBust(GameObject inst, string outBuildPath, string outArtifactPath) {
        GameObject camGo = new GameObject("RenderCamBust");
        Camera cam = camGo.AddComponent<Camera>();
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color(0.08f, 0.09f, 0.12f, 1.0f);
        cam.fieldOfView = 34f;

        float rad = -15f * Mathf.Deg2Rad;
        float dist = 6.8f;
        Vector3 focus = new Vector3(0f, 6.0f, 0.2f);
        camGo.transform.position = focus + new Vector3(Mathf.Sin(rad) * dist, 0.3f, Mathf.Cos(rad) * dist);
        camGo.transform.LookAt(focus);

        SetupLights();

        RenderTexture rt = new RenderTexture(1080, 1080, 24);
        cam.targetTexture = rt;
        cam.Render();

        SaveRT(rt, outBuildPath, outArtifactPath);

        cam.targetTexture = null;
        Object.DestroyImmediate(rt);
        Object.DestroyImmediate(camGo);
        CleanupLights();
    }

    private static void RenderSwordGrip(GameObject inst, Transform rh, string outBuildPath, string outArtifactPath) {
        GameObject camGo = new GameObject("RenderCamSwordGrip");
        Camera cam = camGo.AddComponent<Camera>();
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color(0.08f, 0.09f, 0.12f, 1.0f);
        cam.fieldOfView = 30f;

        Vector3 handPos = rh != null ? rh.position : new Vector3(1.68f, 4.3f, 0f);
        // Focus slightly below hand to capture hilt and fingers
        Vector3 focus = handPos + new Vector3(0f, -0.2f, 0f);
        // Position camera in front and slightly right, looking back at hand
        float dist = 2.4f;
        Vector3 camPos = focus + new Vector3(0.6f, 0.2f, dist);
        camGo.transform.position = camPos;
        camGo.transform.LookAt(focus);

        SetupLights();

        RenderTexture rt = new RenderTexture(1080, 1080, 24);
        cam.targetTexture = rt;
        cam.Render();

        SaveRT(rt, outBuildPath, outArtifactPath);

        cam.targetTexture = null;
        Object.DestroyImmediate(rt);
        Object.DestroyImmediate(camGo);
        CleanupLights();
    }

    private static void SetupLights() {
        GameObject key = new GameObject("KeyLight");
        Light l1 = key.AddComponent<Light>();
        l1.type = LightType.Directional;
        l1.color = new Color(1.0f, 0.96f, 0.90f);
        l1.intensity = 1.35f;
        key.transform.rotation = Quaternion.Euler(22f, -35f, 0f);

        GameObject fill = new GameObject("FillLight");
        Light l2 = fill.AddComponent<Light>();
        l2.type = LightType.Directional;
        l2.color = new Color(0.65f, 0.75f, 0.95f);
        l2.intensity = 0.85f;
        fill.transform.rotation = Quaternion.Euler(15f, 140f, 0f);

        GameObject rim = new GameObject("RimLight");
        Light l3 = rim.AddComponent<Light>();
        l3.type = LightType.Directional;
        l3.color = new Color(0.9f, 0.7f, 1.0f);
        l3.intensity = 1.2f;
        rim.transform.rotation = Quaternion.Euler(-20f, 170f, 0f);
    }

    private static void CleanupLights() {
        GameObject g;
        if ((g = GameObject.Find("KeyLight")) != null) Object.DestroyImmediate(g);
        if ((g = GameObject.Find("FillLight")) != null) Object.DestroyImmediate(g);
        if ((g = GameObject.Find("RimLight")) != null) Object.DestroyImmediate(g);
    }

    private static void SaveRT(RenderTexture rt, string buildPath, string artifactPath) {
        RenderTexture.active = rt;
        Texture2D tex = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false);
        tex.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0);
        tex.Apply();
        RenderTexture.active = null;

        byte[] png = tex.EncodeToPNG();
        File.WriteAllBytes(buildPath, png);
        File.WriteAllBytes(artifactPath, png);
        Object.DestroyImmediate(tex);
        Debug.Log($"[RenderWindblade] Saved: {buildPath}");
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
}
