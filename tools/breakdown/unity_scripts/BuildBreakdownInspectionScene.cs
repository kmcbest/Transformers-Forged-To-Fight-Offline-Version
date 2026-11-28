using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;
using UnityEngine.SceneManagement;

public static class BuildBreakdownInspectionScene {
    private const string SIDESWIPE_BUNDLE_PATH = @"E:\Agent\TFTF\extracted_apk\assets\assetpack\sideswipe_gs_odr\sideswipe_gs.assetbundle";
    private const string MIRAGE_PREV_PATH = @"E:\Agent\TFTF-blender\scratch\mirage_clips_preview.assetbundle";
    private const string PROC_BUNDLE_PATH = @"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle";
    private const string RENDERS_DIR = @"E:\Agent\TFTF-blender\renders\breakdown";

    private const string ROBOT_FBX = "Assets/Breakdown/breakdown_robot_prepared.fbx";
    private const string VEH_FBX = "Assets/Breakdown/breakdown_veh_prepared.fbx";
    private const string GUN_L_FBX = "Assets/Breakdown/breakdown_gun_l_prepared.fbx";

    private const string ROBOT_ASSET = "Assets/Breakdown/cha_sideswipe_GS_Deluxe2008_00.asset";
    private const string VEH_ASSET = "Assets/Breakdown/cha_sideswipe_GS_Deluxe2008_01.asset";
    private const string GUN_L_ASSET = "Assets/Breakdown/cha_sideswipe_gs_deluxe2008_00_wpns_pistol_left.asset";
    private const string SCENE_PATH = "Assets/Scenes/Breakdown_Inspection.unity";

    struct AxisSpec {
        public bool zIsHeight;
        public float sx;
        public float sz;
        public float det;
    }

    [MenuItem("TFTF/Build Breakdown vs Sideswipe Inspection Scene")]
    public static void Build() {
        Debug.Log("=== [Breakdown] Gate 3 Side-by-Side Inspection Scene (Donor: Sideswipe_GS_Deluxe2008) ===");
        Directory.CreateDirectory(RENDERS_DIR);
        Directory.CreateDirectory(Path.Combine(Application.dataPath, "Scenes"));
        AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);

        foreach (string normP in new[] {
            "Assets/Breakdown/Textures/cha_breakdown_main_Normal_unity.png",
            "Assets/Breakdown/Textures/cha_breakdown_wpns_Normal_unity.png",
            "Assets/Breakdown/Textures/cha_breakdown_sym_Normal_unity.png",
        }) {
            var normTi = AssetImporter.GetAtPath(normP) as TextureImporter;
            if (normTi != null && normTi.textureType != TextureImporterType.NormalMap) {
                normTi.textureType = TextureImporterType.NormalMap;
                normTi.SaveAndReimport();
            }
        }

        foreach (string fp in new[] { ROBOT_FBX, VEH_FBX, GUN_L_FBX }) {
            var mi = AssetImporter.GetAtPath(fp) as ModelImporter;
            if (mi != null) {
                mi.isReadable = true;
                mi.useFileScale = true;
                mi.globalScale = 1.0f;
                mi.importNormals = ModelImporterNormals.Import;
                mi.importTangents = ModelImporterTangents.CalculateMikk;
                mi.animationType = ModelImporterAnimationType.Generic;
                mi.SaveAndReimport();
            }
        }

        foreach (var b in AssetBundle.GetAllLoadedAssetBundles()) b.Unload(false);
        AssetBundle donorBundle = AssetBundle.LoadFromFile(SIDESWIPE_BUNDLE_PATH);
        if (donorBundle == null) {
            Debug.LogError("[Breakdown] Missing Sideswipe bundle: " + SIDESWIPE_BUNDLE_PATH);
            if (Application.isBatchMode) EditorApplication.Exit(1);
            return;
        }

        GameObject donorPrefab = null;
        foreach (var g in donorBundle.LoadAllAssets<GameObject>()) {
            if (g.name.ToLower().Contains("sideswipe") && !g.name.ToLower().Contains("_lw")) {
                donorPrefab = g; break;
            }
        }
        if (donorPrefab == null) {
            Debug.LogError("[Breakdown] Missing Sideswipe prefab!");
            if (Application.isBatchMode) EditorApplication.Exit(1);
            return;
        }

