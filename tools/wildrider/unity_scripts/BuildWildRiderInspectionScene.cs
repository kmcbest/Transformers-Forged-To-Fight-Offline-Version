using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;
using UnityEngine.SceneManagement;

public static class BuildWildRiderInspectionScene {
    private const string PROWL_BUNDLE_PATH = @"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle";
    private const string GALVATRON_BUNDLE_PATH = @"E:\Agent\TFTF-blender\scratch\galv_sp1_preview.assetbundle";
    private const string PROC_BUNDLE_PATH = @"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle";
    private const string RENDERS_DIR = @"E:\Agent\TFTF-blender\renders\wildrider";

    private const string ROBOT_FBX = "Assets/WildRider/wildrider_robot_prepared.fbx";
    private const string VEH_FBX = "Assets/WildRider/wildrider_veh_prepared.fbx";
    private const string GUN_FBX = "Assets/WildRider/wildrider_gun_prepared.fbx";

    private const string ROBOT_ASSET = "Assets/WildRider/cha_prowl_gs_deluxe2016_00.asset";
    private const string VEH_ASSET = "Assets/WildRider/cha_prowl_gs_deluxe2016_01.asset";
    private const string GUN_ASSET = "Assets/WildRider/cha_prowl_gs_deluxe2016_wpns_shotgun.asset";
    private const string SCENE_PATH = "Assets/Scenes/WildRider_Inspection.unity";

    struct AxisSpec {
        public bool zIsHeight;
        public float sx;
        public float sz;
        public float det;
    }

    [MenuItem("TFTF/Build WildRider vs Prowl Inspection Scene")]
    public static void Build() {
        Debug.Log("=== [WildRider] Gate 3 Side-by-Side Inspection Scene (Donor: Prowl_GS_Deluxe2016) ===");
        Directory.CreateDirectory(RENDERS_DIR);
        Directory.CreateDirectory(Path.Combine(Application.dataPath, "Scenes"));
        AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);

        // 1. Configure Normal Map & FBX Importers
        var normTi = AssetImporter.GetAtPath("Assets/WildRider/Textures/cha_wildrider_main_Normal_unity.png") as TextureImporter;
        if (normTi != null && normTi.textureType != TextureImporterType.NormalMap) {
            normTi.textureType = TextureImporterType.NormalMap;
            normTi.SaveAndReimport();
        }

        foreach (string fp in new[] { ROBOT_FBX, VEH_FBX, GUN_FBX }) {
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

        // 2. Load Donor Bundles
        foreach (var b in AssetBundle.GetAllLoadedAssetBundles()) b.Unload(false);
        AssetBundle prowlBundle = AssetBundle.LoadFromFile(PROWL_BUNDLE_PATH);
        if (prowlBundle == null) {
            Debug.LogError("[WildRider] Missing Prowl bundle: " + PROWL_BUNDLE_PATH);
            if (Application.isBatchMode) EditorApplication.Exit(1);
            return;
        }
        AssetBundle procBundle = File.Exists(PROC_BUNDLE_PATH) ? AssetBundle.LoadFromFile(PROC_BUNDLE_PATH) : null;
        AssetBundle galvBundle = File.Exists(GALVATRON_BUNDLE_PATH) ? AssetBundle.LoadFromFile(GALVATRON_BUNDLE_PATH) : null;

        GameObject prowlPrefab = null;
        foreach (var g in prowlBundle.LoadAllAssets<GameObject>()) {
            if (g.name.ToLower().Contains("prowl") && !g.name.ToLower().Contains("_lw")) {
                prowlPrefab = g; break;
            }
        }
        if (prowlPrefab == null) {
            Debug.LogError("[WildRider] Missing Prowl prefab!");
            if (Application.isBatchMode) EditorApplication.Exit(1);
            return;
        }

        SkinnedMeshRenderer prowlSmr00 = null, prowlSmr01 = null, prowlSmrGun = null;
        foreach (var smr in prowlPrefab.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name.Contains("_00")) prowlSmr00 = smr;
            else if (smr.name.Contains("_01")) prowlSmr01 = smr;
            else if (smr.name.Contains("shotgun")) prowlSmrGun = smr;
        }

