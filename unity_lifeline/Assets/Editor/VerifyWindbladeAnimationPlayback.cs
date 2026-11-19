using UnityEngine;
using UnityEditor;
using System.IO;

public static class VerifyWindbladeAnimationPlayback {
    public static void Run() {
        string repoRoot = Path.GetFullPath(Path.Combine(Application.dataPath, "..", ".."));
        string charBundlePath = Path.Combine(repoRoot, "extracted_apk", "assets", "assetpack", "characters", "characters.assetbundle");
        string procBundlePath = Path.Combine(repoRoot, "extracted_apk", "assets", "assetpack", "characters_procedural_odr", "character_anim_procedural.assetbundle");
        string windbladeBundlePath = Path.Combine(repoRoot, "assets_redeco", "windblade_gs.assetbundle");
        string texDir = Path.Combine(repoRoot, "build", "windblade_textures");
        string buildDir = Path.Combine(repoRoot, "build");

        AssetBundle.UnloadAllAssetBundles(true);
        AssetBundle.LoadFromFile(procBundlePath);
        AssetBundle.LoadFromFile(charBundlePath);
        AssetBundle windbladeBundle = AssetBundle.LoadFromFile(windbladeBundlePath);

        GameObject prefab = null;
        foreach (var n in windbladeBundle.GetAllAssetNames()) {
            if (n.EndsWith("_lw.prefab")) { prefab = windbladeBundle.LoadAsset<GameObject>(n); break; }
        }

        GameObject inst = Object.Instantiate(prefab);
        inst.transform.position = Vector3.zero;
        inst.transform.rotation = Quaternion.identity;
        Transform tr = inst.transform.Find("transformed");
        if (tr != null) tr.gameObject.SetActive(false);

        Animator anim = inst.GetComponent<Animator>();
        anim.applyRootMotion = false;

        Transform hips = FindChild(inst.transform, "Hips");
        Transform lf = FindChild(inst.transform, "LeftFoot");
        Transform rf = FindChild(inst.transform, "RightFoot");
        Transform rh = FindChild(inst.transform, "RightHand");
        Transform lh = FindChild(inst.transform, "LeftHand");
        Transform lm3 = FindChild(inst.transform, "LeftHandMiddle3");

        float minMeshY_overall = float.MaxValue;
        float maxMeshY_overall = float.MinValue;
        bool hasNaN = false;

        anim.Update(0.05f);
        foreach (var ci in anim.GetCurrentAnimatorClipInfo(0)) {
            Debug.Log($"[VerifyWindblade] StateMachine playing clip: {ci.clip.name} (len={ci.clip.length:F3}s, weight={ci.weight:F2})");
        }

        for (int i = 0; i <= 25; i++) {
            float dt = (i == 0) ? 0.0f : 0.1f;
            if (dt > 0f) anim.Update(dt);

            float minY = GetMinMeshY(inst);
            if (minY < minMeshY_overall) minMeshY_overall = minY;
            if (minY > maxMeshY_overall) maxMeshY_overall = minY;

            if (float.IsNaN(hips.position.y) || float.IsNaN(lf.position.y) || float.IsNaN(rf.position.y) || float.IsNaN(rh.position.y)) {
                hasNaN = true;
                Debug.LogError($"[VerifyWindblade] NaN detected at step {i}!");
                break;
            }

            if (i % 5 == 0) {
                Debug.Log(string.Format("[VerifyWindblade] Step {0}: HipsY={1:F3}, LF_Y={2:F3}, RF_Y={3:F3}, RH_Pos={4}, minMeshY={5:F4}",
                    i, hips.position.y, lf.position.y, rf.position.y, rh.position.ToString("F2"), minY));
            }
        }

        Debug.Log(string.Format("[VerifyWindblade SUMMARY] hasNaN={0}, minMeshY={1:F4}, maxMeshY={2:F4}",
            hasNaN, minMeshY_overall, maxMeshY_overall));

        anim.Rebind();
        anim.Update(0.05f);
        anim.Update(1.20f);
        anim.enabled = false;

        ApplyTextures(inst, texDir);

        RenderStudio(inst, Path.Combine(buildDir, "windblade_v2_front.png"), 180f, 1024, 1440, 28f);
        RenderStudio(inst, Path.Combine(buildDir, "windblade_v2_frontleft.png"), 140f, 1024, 1440, 28f);
        RenderStudio(inst, Path.Combine(buildDir, "windblade_v2_frontright.png"), -140f, 1024, 1440, 28f);
        Vector3 lhCenter = (lh.position + lm3.position) * 0.5f;
        RenderCam(lhCenter + new Vector3(0.0f, 0.2f, 3.2f), lhCenter, Path.Combine(buildDir, "windblade_v2_waist.png"));
        RenderCam(new Vector3(0f, 0.8f, 5.2f), new Vector3(0f, 0.7f, 0f), Path.Combine(buildDir, "windblade_v2_feet.png"));
        RenderCam(rh.position + new Vector3(1.5f, 0.1f, 2.5f), rh.position + new Vector3(0.0f, -0.3f, 0.2f), Path.Combine(buildDir, "windblade_v2_sword.png"));

        Object.DestroyImmediate(inst);
        AssetBundle.UnloadAllAssetBundles(true);
        EditorApplication.Exit(hasNaN ? 1 : 0);
    }