        SkinnedMeshRenderer dSmr00 = null, dSmr01 = null, dSmrGunL = null;
        foreach (var smr in donorPrefab.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name.EndsWith("_00")) dSmr00 = smr;
            else if (smr.name.EndsWith("_01")) dSmr01 = smr;
            else if (smr.name.Contains("pistol_left")) dSmrGunL = smr;
        }

        Avatar officialAvatar00 = donorPrefab.GetComponent<Animator>() != null ? donorPrefab.GetComponent<Animator>().avatar : null;
        if (officialAvatar00 == null) {
            foreach (var av in donorBundle.LoadAllAssets<Avatar>()) {
                if (av.name.Contains("_00")) { officialAvatar00 = av; break; }
            }
        }
        Transform prefabTr = FindChildRecursive(donorPrefab.transform, "transformed");
        Avatar officialAvatar01 = (prefabTr != null && prefabTr.GetComponent<Animator>() != null) ? prefabTr.GetComponent<Animator>().avatar : null;
        if (officialAvatar01 == null) {
            foreach (var av in donorBundle.LoadAllAssets<Avatar>()) {
                if (av.name.Contains("_01")) { officialAvatar01 = av; break; }
            }
        }
        Debug.Log($"[Breakdown] Avatars resolved: av00={(officialAvatar00 != null ? officialAvatar00.name : "NULL")} (isHuman={officialAvatar00?.isHuman}), av01={(officialAvatar01 != null ? officialAvatar01.name : "NULL")}");

        // Build Grafted Meshes
        AxisSpec robotSpec = DetectAxisSpec(ROBOT_FBX);
        Mesh graftedRobot = BuildGraftedMesh(ROBOT_FBX, dSmr00, robotSpec, "cha_sideswipe_GS_Deluxe2008_00", "Hips", null);
        if (AssetDatabase.LoadAssetAtPath<Mesh>(ROBOT_ASSET) != null) AssetDatabase.DeleteAsset(ROBOT_ASSET);
        AssetDatabase.CreateAsset(graftedRobot, ROBOT_ASSET);

        Mesh rawVehMesh = AssetDatabase.LoadAssetAtPath<GameObject>(VEH_FBX).GetComponentInChildren<SkinnedMeshRenderer>(true).sharedMesh;
        AxisSpec vehSpec = DetectVehAxisSpec(rawVehMesh);
        Mesh graftedVeh = BuildGraftedMesh(VEH_FBX, dSmr01, vehSpec, "cha_sideswipe_GS_Deluxe2008_01", "chop2_hip_center", "chop2_hip_center");
        if (AssetDatabase.LoadAssetAtPath<Mesh>(VEH_ASSET) != null) AssetDatabase.DeleteAsset(VEH_ASSET);
        AssetDatabase.CreateAsset(graftedVeh, VEH_ASSET);

        AxisSpec gunSpec = new AxisSpec { zIsHeight = true, sx = 1f, sz = -1f, det = -1f }; // Blender (+X muzzle) -> Unity (-X muzzle) matching Sideswipe pistol_left
        Mesh graftedGunL = BuildGraftedMesh(GUN_L_FBX, dSmrGunL, gunSpec, "cha_sideswipe_gs_deluxe2008_00_wpns_pistol_left", "COG", "COG");
        if (AssetDatabase.LoadAssetAtPath<Mesh>(GUN_L_ASSET) != null) AssetDatabase.DeleteAsset(GUN_L_ASSET);
        AssetDatabase.CreateAsset(graftedGunL, GUN_L_ASSET);

        AssetDatabase.SaveAssets();

        // Standard Materials (persisted as .mat assets BEFORE NewScene so they are never unloaded!)
        Material matBD = new Material(Shader.Find("Standard"));
        matBD.name = "cha_breakdown_main";
        matBD.mainTexture = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Breakdown/Textures/cha_breakdown_main_Diffuse.png");
        matBD.SetTexture("_BumpMap", AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Breakdown/Textures/cha_breakdown_main_Normal_unity.png"));
        matBD.SetTexture("_EmissionMap", AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Breakdown/Textures/cha_breakdown_main_Emission.png"));
        matBD.SetColor("_EmissionColor", Color.white);
        matBD.EnableKeyword("_NORMALMAP");
        matBD.EnableKeyword("_EMISSION");
        matBD.SetFloat("_Glossiness", 0.45f);
        matBD.SetFloat("_Metallic", 0.15f);
        if (AssetDatabase.LoadAssetAtPath<Material>("Assets/Breakdown/cha_breakdown_main.mat") != null)
            AssetDatabase.DeleteAsset("Assets/Breakdown/cha_breakdown_main.mat");
        AssetDatabase.CreateAsset(matBD, "Assets/Breakdown/cha_breakdown_main.mat");

        Material matSym = new Material(Shader.Find("Standard"));
        matSym.name = "cha_breakdown_sym";
        matSym.mainTexture = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Breakdown/Textures/cha_breakdown_sym_Diffuse.png");
        matSym.SetTexture("_BumpMap", AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Breakdown/Textures/cha_breakdown_sym_Normal_unity.png"));
        matSym.EnableKeyword("_NORMALMAP");
        matSym.SetFloat("_Glossiness", 0.35f);
        if (AssetDatabase.LoadAssetAtPath<Material>("Assets/Breakdown/cha_breakdown_sym.mat") != null)
            AssetDatabase.DeleteAsset("Assets/Breakdown/cha_breakdown_sym.mat");
        AssetDatabase.CreateAsset(matSym, "Assets/Breakdown/cha_breakdown_sym.mat");

        Material matWpn = new Material(Shader.Find("Standard"));
        matWpn.name = "cha_breakdown_wpns";
        matWpn.mainTexture = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Breakdown/Textures/cha_breakdown_wpns_Diffuse.png");
        matWpn.SetTexture("_BumpMap", AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Breakdown/Textures/cha_breakdown_wpns_Normal_unity.png"));
        matWpn.EnableKeyword("_NORMALMAP");
        matWpn.SetFloat("_Glossiness", 0.55f);
        matWpn.SetFloat("_Metallic", 0.35f);
        if (AssetDatabase.LoadAssetAtPath<Material>("Assets/Breakdown/cha_breakdown_wpns.mat") != null)
            AssetDatabase.DeleteAsset("Assets/Breakdown/cha_breakdown_wpns.mat");
        AssetDatabase.CreateAsset(matWpn, "Assets/Breakdown/cha_breakdown_wpns.mat");
        AssetDatabase.SaveAssets();

        // Build Android Mesh AssetBundle BEFORE loading external AnimationClips (prevents Unity CleanupMecanimData double-free in UnloadAllAssetBundles)
        BuildMeshAssetBundle();
        donorBundle = AssetBundle.LoadFromFile(SIDESWIPE_BUNDLE_PATH);
        donorPrefab = null;
        foreach (var g in donorBundle.LoadAllAssets<GameObject>()) {
            if (g.name.ToLower().Contains("sideswipe") && !g.name.ToLower().Contains("_lw")) {
                donorPrefab = g; break;
            }
        }
        AssetBundle miragePrevBundle = File.Exists(MIRAGE_PREV_PATH) ? AssetBundle.LoadFromFile(MIRAGE_PREV_PATH) : null;
        AssetBundle procBundle = File.Exists(PROC_BUNDLE_PATH) ? AssetBundle.LoadFromFile(PROC_BUNDLE_PATH) : null;

        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        RenderSettings.ambientLight = new Color(0.55f, 0.55f, 0.58f);

        GameObject lightGo = new GameObject("Key Light");
        Light lk = lightGo.AddComponent<Light>();
        lk.type = LightType.Directional; lk.intensity = 1.25f;
        lightGo.transform.rotation = Quaternion.Euler(40.0f, 155.0f, 0.0f);

        GameObject lightBack = new GameObject("Fill Light");
        Light lb = lightBack.AddComponent<Light>();
        lb.type = LightType.Directional; lb.intensity = 0.75f;
        lightBack.transform.rotation = Quaternion.Euler(30.0f, -35.0f, 0.0f);

        GameObject camGo = new GameObject("Main Camera");
        Camera cam = camGo.AddComponent<Camera>();
        cam.tag = "MainCamera";
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color(0.12f, 0.14f, 0.18f);

        Material matWhite = new Material(Shader.Find("Standard")) { color = new Color(0.88f, 0.88f, 0.88f) };

        GameObject ssInst = UnityEngine.Object.Instantiate(donorPrefab);
        ssInst.name = "Sideswipe_Official_Reference";
        ssInst.transform.position = new Vector3(3.5f, 0.0f, 0.0f);
        SkinnedMeshRenderer s00 = null, s01 = null, sGL = null;
        foreach (var smr in ssInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name.EndsWith("_00")) { smr.sharedMaterials = new[] { matWhite, matWhite, matWhite }; smr.updateWhenOffscreen = true; s00 = smr; }
            else if (smr.name.EndsWith("_01")) { smr.sharedMaterials = new[] { matWhite, matWhite, matWhite, matWhite }; smr.updateWhenOffscreen = true; s01 = smr; }
            else if (smr.name.Contains("pistol_left")) { smr.sharedMaterials = new[] { matWhite }; smr.updateWhenOffscreen = true; sGL = smr; }
            else smr.enabled = false;
        }

        GameObject bdInst = UnityEngine.Object.Instantiate(donorPrefab);
        bdInst.name = "Breakdown_Candidate";
        bdInst.transform.position = new Vector3(-3.5f, 0.0f, 0.0f);
        SkinnedMeshRenderer b00 = null, b01 = null, bGL = null;
        foreach (var smr in bdInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name.EndsWith("_00")) { smr.sharedMesh = graftedRobot; smr.sharedMaterials = new[] { matBD, matSym }; smr.updateWhenOffscreen = true; b00 = smr; }
            else if (smr.name.EndsWith("_01")) { smr.sharedMesh = graftedVeh; smr.sharedMaterials = new[] { matBD, matSym }; smr.updateWhenOffscreen = true; b01 = smr; }
            else if (smr.name.Contains("pistol_left")) { smr.sharedMesh = graftedGunL; smr.sharedMaterials = new[] { matWpn }; smr.updateWhenOffscreen = true; bGL = smr; }
            else smr.enabled = false;
        }

        foreach (var t in ssInst.GetComponentsInChildren<Transform>(true)) GameObjectUtility.RemoveMonoBehavioursWithMissingScript(t.gameObject);
        foreach (var t in bdInst.GetComponentsInChildren<Transform>(true)) GameObjectUtility.RemoveMonoBehavioursWithMissingScript(t.gameObject);

        Animator animSS = ssInst.GetComponent<Animator>();
        Animator animBD = bdInst.GetComponent<Animator>();
        if (officialAvatar00 != null) { animSS.avatar = officialAvatar00; animBD.avatar = officialAvatar00; }
        animSS.cullingMode = AnimatorCullingMode.AlwaysAnimate;
        animBD.cullingMode = AnimatorCullingMode.AlwaysAnimate;
        animSS.applyRootMotion = false;
        animBD.applyRootMotion = false;

        Transform trSS = FindChildRecursive(ssInst.transform, "transformed");
        Transform trBD = FindChildRecursive(bdInst.transform, "transformed");
        Animator animTrSS = trSS != null ? (trSS.GetComponent<Animator>() ?? trSS.gameObject.AddComponent<Animator>()) : null;
        Animator animTrBD = trBD != null ? (trBD.GetComponent<Animator>() ?? trBD.gameObject.AddComponent<Animator>()) : null;
        if (officialAvatar01 != null) {
            if (animTrSS != null) { animTrSS.avatar = officialAvatar01; animTrSS.cullingMode = AnimatorCullingMode.AlwaysAnimate; animTrSS.applyRootMotion = false; }
            if (animTrBD != null) { animTrBD.avatar = officialAvatar01; animTrBD.cullingMode = AnimatorCullingMode.AlwaysAnimate; animTrBD.applyRootMotion = false; }
        }

        EditorSceneManager.SaveScene(scene, SCENE_PATH);
        Debug.Log("[✓] Inspection Scene saved to " + SCENE_PATH);

        RenderPoses(ssInst, bdInst, animSS, animBD, s00, s01, sGL, b00, b01, bGL, trSS, trBD, procBundle, donorBundle, miragePrevBundle, cam);

        Debug.Log("[✓] Gate 3 Breakdown Inspection Scene, Renders, and Mesh Bundle complete!");
        if (Application.isBatchMode) EditorApplication.Exit(0);
    }

    static Transform FindChildRecursive(Transform root, string targetName) {
        if (root == null) return null;
        if (root.name == targetName) return root;
        foreach (Transform c in root) {
            var res = FindChildRecursive(c, targetName);
            if (res != null) return res;
        }
        return null;
    }

    static AxisSpec DetectAxisSpec(string fbxPath) {
        GameObject fbx = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
        SkinnedMeshRenderer smr = fbx.GetComponentInChildren<SkinnedMeshRenderer>(true);
        Mesh raw = smr.sharedMesh;
        bool zIsHeight = raw.bounds.size.z > raw.bounds.size.y * 1.15f;
        Vector3 CentroidOf(string boneName) {
            int bi = -1;
            for (int i = 0; i < smr.bones.Length; i++) if (smr.bones[i].name == boneName) { bi = i; break; }
            if (bi < 0) return Vector3.zero;
            BoneWeight[] bws = raw.boneWeights; Vector3[] vs = raw.vertices;
            Vector3 sum = Vector3.zero; int cnt = 0;
            for (int i = 0; i < bws.Length; i++) {
                if ((bws[i].boneIndex0 == bi && bws[i].weight0 > 0.3f) || (bws[i].boneIndex1 == bi && bws[i].weight1 > 0.3f)) {
                    sum += vs[i]; cnt++;
                }
            }
            return cnt > 0 ? sum / cnt : Vector3.zero;
        }
        Vector3 cLH = CentroidOf("LeftHand");
        Vector3 cToe = CentroidOf("LeftToeBase");
        float sx = (cLH.x <= 0f) ? 1f : -1f;
        float toeDepth = zIsHeight ? cToe.y : cToe.z;
        float sz = (toeDepth >= 0f) ? 1f : -1f;
        return new AxisSpec { zIsHeight = zIsHeight, sx = sx, sz = sz, det = (zIsHeight ? -1f : 1f) * sx * sz };
    }

    static AxisSpec DetectVehAxisSpec(Mesh rawVeh) {
        Vector3 s = rawVeh.bounds.size;
        Vector3 c = rawVeh.bounds.center;
        bool zIsHeight = s.y > s.z * 1.5f;
        float lenCoord = zIsHeight ? c.y : c.z;
        float sz = (lenCoord >= 0f) ? 1f : -1f;
        return new AxisSpec { zIsHeight = zIsHeight, sx = 1f, sz = sz, det = (zIsHeight ? -1f : 1f) * sz };
    }

    static Mesh BuildGraftedMesh(string fbxPath, SkinnedMeshRenderer donorSmr, AxisSpec spec, string meshName, string fallbackBone, string forceSingleBone) {
        GameObject fbx = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
        SkinnedMeshRenderer srcSmr = fbx.GetComponentInChildren<SkinnedMeshRenderer>(true);
        Mesh raw = srcSmr.sharedMesh;

        Vector3[] rv = raw.vertices;
        Vector3[] rn = raw.normals;
        Vector4[] rt = raw.tangents;

        float maxCoord = 0f;
        for (int i = 0; i < rv.Length; i++) maxCoord = Mathf.Max(maxCoord, Mathf.Abs(rv[i].x), Mathf.Abs(rv[i].y), Mathf.Abs(rv[i].z));
        float scaleFix = (maxCoord < 0.5f) ? 100.0f : ((maxCoord > 200.0f) ? 0.01f : 1.0f);

        Vector3[] nv = new Vector3[rv.Length];
        Vector3[] nn = new Vector3[rn.Length];
        Vector4[] nt = new Vector4[rt != null ? rt.Length : 0];
        for (int i = 0; i < rv.Length; i++) {
            Vector3 v = rv[i] * scaleFix;
            nv[i] = spec.zIsHeight ? new Vector3(spec.sx * v.x, v.z, spec.sz * v.y) : new Vector3(spec.sx * v.x, v.y, spec.sz * v.z);
        }
        for (int i = 0; i < rn.Length; i++) {
            Vector3 n = rn[i];
            nn[i] = (spec.zIsHeight ? new Vector3(spec.sx * n.x, n.z, spec.sz * n.y) : new Vector3(spec.sx * n.x, n.y, spec.sz * n.z)).normalized;
        }
        if (rt != null) {
            for (int i = 0; i < rt.Length; i++) {
                Vector4 t = rt[i];
                float tw = (spec.det < 0f) ? -t.w : t.w;
                nt[i] = spec.zIsHeight ? new Vector4(spec.sx * t.x, t.z, spec.sz * t.y, tw) : new Vector4(spec.sx * t.x, t.y, spec.sz * t.z, tw);
            }
        }

        Transform[] donorBones = donorSmr.bones;
        var donorMap = new Dictionary<string, int>();
        for (int i = 0; i < donorBones.Length; i++) donorMap[donorBones[i].name] = i;

        int fallbackIdx = donorMap.ContainsKey(fallbackBone) ? donorMap[fallbackBone] : 0;
        int forcedIdx = (!string.IsNullOrEmpty(forceSingleBone) && donorMap.ContainsKey(forceSingleBone)) ? donorMap[forceSingleBone] : -1;

        Transform[] srcBones = srcSmr.bones;
        int[] srcToDonor = new int[srcBones.Length];
        for (int i = 0; i < srcBones.Length; i++) srcToDonor[i] = donorMap.TryGetValue(srcBones[i].name, out int di) ? di : fallbackIdx;

        BoneWeight[] oldBw = raw.boneWeights;
        BoneWeight[] newBw = new BoneWeight[nv.Length];
        for (int i = 0; i < nv.Length; i++) {
            if (forcedIdx >= 0) {
                newBw[i] = new BoneWeight { boneIndex0 = forcedIdx, weight0 = 1f };
            } else {
                BoneWeight bw = oldBw[i];
                newBw[i] = new BoneWeight {
                    boneIndex0 = srcToDonor[bw.boneIndex0], weight0 = bw.weight0,
                    boneIndex1 = srcToDonor[bw.boneIndex1], weight1 = bw.weight1,
                    boneIndex2 = srcToDonor[bw.boneIndex2], weight2 = bw.weight2,
                    boneIndex3 = srcToDonor[bw.boneIndex3], weight3 = bw.weight3,
                };
            }
        }

        Mesh outMesh = new Mesh();
        outMesh.name = meshName;
        outMesh.indexFormat = (nv.Length > 65534) ? UnityEngine.Rendering.IndexFormat.UInt32 : UnityEngine.Rendering.IndexFormat.UInt16;
        outMesh.vertices = nv;
        outMesh.normals = nn;
        if (rt != null && nt.Length == nv.Length) outMesh.tangents = nt;
        outMesh.uv = raw.uv;
        outMesh.boneWeights = newBw;
        outMesh.bindposes = donorSmr.sharedMesh.bindposes;

        outMesh.subMeshCount = raw.subMeshCount;
        for (int s = 0; s < raw.subMeshCount; s++) {
            int[] tris = raw.GetTriangles(s);
            double dotSum = 0.0;
            for (int t = 0; t + 2 < tris.Length; t += 3) {
                Vector3 cr = Vector3.Cross(nv[tris[t + 1]] - nv[tris[t]], nv[tris[t + 2]] - nv[tris[t]]);
                if (cr.sqrMagnitude > 1e-12f) dotSum += Vector3.Dot(cr.normalized, nn[tris[t]]);
            }
            if (dotSum < 0.0) {
                for (int t = 0; t + 2 < tris.Length; t += 3) { int tmp = tris[t + 1]; tris[t + 1] = tris[t + 2]; tris[t + 2] = tmp; }
            }
            outMesh.SetTriangles(tris, s);
        }
        outMesh.RecalculateBounds();
        Debug.Log($"[BuildGraftedMesh] {meshName} verts={nv.Length} submeshes={raw.subMeshCount} Center={outMesh.bounds.center:F3} Size={outMesh.bounds.size:F3}");
        return outMesh;
    }

    static void CollectClips(AssetBundle b, Dictionary<string, AnimationClip> dict) {
        if (b == null) return;
        foreach (string ap in b.GetAllAssetNames()) {
            foreach (var sub in b.LoadAssetWithSubAssets(ap)) {
                if (sub is AnimationClip ac && !dict.ContainsKey(ac.name)) dict[ac.name] = ac;
            }
        }
        foreach (var c in b.LoadAllAssets<AnimationClip>()) {
            if (c != null && !dict.ContainsKey(c.name)) dict[c.name] = c;
        }
    }

    static void RenderPoses(
        GameObject ssInst, GameObject bdInst,
        Animator animSS, Animator animBD,
        SkinnedMeshRenderer s00, SkinnedMeshRenderer s01, SkinnedMeshRenderer sGL,
        SkinnedMeshRenderer b00, SkinnedMeshRenderer b01, SkinnedMeshRenderer bGL,
        Transform trSS, Transform trBD,
        AssetBundle procBundle, AssetBundle donorBundle, AssetBundle miragePrevBundle, Camera cam
    ) {
        Dictionary<string, AnimationClip> clips = new Dictionary<string, AnimationClip>();
        CollectClips(donorBundle, clips);
        CollectClips(miragePrevBundle, clips);
        CollectClips(procBundle, clips);
        Debug.Log($"[Render] Collected {clips.Count} clips total (has TeamSelect={clips.ContainsKey("TeamSelect_Agile_idle")}, has Victory={(clips.ContainsKey("Agile_Backflip_Victory_Idle"))})");

        var initPos = new Dictionary<Transform, Vector3>();
        var initRot = new Dictionary<Transform, Quaternion>();
        var initScl = new Dictionary<Transform, Vector3>();
        foreach (var t in ssInst.GetComponentsInChildren<Transform>(true)) { initPos[t] = t.localPosition; initRot[t] = t.localRotation; initScl[t] = t.localScale; }
        foreach (var t in bdInst.GetComponentsInChildren<Transform>(true)) { initPos[t] = t.localPosition; initRot[t] = t.localRotation; initScl[t] = t.localScale; }

        void RestoreInit() {
            foreach (var kv in initPos) {
                if (kv.Key != null) { kv.Key.localPosition = kv.Value; kv.Key.localRotation = initRot[kv.Key]; kv.Key.localScale = initScl[kv.Key]; }
            }
            ssInst.transform.SetPositionAndRotation(new Vector3(3.5f, 0f, 0f), Quaternion.identity);
            bdInst.transform.SetPositionAndRotation(new Vector3(-3.5f, 0f, 0f), Quaternion.identity);
        }

        Transform hipsSS = FindChildRecursive(ssInst.transform, "Hips");
        Transform hipsBD = FindChildRecursive(bdInst.transform, "Hips");

        RenderTexture rt = new RenderTexture(1280, 960, 24, RenderTextureFormat.ARGB32) { antiAliasing = 8 };
        cam.targetTexture = rt;

        void RenderShot(string name, string clipName, float t, Vector3 camP, Vector3 look, bool vehMode, bool gunVis) {
            RestoreInit();
            if (trSS != null) trSS.gameObject.SetActive(vehMode);
            if (trBD != null) trBD.gameObject.SetActive(vehMode);
            s00.enabled = !vehMode; s01.gameObject.SetActive(vehMode); s01.enabled = vehMode;
            b00.enabled = !vehMode; b01.gameObject.SetActive(vehMode); b01.enabled = vehMode;
            sGL.enabled = gunVis && !vehMode;
            bGL.enabled = gunVis && !vehMode;

            if (!string.IsNullOrEmpty(clipName) && clips.TryGetValue(clipName, out AnimationClip c)) {
                EvalPairGraph(animSS, animBD, c, t);
            } else if (!string.IsNullOrEmpty(clipName)) {
                Debug.LogWarning($"[Shot {name}] Missing clip '{clipName}'");
            }

            if (!vehMode && hipsSS != null && hipsBD != null) {
                Vector3 dS = hipsSS.position - ssInst.transform.position;
                ssInst.transform.position = new Vector3(3.5f - dS.x, 0f, -dS.z);
                Vector3 dB = hipsBD.position - bdInst.transform.position;
                bdInst.transform.position = new Vector3(-3.5f - dB.x, 0f, -dB.z);
            } else if (vehMode && trSS != null && trBD != null) {
                trSS.SetPositionAndRotation(new Vector3(3.5f, 0f, 0f), Quaternion.identity);
                trBD.SetPositionAndRotation(new Vector3(-3.5f, 0f, 0f), Quaternion.identity);
            }

            var activeSmrs = new List<SkinnedMeshRenderer>();
            if (vehMode) { activeSmrs.Add(s01); activeSmrs.Add(b01); }
            else { activeSmrs.Add(s00); activeSmrs.Add(b00); if (gunVis) { activeSmrs.Add(sGL); activeSmrs.Add(bGL); } }

            var tempGos = new List<GameObject>();
            var tempMeshes = new List<Mesh>();
            foreach (var smr in activeSmrs) {
                if (smr == null) continue;
                Mesh bm = new Mesh();
                smr.BakeMesh(bm, true);
                bm.RecalculateBounds();
                GameObject bgo = new GameObject("Baked_" + smr.name);
                bgo.transform.SetPositionAndRotation(smr.transform.position, smr.transform.rotation);
                bgo.transform.localScale = Vector3.one;
                bgo.AddComponent<MeshFilter>().sharedMesh = bm;
                bgo.AddComponent<MeshRenderer>().sharedMaterials = smr.sharedMaterials;
                smr.enabled = false;
                tempGos.Add(bgo);
                tempMeshes.Add(bm);
            }

            cam.transform.position = camP;
            cam.transform.LookAt(look);
            cam.Render();
            SaveRenderTexture(rt, Path.Combine(RENDERS_DIR, name));

            foreach (var bgo in tempGos) UnityEngine.Object.DestroyImmediate(bgo);
            foreach (var bm in tempMeshes) UnityEngine.Object.DestroyImmediate(bm);
            Debug.Log($"[Render] Saved {name}");
        }

        string rangedClip = null;
        foreach (var kv in clips) {
            if (kv.Key.IndexOf("handgun_left", StringComparison.OrdinalIgnoreCase) >= 0) {
                rangedClip = kv.Key; break;
            }
        }
        if (rangedClip == null && clips.ContainsKey("dual pistols_attackRanged_gun_01")) rangedClip = "dual pistols_attackRanged_gun_01";
        Debug.Log($"[Render] Ranged clip resolved: '{rangedClip}'");

        RenderShot("gate3_00_rest_pose.png", null, 0f, new Vector3(0, 5.0f, 16.5f), new Vector3(0, 4.7f, 0), false, false);
        RenderShot("gate3_01_combat_idle.png", "agile_normal_idle", 0.40f, new Vector3(0, 5.0f, 16.5f), new Vector3(0, 4.7f, 0), false, false);
        RenderShot("gate3_01b_frontend_idle.png", "TeamSelect_Agile_idle", 0.50f, new Vector3(0, 5.0f, 16.5f), new Vector3(0, 4.7f, 0), false, false);
        RenderShot("gate3_01c_frontend_torso_closeup.png", "TeamSelect_Agile_idle", 0.50f, new Vector3(-2.4f, 6.1f, 7.6f), new Vector3(-3.5f, 5.5f, 0), false, false);
        RenderShot("gate3_02_head_chest_closeup.png", "agile_normal_idle", 0.40f, new Vector3(-3.5f, 7.6f, 6.2f), new Vector3(-3.5f, 7.2f, 0), false, false);
        RenderShot("gate3_03_back_3q.png", "agile_normal_idle", 0.40f, new Vector3(5.5f, 5.5f, -15.0f), new Vector3(0, 4.7f, 0), false, false);
        RenderShot("gate3_04_jab_punch.png", "agile_normal_attackLight_01_jab_R", 0.30f, new Vector3(0, 5.2f, 16.5f), new Vector3(0, 4.7f, 0), false, false);
        RenderShot("gate3_04b_jab_fist_closeup.png", "agile_normal_attackLight_01_jab_R", 0.30f, new Vector3(-0.8f, 5.8f, 6.8f), new Vector3(-3.2f, 5.3f, 0.2f), false, false);
        RenderShot("gate3_05_ranged_gun.png", rangedClip, 0.35f, new Vector3(0, 5.2f, 16.5f), new Vector3(0, 4.8f, 0), false, true);
        RenderShot("gate3_05b_gun_closeup.png", rangedClip, 0.35f, new Vector3(0.0f, 6.0f, 8.2f), new Vector3(-3.0f, 5.2f, 0.8f), false, true);
        RenderShot("gate3_07_high_kick.png", "agile_normal_attackLight_04_sidekick_R", 0.35f, new Vector3(0, 5.0f, 16.5f), new Vector3(0, 4.7f, 0), false, false);
        RenderShot("gate3_08b_sp1_open_hand.png", "Mirage_Normal_attackSpecial_01", 0.45f, new Vector3(-3.0f, 5.5f, 7.8f), new Vector3(-6.2f, 4.2f, 0.5f), false, false);
        if (clips.ContainsKey("Agile_Backflip_Victory_Idle")) {
            RenderShot("gate3_09_victory.png", "Agile_Backflip_Victory_Idle", 0.35f, new Vector3(0, 4.2f, 14.5f), new Vector3(0, 2.8f, 0), false, false);
            RenderShot("gate3_09b_victory_hands.png", "Agile_Backflip_Victory_Idle", 0.35f, new Vector3(-2.0f, 3.2f, 7.2f), new Vector3(-3.8f, 2.2f, 0.8f), false, false);
        }
        RenderShot("gate3_06_car_3q.png", null, 0f, new Vector3(6.5f, 6.2f, 12.0f), new Vector3(0f, 1.2f, 0f), true, false);
        RenderShot("gate3_06b_car_side.png", null, 0f, new Vector3(-11.5f, 3.0f, 2.5f), new Vector3(-3.5f, 1.2f, 0f), true, false);

        RestoreInit();
        s00.enabled = true; s01.gameObject.SetActive(false); sGL.enabled = false;
        b00.enabled = true; b01.gameObject.SetActive(false); bGL.enabled = false;
        cam.targetTexture = null;
        UnityEngine.Object.DestroyImmediate(rt);
    }

    static void EvalPairGraph(Animator a1, Animator a2, AnimationClip clip, float time) {
        if (a1 == null || a2 == null || clip == null) return;
        PlayableGraph g1 = PlayableGraph.Create("G1");
        PlayableGraph g2 = PlayableGraph.Create("G2");
        var p1 = AnimationClipPlayable.Create(g1, clip);
        var p2 = AnimationClipPlayable.Create(g2, clip);
        var o1 = AnimationPlayableOutput.Create(g1, "Out1", a1);
        var o2 = AnimationPlayableOutput.Create(g2, "Out2", a2);
        o1.SetSourcePlayable(p1); o2.SetSourcePlayable(p2);
        p1.SetTime(time); p2.SetTime(time);
        g1.Evaluate(0f); g2.Evaluate(0f);
        g1.Destroy(); g2.Destroy();
    }

    static void SaveRenderTexture(RenderTexture rt, string outPath) {
        RenderTexture.active = rt;
        Texture2D tex = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false);
        tex.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0);
        tex.Apply();
        RenderTexture.active = null;
        File.WriteAllBytes(outPath, tex.EncodeToPNG());
        UnityEngine.Object.DestroyImmediate(tex);
    }

    static void BuildMeshAssetBundle() {
        string bundleDir = @"E:\Agent\TFTF-blender\3rd-party-models\Breakdown\04_unity_bundles";
        Directory.CreateDirectory(bundleDir);
        AssetBundleBuild[] builds = new AssetBundleBuild[1];
        builds[0].assetBundleName = "breakdown_mesh.assetbundle";
        builds[0].assetNames = new[] { ROBOT_ASSET, VEH_ASSET, GUN_L_ASSET };
        BuildPipeline.BuildAssetBundles(
            bundleDir,
            builds,
            BuildAssetBundleOptions.ForceRebuildAssetBundle | BuildAssetBundleOptions.ChunkBasedCompression,
            BuildTarget.Android
        );
        Debug.Log("[✓] Built Android Mesh AssetBundle to " + Path.Combine(bundleDir, "breakdown_mesh.assetbundle"));
    }
}