        // Extract authentic Humanoid & Vehicle Avatars!
        Avatar officialAvatar00 = prowlPrefab.GetComponent<Animator>() != null ? prowlPrefab.GetComponent<Animator>().avatar : null;
        if (officialAvatar00 == null) {
            foreach (var av in prowlBundle.LoadAllAssets<Avatar>()) {
                if (av.name.Contains("_00")) { officialAvatar00 = av; break; }
            }
        }
        Transform prefabTr = FindChildRecursive(prowlPrefab.transform, "transformed");
        Avatar officialAvatar01 = (prefabTr != null && prefabTr.GetComponent<Animator>() != null) ? prefabTr.GetComponent<Animator>().avatar : null;
        if (officialAvatar01 == null) {
            foreach (var av in prowlBundle.LoadAllAssets<Avatar>()) {
                if (av.name.Contains("_01")) { officialAvatar01 = av; break; }
            }
        }
        Debug.Log($"[WildRider] Avatars resolved: av00={(officialAvatar00 != null ? officialAvatar00.name : "NULL")} (isHuman={officialAvatar00?.isHuman}), av01={(officialAvatar01 != null ? officialAvatar01.name : "NULL")}");

        // 3. Build Grafted Meshes via DeleteAsset + CreateAsset
        AxisSpec robotSpec = DetectAxisSpec(ROBOT_FBX);
        Mesh graftedRobot = BuildGraftedMesh(ROBOT_FBX, prowlSmr00, robotSpec, "cha_prowl_gs_deluxe2016_00", "Hips", null);
        if (AssetDatabase.LoadAssetAtPath<Mesh>(ROBOT_ASSET) != null) AssetDatabase.DeleteAsset(ROBOT_ASSET);
        AssetDatabase.CreateAsset(graftedRobot, ROBOT_ASSET);

        GameObject vehFbxObj = AssetDatabase.LoadAssetAtPath<GameObject>(VEH_FBX);
        Mesh rawVehMesh = vehFbxObj.GetComponentInChildren<SkinnedMeshRenderer>(true).sharedMesh;
        AxisSpec vehSpec = DetectVehAxisSpec(rawVehMesh);
        Mesh graftedVeh = BuildGraftedMesh(VEH_FBX, prowlSmr01, vehSpec, "cha_prowl_gs_deluxe2016_01", "COG", null);
        if (AssetDatabase.LoadAssetAtPath<Mesh>(VEH_ASSET) != null) AssetDatabase.DeleteAsset(VEH_ASSET);
        AssetDatabase.CreateAsset(graftedVeh, VEH_ASSET);

        GameObject gunFbxObj = AssetDatabase.LoadAssetAtPath<GameObject>(GUN_FBX);
        Mesh rawGunMesh = gunFbxObj.GetComponentInChildren<SkinnedMeshRenderer>(true).sharedMesh;
        AxisSpec gunSpec = DetectGunAxisSpec(rawGunMesh);
        Mesh graftedGun = BuildGraftedMesh(GUN_FBX, prowlSmrGun, gunSpec, "cha_prowl_gs_deluxe2016_wpns_shotgun", "Shutgun", "Shutgun");
        if (AssetDatabase.LoadAssetAtPath<Mesh>(GUN_ASSET) != null) AssetDatabase.DeleteAsset(GUN_ASSET);
        AssetDatabase.CreateAsset(graftedGun, GUN_ASSET);

        AssetDatabase.SaveAssets();