    private static void ApplyTextures(GameObject inst, string texDir) {
        Shader standardShader = Shader.Find("Standard") ?? Shader.Find("Diffuse");
        Texture2D mainTex = LoadPNG(Path.Combine(texDir, "cha_windblade_gs_deluxe2014_main_a.png"));
        Texture2D mainNM = LoadPNG(Path.Combine(texDir, "main_NM.png"));
        Texture2D wpnsTex = LoadPNG(Path.Combine(texDir, "cha_windblade_gs_deluxe2014_wpns_a.png"));
        Texture2D wpnsNM = LoadPNG(Path.Combine(texDir, "wpns_NM.png"));
        Texture2D tformTex = LoadPNG(Path.Combine(texDir, "tform_misc_A.png"));
        Texture2D tformNM = LoadPNG(Path.Combine(texDir, "tform_misc_NM.png"));

        foreach (var r in inst.GetComponentsInChildren<Renderer>(true)) {
            if (!r.enabled || !r.gameObject.activeInHierarchy) continue;
            Material[] mats = new Material[r.sharedMaterials.Length];
            for (int i = 0; i < mats.Length; i++) {
                string mName = r.sharedMaterials[i] != null ? r.sharedMaterials[i].name.ToLower() : "";
                string rName = r.name.ToLower();
                Material m = new Material(standardShader);
                Texture2D diff = mainTex, bump = mainNM;
                if (mName.Contains("wpn") || mName.Contains("sword") || rName.Contains("wpn") || rName.Contains("sword")) {
                    if (wpnsTex != null) diff = wpnsTex;
                    if (wpnsNM != null) bump = wpnsNM;
                } else if (mName.Contains("tform") || i == 1) {
                    if (tformTex != null) diff = tformTex;
                    if (tformNM != null) bump = tformNM;
                }
                if (diff != null) { m.mainTexture = diff; m.color = Color.white; }
                if (bump != null) { m.EnableKeyword("_NORMALMAP"); m.SetTexture("_BumpMap", bump); }
                m.SetFloat("_Glossiness", 0.50f);
                m.SetFloat("_Metallic", 0.35f);
                mats[i] = m;
            }
            r.sharedMaterials = mats;
        }
    }

    private static Texture2D LoadPNG(string path) {
        if (!File.Exists(path)) return null;
        Texture2D tex = new Texture2D(2, 2, TextureFormat.RGBA32, true);
        tex.LoadImage(File.ReadAllBytes(path));
        return tex;
    }