        // 4. Create WildRider Standard Preview Material
        Material matWR = new Material(Shader.Find("Standard"));
        matWR.name = "cha_wildrider_main";
        matWR.mainTexture = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/WildRider/Textures/cha_wildrider_main_Diffuse.png");
        matWR.SetTexture("_BumpMap", AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/WildRider/Textures/cha_wildrider_main_Normal_unity.png"));
        matWR.SetTexture("_EmissionMap", AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/WildRider/Textures/cha_wildrider_main_Emission.png"));
        matWR.SetColor("_EmissionColor", Color.white);
        matWR.EnableKeyword("_EMISSION");
        matWR.EnableKeyword("_NORMALMAP");
        matWR.SetFloat("_Glossiness", 0.45f);
        matWR.SetFloat("_Metallic", 0.12f);
        if (AssetDatabase.LoadAssetAtPath<Material>("Assets/WildRider/cha_wildrider_main.mat") != null)
            AssetDatabase.DeleteAsset("Assets/WildRider/cha_wildrider_main.mat");
        AssetDatabase.CreateAsset(matWR, "Assets/WildRider/cha_wildrider_main.mat");
        AssetDatabase.SaveAssets();

        // 5. Build Side-by-Side Scene
        Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        GameObject lightFront = new GameObject("Directional Light Front");
        Light lf = lightFront.AddComponent<Light>();
        lf.type = LightType.Directional; lf.intensity = 1.25f;
        lightFront.transform.rotation = Quaternion.Euler(40.0f, 155.0f, 0.0f);

        GameObject lightBack = new GameObject("Directional Light Back");
        Light lb = lightBack.AddComponent<Light>();
        lb.type = LightType.Directional; lb.intensity = 0.75f;
        lightBack.transform.rotation = Quaternion.Euler(30.0f, -35.0f, 0.0f);

        GameObject camGo = new GameObject("Main Camera");
        Camera cam = camGo.AddComponent<Camera>();
        cam.tag = "MainCamera";
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color(0.12f, 0.14f, 0.18f);

        GameObject prowlInst = UnityEngine.Object.Instantiate(prowlPrefab);
        prowlInst.name = "Prowl_Official_Reference";
        prowlInst.transform.position = new Vector3(3.5f, 0.0f, 0.0f);

        Material prMain = new Material(Shader.Find("Standard"));
        prMain.mainTexture = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/WildRider/Prowl/cha_prowl_gs_deluxe2016_main_a.png");
        Material prMisc = new Material(Shader.Find("Standard"));
        prMisc.mainTexture = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/WildRider/Prowl/tform_misc_A.png");
        Material prWpn = new Material(Shader.Find("Standard"));
        prWpn.mainTexture = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/WildRider/Prowl/cha_prowl_gs_deluxe2016_wpns_a.png");

        SkinnedMeshRenderer pr00 = null, pr01 = null, prGun = null;
        foreach (var smr in prowlInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name.Contains("_00")) { smr.sharedMaterials = new[] { prMain, prMisc }; smr.updateWhenOffscreen = true; pr00 = smr; }
            else if (smr.name.Contains("_01")) { smr.sharedMaterials = new[] { prMisc, prMain, prMisc }; smr.updateWhenOffscreen = true; pr01 = smr; }
            else if (smr.name.Contains("shotgun")) { smr.sharedMaterials = new[] { prWpn }; smr.updateWhenOffscreen = true; prGun = smr; }
            else smr.enabled = false;
        }

        GameObject wrInst = UnityEngine.Object.Instantiate(prowlPrefab);
        wrInst.name = "WildRider_Candidate";
        wrInst.transform.position = new Vector3(-3.5f, 0.0f, 0.0f);

        SkinnedMeshRenderer wr00 = null, wr01 = null, wrGun = null;
        foreach (var smr in wrInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name.Contains("_00")) {
                smr.sharedMesh = graftedRobot;
                smr.sharedMaterials = new[] { matWR };
                smr.updateWhenOffscreen = true;
                wr00 = smr;
            } else if (smr.name.Contains("_01")) {
                smr.sharedMesh = graftedVeh;
                smr.sharedMaterials = new[] { matWR };
                smr.updateWhenOffscreen = true;
                wr01 = smr;
            } else if (smr.name.Contains("shotgun")) {
                smr.sharedMesh = graftedGun;
                smr.sharedMaterials = new[] { matWR };
                smr.updateWhenOffscreen = true;
                wrGun = smr;
            } else {
                smr.enabled = false;
            }
        }

        // Remove missing MonoBehaviours from Unity 5 runtime so Animators evaluate cleanly!
        foreach (var t in prowlInst.GetComponentsInChildren<Transform>(true)) GameObjectUtility.RemoveMonoBehavioursWithMissingScript(t.gameObject);
        foreach (var t in wrInst.GetComponentsInChildren<Transform>(true)) GameObjectUtility.RemoveMonoBehavioursWithMissingScript(t.gameObject);

        Animator animPr = prowlInst.GetComponent<Animator>();
        Animator animWR = wrInst.GetComponent<Animator>();
        if (officialAvatar00 != null) { animPr.avatar = officialAvatar00; animWR.avatar = officialAvatar00; }
        animPr.cullingMode = AnimatorCullingMode.AlwaysAnimate;
        animWR.cullingMode = AnimatorCullingMode.AlwaysAnimate;
        animPr.applyRootMotion = false;
        animWR.applyRootMotion = false;

        Transform trPr = FindChildRecursive(prowlInst.transform, "transformed");
        Transform trWR = FindChildRecursive(wrInst.transform, "transformed");
        Animator animTrPr = trPr != null ? (trPr.GetComponent<Animator>() ?? trPr.gameObject.AddComponent<Animator>()) : null;
        Animator animTrWR = trWR != null ? (trWR.GetComponent<Animator>() ?? trWR.gameObject.AddComponent<Animator>()) : null;
        if (officialAvatar01 != null) {
            if (animTrPr != null) { animTrPr.avatar = officialAvatar01; animTrPr.cullingMode = AnimatorCullingMode.AlwaysAnimate; animTrPr.applyRootMotion = false; }
            if (animTrWR != null) { animTrWR.avatar = officialAvatar01; animTrWR.cullingMode = AnimatorCullingMode.AlwaysAnimate; animTrWR.applyRootMotion = false; }
        }