    private static void RenderStudio(GameObject inst, string outBuildPath, float angleY, int width, int height, float fov) {
        foreach (var c in Object.FindObjectsOfType<Camera>()) Object.DestroyImmediate(c.gameObject);
        foreach (var l in Object.FindObjectsOfType<Light>()) Object.DestroyImmediate(l.gameObject);
        inst.transform.rotation = Quaternion.Euler(0f, angleY, 0f);
        Bounds b = new Bounds(inst.transform.position, Vector3.zero);
        bool hasB = false;
        foreach (var r in inst.GetComponentsInChildren<Renderer>(true)) {
            if (r.enabled && r.gameObject.activeInHierarchy) {
                if (!hasB) { b = r.bounds; hasB = true; } else b.Encapsulate(r.bounds);
            }
        }
        GameObject camObj = new GameObject("RenderCam");
        Camera cam = camObj.AddComponent<Camera>();
        cam.clearFlags = CameraClearFlags.Color;
        cam.backgroundColor = new Color(0.12f, 0.13f, 0.16f, 1f);
        cam.fieldOfView = fov;
        Vector3 center = b.center;
        float radius = Mathf.Max(b.extents.x, b.extents.y, b.extents.z);
        float dist = (radius / Mathf.Sin(cam.fieldOfView * 0.5f * Mathf.Deg2Rad)) * 1.15f;
        camObj.transform.position = center + new Vector3(0f, 0f, -dist);
        camObj.transform.LookAt(center);
        SetupLights();
        CaptureCamera(cam, outBuildPath, width, height);
        inst.transform.rotation = Quaternion.identity;
    }

    private static void RenderCam(Vector3 pos, Vector3 lookAt, string outBuildPath) {
        foreach (var c in Object.FindObjectsOfType<Camera>()) Object.DestroyImmediate(c.gameObject);
        foreach (var l in Object.FindObjectsOfType<Light>()) Object.DestroyImmediate(l.gameObject);
        GameObject camObj = new GameObject("RenderCamClose");
        Camera cam = camObj.AddComponent<Camera>();
        cam.clearFlags = CameraClearFlags.Color;
        cam.backgroundColor = new Color(0.12f, 0.13f, 0.16f, 1f);
        cam.fieldOfView = 26f;
        camObj.transform.position = pos;
        camObj.transform.LookAt(lookAt);
        SetupLights();
        CaptureCamera(cam, outBuildPath, 1024, 1024);
    }

    private static void SetupLights() {
        GameObject l1o = new GameObject("KeyLight"); Light l1 = l1o.AddComponent<Light>(); l1.type = LightType.Directional; l1.intensity = 1.35f; l1o.transform.rotation = Quaternion.Euler(24f, -28f, 0f);
        GameObject l2o = new GameObject("FillLight"); Light l2 = l2o.AddComponent<Light>(); l2.type = LightType.Directional; l2.intensity = 0.75f; l2o.transform.rotation = Quaternion.Euler(15f, 135f, 0f);
        GameObject l3o = new GameObject("RimLight"); Light l3 = l3o.AddComponent<Light>(); l3.type = LightType.Directional; l3.intensity = 0.65f; l3o.transform.rotation = Quaternion.Euler(-20f, 170f, 0f);
    }

    private static void CaptureCamera(Camera cam, string outPath, int width, int height) {
        RenderTexture rt = new RenderTexture(width, height, 24, RenderTextureFormat.ARGB32);
        rt.antiAliasing = 4;
        cam.targetTexture = rt;
        cam.Render();
        RenderTexture.active = rt;
        Texture2D tex = new Texture2D(width, height, TextureFormat.RGB24, false);
        tex.ReadPixels(new Rect(0, 0, width, height), 0, 0);
        tex.Apply();
        cam.targetTexture = null; RenderTexture.active = null;
        Object.DestroyImmediate(rt);
        File.WriteAllBytes(outPath, tex.EncodeToPNG());
        Object.DestroyImmediate(tex);
    }

    private static float GetMinMeshY(GameObject inst) {
        float minY = float.MaxValue;
        foreach (var smr in inst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (!smr.enabled || !smr.gameObject.activeInHierarchy) continue;
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