        // Snap Shutgun bone under RightHand -> gun for accurate runtime gun-in-hand visualization!
        DockShotgunToRightHand(prowlInst);
        DockShotgunToRightHand(wrInst);

        EditorSceneManager.SaveScene(scene, SCENE_PATH);
        Debug.Log("[✓] Inspection Scene saved to " + SCENE_PATH);

        // 6. Render Synced Comparison Poses using BakeMesh()
        RenderPoses(prowlInst, wrInst, animPr, animWR, animTrPr, animTrWR, pr00, pr01, prGun, wr00, wr01, wrGun, trPr, trWR, procBundle, prowlBundle, galvBundle, cam);

        // 7. Build Android Mesh AssetBundle
        BuildMeshAssetBundle();

        Debug.Log("[✓] Gate 3 WildRider Inspection Scene, Renders, and Mesh Bundle complete!");
        if (Application.isBatchMode) EditorApplication.Exit(0);
    }

    static void DockShotgunToRightHand(GameObject inst) {
        Transform rh = FindChildRecursive(inst.transform, "RightHand");
        Transform gunNode = FindChildRecursive(inst.transform, "gun");
        Transform shutgunBone = FindChildRecursive(inst.transform, "Shutgun");
        if (gunNode != null && rh != null) {
            gunNode.SetParent(rh, false);
            gunNode.localPosition = new Vector3(-0.38f, 0.16f, -0.433f);
            gunNode.localRotation = Quaternion.Euler(0f, -90f, -90f);
            gunNode.localScale = new Vector3(1.2f, 1.2f, 1.2f);
        }
        if (shutgunBone != null && gunNode != null) {
            shutgunBone.SetParent(gunNode, false);
            shutgunBone.localPosition = Vector3.zero;
            shutgunBone.localRotation = Quaternion.identity;
            shutgunBone.localScale = Vector3.one;
        }
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
            BoneWeight[] bws = raw.boneWeights;
            Vector3[] vs = raw.vertices;
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
        float det = (zIsHeight ? -1f : 1f) * sx * sz;
        return new AxisSpec { zIsHeight = zIsHeight, sx = sx, sz = sz, det = det };
    }

    static AxisSpec DetectVehAxisSpec(Mesh rawVeh) {
        Vector3 s = rawVeh.bounds.size;
        Vector3 c = rawVeh.bounds.center;
        bool zIsHeight = s.y > s.z * 1.5f;
        float lenCoord = zIsHeight ? c.y : c.z;
        float sz = (lenCoord >= 0f) ? 1f : -1f;
        float sx = 1f;
        float det = (zIsHeight ? -1f : 1f) * sx * sz;
        return new AxisSpec { zIsHeight = zIsHeight, sx = sx, sz = sz, det = det };
    }

    static AxisSpec DetectGunAxisSpec(Mesh rawGun) {
        Vector3 s = rawGun.bounds.size;
        Vector3 c = rawGun.bounds.center;
        bool zIsHeight = s.y > s.z * 1.5f;
        float gunLenCoord = zIsHeight ? c.y : c.z;
        float sz = (gunLenCoord < 0f) ? 1f : -1f;
        float sx = 1f;
        float det = (zIsHeight ? -1f : 1f) * sx * sz;
        Debug.Log($"[Gun AxisSpec] rawBounds={rawGun.bounds} size={s} center={c} -> zIsHeight={zIsHeight}, sx={sx}, sz={sz}");
        return new AxisSpec { zIsHeight = zIsHeight, sx = sx, sz = sz, det = det };
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
        if (Mathf.Abs(scaleFix - 1.0f) > 0.01f) Debug.Log($"[ScaleFix] {meshName} raw maxCoord={maxCoord:F4} -> scaleFix={scaleFix}");

        Vector3[] nv = new Vector3[rv.Length];
        Vector3[] nn = new Vector3[rn.Length];
        Vector4[] nt = new Vector4[rt != null ? rt.Length : 0];

        bool useZHeight = spec.zIsHeight;
        float useSx = spec.sx;
        float useSz = spec.sz;

        for (int i = 0; i < rv.Length; i++) {
            Vector3 v = rv[i] * scaleFix;
            nv[i] = useZHeight ? new Vector3(useSx * v.x, v.z, useSz * v.y) : new Vector3(useSx * v.x, v.y, useSz * v.z);
        }
        for (int i = 0; i < rn.Length; i++) {
            Vector3 n = rn[i];
            nn[i] = (useZHeight ? new Vector3(useSx * n.x, n.z, useSz * n.y) : new Vector3(useSx * n.x, n.y, useSz * n.z)).normalized;
        }
        if (rt != null) {
            for (int i = 0; i < rt.Length; i++) {
                Vector4 t = rt[i];
                float tw = (spec.det < 0f) ? -t.w : t.w;
                nt[i] = useZHeight ? new Vector4(useSx * t.x, t.z, useSz * t.y, tw) : new Vector4(useSx * t.x, t.y, useSz * t.z, tw);
            }
        }

        Bounds tmpB = new Bounds(nv[0], Vector3.zero);
        for (int i = 1; i < nv.Length; i++) tmpB.Encapsulate(nv[i]);
        double outerDot = 0.0;
        for (int i = 0; i < nv.Length; i++) {
            Vector3 d = nv[i] - tmpB.center;
            if (d.sqrMagnitude > 0.25f * tmpB.extents.sqrMagnitude) outerDot += Vector3.Dot(d.normalized, nn[i]);
        }
        if (outerDot < 0.0) {
            for (int i = 0; i < nn.Length; i++) nn[i] = -nn[i];
        }

        Transform[] donorBones = donorSmr.bones;
        Dictionary<string, int> donorMap = new Dictionary<string, int>();
        for (int i = 0; i < donorBones.Length; i++) if (donorBones[i] != null) donorMap[donorBones[i].name] = i;
        int fbIdx = donorMap.ContainsKey(fallbackBone) ? donorMap[fallbackBone] : 0;

        int[] remap = new int[srcSmr.bones.Length];
        for (int j = 0; j < srcSmr.bones.Length; j++) {
            string bn = srcSmr.bones[j] != null ? srcSmr.bones[j].name : "";
            remap[j] = donorMap.TryGetValue(bn, out int idx) ? idx : fbIdx;
        }

        BoneWeight[] origBw = raw.boneWeights;
        BoneWeight[] newBw = new BoneWeight[rv.Length];
        if (!string.IsNullOrEmpty(forceSingleBone) && donorMap.TryGetValue(forceSingleBone, out int forcedIdx)) {
            for (int i = 0; i < rv.Length; i++) newBw[i] = new BoneWeight { boneIndex0 = forcedIdx, weight0 = 1.0f };
        } else {
            for (int i = 0; i < origBw.Length; i++) {
                BoneWeight bw = origBw[i];
                bw.boneIndex0 = (bw.boneIndex0 >= 0 && bw.boneIndex0 < remap.Length) ? remap[bw.boneIndex0] : fbIdx;
                bw.boneIndex1 = (bw.boneIndex1 >= 0 && bw.boneIndex1 < remap.Length) ? remap[bw.boneIndex1] : fbIdx;
                bw.boneIndex2 = (bw.boneIndex2 >= 0 && bw.boneIndex2 < remap.Length) ? remap[bw.boneIndex2] : fbIdx;
                bw.boneIndex3 = (bw.boneIndex3 >= 0 && bw.boneIndex3 < remap.Length) ? remap[bw.boneIndex3] : fbIdx;
                newBw[i] = bw;
            }
        }

        Mesh outMesh = new Mesh { name = meshName };
        if (nv.Length > 65535) outMesh.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;
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
                for (int t = 0; t + 2 < tris.Length; t += 3) {
                    int tmp = tris[t + 1]; tris[t + 1] = tris[t + 2]; tris[t + 2] = tmp;
                }
            }
            outMesh.SetTriangles(tris, s);
        }
        outMesh.RecalculateBounds();
        Debug.Log($"[BuildGraftedMesh] {meshName} verts={nv.Length} Center={outMesh.bounds.center:F3} Size={outMesh.bounds.size:F3}");
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
        GameObject prowlInst, GameObject wrInst,
        Animator animPr, Animator animWR, Animator animTrPr, Animator animTrWR,
        SkinnedMeshRenderer pr00, SkinnedMeshRenderer pr01, SkinnedMeshRenderer prGun,
        SkinnedMeshRenderer wr00, SkinnedMeshRenderer wr01, SkinnedMeshRenderer wrGun,
        Transform trPr, Transform trWR,
        AssetBundle procBundle, AssetBundle prowlBundle, AssetBundle galvBundle, Camera cam
    ) {
        Dictionary<string, AnimationClip> clips = new Dictionary<string, AnimationClip>();
        CollectClips(prowlBundle, clips);
        CollectClips(galvBundle, clips);
        CollectClips(procBundle, clips);
        Debug.Log($"[Render] Collected {clips.Count} clips total (has GalvS1={clips.ContainsKey("Galvatron_GS_attackSpecial_01")}, has Jab={clips.ContainsKey("tactical_normal_attacklight_01_jab_L")})");

        // Cache initial poses so every shot restores clean rest pose before EvalPairGraph!
        var initPos = new Dictionary<Transform, Vector3>();
        var initRot = new Dictionary<Transform, Quaternion>();
        var initScl = new Dictionary<Transform, Vector3>();
        foreach (var t in prowlInst.GetComponentsInChildren<Transform>(true)) { initPos[t] = t.localPosition; initRot[t] = t.localRotation; initScl[t] = t.localScale; }
        foreach (var t in wrInst.GetComponentsInChildren<Transform>(true)) { initPos[t] = t.localPosition; initRot[t] = t.localRotation; initScl[t] = t.localScale; }

        void RestoreInit() {
            foreach (var kv in initPos) {
                if (kv.Key != null) { kv.Key.localPosition = kv.Value; kv.Key.localRotation = initRot[kv.Key]; kv.Key.localScale = initScl[kv.Key]; }
            }
            prowlInst.transform.SetPositionAndRotation(new Vector3(3.5f, 0f, 0f), Quaternion.identity);
            wrInst.transform.SetPositionAndRotation(new Vector3(-3.5f, 0f, 0f), Quaternion.identity);
        }

        // Pick a genuine kick clip name
        string kickClip = null;
        foreach (string cand in new[] { "tactical_normal_attackMedium_01", "tactical_normal_attackMedium_02", "brawler_normal_attackMedium_01", "brawler_normal_attackMedium_02" }) {
            if (clips.ContainsKey(cand)) { kickClip = cand; break; }
        }
        if (kickClip == null) {
            foreach (var k in clips.Keys) {
                if (k.ToLower().Contains("attackmedium_0") && !k.Contains("transformed")) { kickClip = k; break; }
            }
        }
        Debug.Log($"[Render] Selected kick clip: '{kickClip}'");

        Transform hipsPr = FindChildRecursive(prowlInst.transform, "Hips");
        Transform hipsWR = FindChildRecursive(wrInst.transform, "Hips");

        RenderTexture rt = new RenderTexture(1280, 960, 24, RenderTextureFormat.ARGB32) { antiAliasing = 8 };
        cam.targetTexture = rt;

        void RenderShot(string name, string clipName, float t, Vector3 camP, Vector3 look, bool vehMode, bool gunVis, string transClip = null) {
            RestoreInit();
            if (trPr != null) trPr.gameObject.SetActive(vehMode);
            if (trWR != null) trWR.gameObject.SetActive(vehMode);
            pr00.enabled = !vehMode; pr01.gameObject.SetActive(vehMode); pr01.enabled = vehMode;
            wr00.enabled = !vehMode; wr01.gameObject.SetActive(vehMode); wr01.enabled = vehMode;
            prGun.enabled = gunVis && !vehMode;
            wrGun.enabled = gunVis && !vehMode;

            if (!string.IsNullOrEmpty(clipName) && clips.TryGetValue(clipName, out AnimationClip c)) {
                EvalPairGraph(animPr, animWR, c, t);
            } else if (!string.IsNullOrEmpty(clipName)) {
                Debug.LogWarning($"[Shot {name}] Missing clip '{clipName}'");
            }
            if (vehMode && !string.IsNullOrEmpty(transClip) && clips.TryGetValue(transClip, out AnimationClip tc) && animTrPr != null && animTrWR != null) {
                EvalPairGraph(animTrPr, animTrWR, tc, t);
            }

            if (!vehMode && hipsPr != null && hipsWR != null) {
                Vector3 dP = hipsPr.position - prowlInst.transform.position;
                prowlInst.transform.position = new Vector3(3.5f - dP.x, 0f, -dP.z);
                Vector3 dW = hipsWR.position - wrInst.transform.position;
                wrInst.transform.position = new Vector3(-3.5f - dW.x, 0f, -dW.z);
            } else if (vehMode) {
                prowlInst.transform.SetPositionAndRotation(new Vector3(3.5f, 0f, 0f), Quaternion.Euler(90f, 0f, 0f));
                wrInst.transform.SetPositionAndRotation(new Vector3(-3.5f, 0f, 0f), Quaternion.Euler(90f, 0f, 0f));
            }

            // CRITICAL: BakeMesh into temporary MeshRenderer before cam.Render() so Editor renders true evaluated pose!
            var activeSmrs = new List<SkinnedMeshRenderer>();
            if (vehMode) { activeSmrs.Add(pr01); activeSmrs.Add(wr01); }
            else { activeSmrs.Add(pr00); activeSmrs.Add(wr00); if (gunVis) { activeSmrs.Add(prGun); activeSmrs.Add(wrGun); } }

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
                if (!vehMode && (smr == wr00 || smr == pr00) && (name == "gate3_00_rest_pose.png" || name == "gate3_01d_char_idle.png" || name == "gate3_01c_frontend_torso_closeup.png" || name == "gate3_04b_jab_fist_closeup.png")) {
                    int tbIdx = -1, tb2Idx = -1, tb3Idx = -1, hbIdx = -1;
                    int rtbIdx = -1, rtb2Idx = -1, rtb3Idx = -1, rhbIdx = -1;
                    for (int bi = 0; bi < smr.bones.Length; bi++) {
                        string bn = smr.bones[bi].name;
                        if (bn == "LeftHandThumb1") tbIdx = bi;
                        if (bn == "LeftHandThumb2") tb2Idx = bi;
                        if (bn == "LeftHandThumb3") tb3Idx = bi;
                        if (bn == "LeftHand") hbIdx = bi;
                        if (bn == "RightHandThumb1") rtbIdx = bi;
                        if (bn == "RightHandThumb2") rtb2Idx = bi;
                        if (bn == "RightHandThumb3") rtb3Idx = bi;
                        if (bn == "RightHand") rhbIdx = bi;
                    }
                    BoneWeight[] bws = smr.sharedMesh.boneWeights; Vector3[] verts = bm.vertices;
                    Vector3 tMin = Vector3.one * 999f, tMax = Vector3.one * -999f; int tCnt = 0;
                    Vector3 hMin = Vector3.one * 999f, hMax = Vector3.one * -999f; int hCnt = 0;
                    Vector3 rtMin = Vector3.one * 999f, rtMax = Vector3.one * -999f; int rtCnt = 0;
                    Vector3 rhMin = Vector3.one * 999f, rhMax = Vector3.one * -999f; int rhCnt = 0;
                    int n = Mathf.Min(verts.Length, bws.Length);
                    for (int vi = 0; vi < n; vi++) {
                        Vector3 wp = bgo.transform.TransformPoint(verts[vi]);
                        int b0 = bws[vi].boneIndex0;
                        if ((b0 == tbIdx || b0 == tb2Idx || b0 == tb3Idx) && bws[vi].weight0 > 0.3f) { tMin = Vector3.Min(tMin, wp); tMax = Vector3.Max(tMax, wp); tCnt++; }
                        if (b0 == hbIdx && bws[vi].weight0 > 0.3f) { hMin = Vector3.Min(hMin, wp); hMax = Vector3.Max(hMax, wp); hCnt++; }
                        if ((b0 == rtbIdx || b0 == rtb2Idx || b0 == rtb3Idx) && bws[vi].weight0 > 0.3f) { rtMin = Vector3.Min(rtMin, wp); rtMax = Vector3.Max(rtMax, wp); rtCnt++; }
                        if (b0 == rhbIdx && bws[vi].weight0 > 0.3f) { rhMin = Vector3.Min(rhMin, wp); rhMax = Vector3.Max(rhMax, wp); rhCnt++; }
                    }
                    string who = smr == pr00 ? "PROWL" : "WILDRIDER";
                    string bpos = tbIdx >= 0 ? $"LT1p={smr.bones[tbIdx].position:F3} LT2p={(tb2Idx>=0?smr.bones[tb2Idx].position.ToString("F3"):"?")} LT3p={(tb3Idx>=0?smr.bones[tb3Idx].position.ToString("F3"):"?")}" : "";
                    Debug.Log($"[Render ThumbDiag {name} {who}] LH({hCnt}v)=[{hMin:F3}..{hMax:F3}] LT_all({tCnt}v)=[{tMin:F3}..{tMax:F3}] RH({rhCnt}v)=[{rhMin:F3}..{rhMax:F3}] RT_all({rtCnt}v)=[{rtMin:F3}..{rtMax:F3}] {bpos}");
                }
            }

            cam.transform.position = camP;
            cam.transform.LookAt(look);
            cam.Render();
            SaveRenderTexture(rt, Path.Combine(RENDERS_DIR, name));

            foreach (var bgo in tempGos) UnityEngine.Object.DestroyImmediate(bgo);
            foreach (var bm in tempMeshes) UnityEngine.Object.DestroyImmediate(bm);
            Debug.Log($"[Render] Saved {name}");
        }

        RenderShot("gate3_00_rest_pose.png", null, 0f, new Vector3(0, 5.0f, 16.5f), new Vector3(0, 4.7f, 0), false, false);
        RenderShot("gate3_01_combat_idle.png", "tactical_normal_idle", 0.40f, new Vector3(0, 5.0f, 16.5f), new Vector3(0, 4.7f, 0), false, false);
        RenderShot("gate3_01b_frontend_idle.png", "TeamSelect_Agile_idle", 0.50f, new Vector3(0, 5.0f, 16.5f), new Vector3(0, 4.7f, 0), false, false);
        RenderShot("gate3_01c_frontend_torso_closeup.png", "TeamSelect_Agile_idle", 0.50f, new Vector3(-2.5f, 6.2f, 7.8f), new Vector3(-3.5f, 5.6f, 0), false, false);
        RenderShot("gate3_01d_char_idle.png", "char_idle", 0.30f, new Vector3(-2.5f, 5.4f, 8.5f), new Vector3(-3.5f, 4.5f, 0), false, false);
        RenderShot("gate3_02_head_chest_closeup.png", "tactical_normal_idle", 0.40f, new Vector3(-3.5f, 7.6f, 6.2f), new Vector3(-3.5f, 7.2f, 0), false, false);
        RenderShot("gate3_03_back_3q.png", "tactical_normal_idle", 0.40f, new Vector3(5.5f, 5.5f, -15.0f), new Vector3(0, 4.7f, 0), false, false);
        RenderShot("gate3_04_jab_punch.png", "tactical_normal_attacklight_01_jab_L", 0.30f, new Vector3(0, 5.2f, 16.5f), new Vector3(0, 4.7f, 0), false, false);
        RenderShot("gate3_04b_jab_fist_closeup.png", "tactical_normal_attacklight_01_jab_L", 0.30f, new Vector3(-0.8f, 5.8f, 6.8f), new Vector3(-3.2f, 5.3f, 0.2f), false, false);
        RenderShot("gate3_05_ranged_gun.png", "TwoHnad_R_attackRanged_01", 0.35f, new Vector3(0, 5.2f, 16.5f), new Vector3(0, 4.8f, 0), false, true);
        RenderShot("gate3_05b_gun_in_hand_closeup.png", "TwoHnad_R_attackRanged_01", 0.35f, new Vector3(-0.2f, 6.2f, 6.8f), new Vector3(-3.2f, 5.2f, 0.4f), false, true);
        RenderShot("gate3_07_high_kick_extreme.png", kickClip, 0.35f, new Vector3(0, 5.0f, 16.5f), new Vector3(0, 4.7f, 0), false, false);
        RenderShot("gate3_08_sp1_galvatron.png", "Galvatron_GS_attackSpecial_01", 0.55f, new Vector3(0, 5.2f, 17.5f), new Vector3(0, 4.8f, 0), false, false);
        RenderShot("gate3_08b_sp1_open_hand.png", "Mirage_Normal_attackSpecial_01", 0.45f, new Vector3(-3.0f, 5.5f, 7.8f), new Vector3(-6.2f, 4.2f, 0.5f), false, false);
        RenderShot("gate3_09_sp2_motormaster.png", "motormaster_gs_attackSpecial_02", 0.55f, new Vector3(0, 5.2f, 17.5f), new Vector3(0, 4.8f, 0), false, false);
        RenderShot("gate3_06_vehicle_3q.png", "frontend_Prowl_levelup_vehicle_idle_transformed", 0.25f, new Vector3(6.5f, 6.2f, 11.5f), new Vector3(0f, 1.2f, 0f), true, false, "frontend_Prowl_levelup_vehicle_idle_transformed");
        RenderShot("gate3_06b_vehicle_side.png", "Car_Prowl_Normal_attackHeavy_transformed", 0.45f, new Vector3(-11.5f, 3.0f, 2.5f), new Vector3(-3.5f, 1.2f, 0f), true, false, "Car_Prowl_Normal_attackHeavy_transformed");

        RestoreInit();
        pr00.enabled = true; pr01.gameObject.SetActive(false); prGun.enabled = false;
        wr00.enabled = true; wr01.gameObject.SetActive(false); wrGun.enabled = false;
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
        o1.SetSourcePlayable(p1);
        o2.SetSourcePlayable(p2);
        p1.SetTime(time);
        p2.SetTime(time);
        g1.Evaluate(0f);
        g2.Evaluate(0f);
        g1.Destroy();
        g2.Destroy();
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
        string bundleDir = @"E:\Agent\TFTF-blender\3rd-party-models\WildRider\04_unity_bundles";
        Directory.CreateDirectory(bundleDir);
        AssetBundleBuild[] builds = new AssetBundleBuild[1];
        builds[0].assetBundleName = "wildrider_mesh.assetbundle";
        builds[0].assetNames = new[] { ROBOT_ASSET, VEH_ASSET, GUN_ASSET };
        BuildPipeline.BuildAssetBundles(
            bundleDir,
            builds,
            BuildAssetBundleOptions.ForceRebuildAssetBundle | BuildAssetBundleOptions.ChunkBasedCompression,
            BuildTarget.Android
        );
        Debug.Log("[✓] Built Android Mesh AssetBundle to " + Path.Combine(bundleDir, "wildrider_mesh.assetbundle"));
    }
}
