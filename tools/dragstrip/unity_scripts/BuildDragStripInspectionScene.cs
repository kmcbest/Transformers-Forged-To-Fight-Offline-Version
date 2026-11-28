using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;
using UnityEngine.SceneManagement;

public static class BuildDragStripInspectionScene {
    private const string MIRAGE_BUNDLE_PATH = @"E:\Agent\TFTF\extracted_apk\assets\assetpack\mirage_gs_deluxe2016_odr\mirage_gs_deluxe2016.assetbundle";
    private const string MIRAGE_PREV_PATH = @"E:\Agent\TFTF-blender\scratch\mirage_clips_preview.assetbundle";
    private const string PROC_BUNDLE_PATH = @"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle";
    private const string RENDERS_DIR = @"E:\Agent\TFTF-blender\renders\dragstrip";

    private const string ROBOT_FBX = "Assets/DragStrip/dragstrip_robot_prepared.fbx";
    private const string VEH_FBX = "Assets/DragStrip/dragstrip_veh_prepared.fbx";
    private const string GUN_R_FBX = "Assets/DragStrip/dragstrip_gun_r_prepared.fbx";
    private const string GUN_L_FBX = "Assets/DragStrip/dragstrip_gun_l_prepared.fbx";

    private const string ROBOT_ASSET = "Assets/DragStrip/cha_mirage_gs_deluxe2016_00.asset";
    private const string VEH_ASSET = "Assets/DragStrip/cha_mirage_gs_deluxe2016_01.asset";
    private const string GUN_R_ASSET = "Assets/DragStrip/cha_mirage_gs_deluxe2016_wpns_blaster_right.asset";
    private const string GUN_L_ASSET = "Assets/DragStrip/cha_mirage_gs_deluxe2016_wpns_blaster_left.asset";
    private const string SCENE_PATH = "Assets/Scenes/DragStrip_Inspection.unity";

    struct AxisSpec {
        public bool zIsHeight;
        public float sx;
        public float sz;
        public float det;
    }

    [MenuItem("TFTF/Build DragStrip vs Mirage Inspection Scene")]
    public static void Build() {
        Debug.Log("=== [DragStrip] Gate 3 Side-by-Side Inspection Scene (Donor: Mirage_GS_Deluxe2016) ===");
        Directory.CreateDirectory(RENDERS_DIR);
        Directory.CreateDirectory(Path.Combine(Application.dataPath, "Scenes"));
        AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);

        foreach (string normP in new[] {
            "Assets/DragStrip/Textures/cha_dragstrip_main_Normal_unity.png",
            "Assets/DragStrip/Textures/cha_dragstrip_wpns_Normal_unity.png",
        }) {
            var normTi = AssetImporter.GetAtPath(normP) as TextureImporter;
            if (normTi != null && normTi.textureType != TextureImporterType.NormalMap) {
                normTi.textureType = TextureImporterType.NormalMap;
                normTi.SaveAndReimport();
            }
        }

        foreach (string fp in new[] { ROBOT_FBX, VEH_FBX, GUN_R_FBX, GUN_L_FBX }) {
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
        AssetBundle mirageBundle = AssetBundle.LoadFromFile(MIRAGE_BUNDLE_PATH);
        if (mirageBundle == null) {
            Debug.LogError("[DragStrip] Missing Mirage bundle: " + MIRAGE_BUNDLE_PATH);
            if (Application.isBatchMode) EditorApplication.Exit(1);
            return;
        }
        AssetBundle miragePrevBundle = File.Exists(MIRAGE_PREV_PATH) ? AssetBundle.LoadFromFile(MIRAGE_PREV_PATH) : null;
        AssetBundle procBundle = File.Exists(PROC_BUNDLE_PATH) ? AssetBundle.LoadFromFile(PROC_BUNDLE_PATH) : null;

        GameObject miragePrefab = null;
        foreach (var g in mirageBundle.LoadAllAssets<GameObject>()) {
            if (g.name.ToLower().Contains("mirage") && !g.name.ToLower().Contains("_lw")) {
                miragePrefab = g; break;
            }
        }
        if (miragePrefab == null) {
            Debug.LogError("[DragStrip] Missing Mirage prefab!");
            if (Application.isBatchMode) EditorApplication.Exit(1);
            return;
        }

        SkinnedMeshRenderer mirSmr00 = null, mirSmr01 = null, mirSmrGunR = null, mirSmrGunL = null;
        foreach (var smr in miragePrefab.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name.EndsWith("_00")) mirSmr00 = smr;
            else if (smr.name.EndsWith("_01")) mirSmr01 = smr;
            else if (smr.name.Contains("blaster_right")) mirSmrGunR = smr;
            else if (smr.name.Contains("blaster_left")) mirSmrGunL = smr;
        }

        Avatar officialAvatar00 = miragePrefab.GetComponent<Animator>() != null ? miragePrefab.GetComponent<Animator>().avatar : null;
        if (officialAvatar00 == null) {
            foreach (var av in mirageBundle.LoadAllAssets<Avatar>()) {
                if (av.name.Contains("_00")) { officialAvatar00 = av; break; }
            }
        }
        Transform prefabTr = FindChildRecursive(miragePrefab.transform, "transformed");
        Avatar officialAvatar01 = (prefabTr != null && prefabTr.GetComponent<Animator>() != null) ? prefabTr.GetComponent<Animator>().avatar : null;
        if (officialAvatar01 == null) {
            foreach (var av in mirageBundle.LoadAllAssets<Avatar>()) {
                if (av.name.Contains("_01")) { officialAvatar01 = av; break; }
            }
        }
        Debug.Log($"[DragStrip] Avatars resolved: av00={(officialAvatar00 != null ? officialAvatar00.name : "NULL")} (isHuman={officialAvatar00?.isHuman}), av01={(officialAvatar01 != null ? officialAvatar01.name : "NULL")}");

        // Build Grafted Meshes
        AxisSpec robotSpec = DetectAxisSpec(ROBOT_FBX);
        Mesh graftedRobot = BuildGraftedMesh(ROBOT_FBX, mirSmr00, robotSpec, "cha_mirage_gs_deluxe2016_00", "Hips", null);
        if (AssetDatabase.LoadAssetAtPath<Mesh>(ROBOT_ASSET) != null) AssetDatabase.DeleteAsset(ROBOT_ASSET);
        AssetDatabase.CreateAsset(graftedRobot, ROBOT_ASSET);

        Mesh rawVehMesh = AssetDatabase.LoadAssetAtPath<GameObject>(VEH_FBX).GetComponentInChildren<SkinnedMeshRenderer>(true).sharedMesh;
        AxisSpec vehSpec = DetectVehAxisSpec(rawVehMesh);
        Mesh graftedVeh = BuildGraftedMesh(VEH_FBX, mirSmr01, vehSpec, "cha_mirage_gs_deluxe2016_01", "COG", "COG");
        if (AssetDatabase.LoadAssetAtPath<Mesh>(VEH_ASSET) != null) AssetDatabase.DeleteAsset(VEH_ASSET);
        AssetDatabase.CreateAsset(graftedVeh, VEH_ASSET);

        AxisSpec gunSpec = new AxisSpec { zIsHeight = true, sx = 1f, sz = -1f, det = -1f }; // Blender (+X muzzle) via Unity useFileScale -> Unity (-X muzzle) matching Mirage blasters!
        Mesh graftedGunR = BuildGraftedMesh(GUN_R_FBX, mirSmrGunR, gunSpec, "cha_mirage_gs_deluxe2016_wpns_blaster_right", "COG", "COG");
        if (AssetDatabase.LoadAssetAtPath<Mesh>(GUN_R_ASSET) != null) AssetDatabase.DeleteAsset(GUN_R_ASSET);
        AssetDatabase.CreateAsset(graftedGunR, GUN_R_ASSET);

        Mesh graftedGunL = BuildGraftedMesh(GUN_L_FBX, mirSmrGunL, gunSpec, "cha_mirage_gs_deluxe2016_wpns_blaster_left", "COG", "COG");
        if (AssetDatabase.LoadAssetAtPath<Mesh>(GUN_L_ASSET) != null) AssetDatabase.DeleteAsset(GUN_L_ASSET);
        AssetDatabase.CreateAsset(graftedGunL, GUN_L_ASSET);

        AssetDatabase.SaveAssets();

        // Create Dragstrip Main & Weapon Standard Materials
        Material matDS = new Material(Shader.Find("Standard"));
        matDS.name = "cha_dragstrip_main";
        matDS.mainTexture = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/DragStrip/Textures/cha_dragstrip_main_Diffuse.png");
        matDS.SetTexture("_BumpMap", AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/DragStrip/Textures/cha_dragstrip_main_Normal_unity.png"));
        matDS.SetTexture("_EmissionMap", AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/DragStrip/Textures/cha_dragstrip_main_Emission.png"));
        matDS.SetColor("_EmissionColor", Color.white);
        matDS.EnableKeyword("_EMISSION");
        matDS.EnableKeyword("_NORMALMAP");
        matDS.SetFloat("_Glossiness", 0.45f);
        matDS.SetFloat("_Metallic", 0.15f);
        if (AssetDatabase.LoadAssetAtPath<Material>("Assets/DragStrip/cha_dragstrip_main.mat") != null)
            AssetDatabase.DeleteAsset("Assets/DragStrip/cha_dragstrip_main.mat");
        AssetDatabase.CreateAsset(matDS, "Assets/DragStrip/cha_dragstrip_main.mat");

        Material matWpn = new Material(Shader.Find("Standard"));
        matWpn.name = "cha_dragstrip_wpns";
        matWpn.mainTexture = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/DragStrip/Textures/cha_dragstrip_wpns_Diffuse.png");
        matWpn.SetTexture("_BumpMap", AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/DragStrip/Textures/cha_dragstrip_wpns_Normal_unity.png"));
        matWpn.EnableKeyword("_NORMALMAP");
        matWpn.SetFloat("_Glossiness", 0.55f);
        matWpn.SetFloat("_Metallic", 0.35f);
        if (AssetDatabase.LoadAssetAtPath<Material>("Assets/DragStrip/cha_dragstrip_wpns.mat") != null)
            AssetDatabase.DeleteAsset("Assets/DragStrip/cha_dragstrip_wpns.mat");
        AssetDatabase.CreateAsset(matWpn, "Assets/DragStrip/cha_dragstrip_wpns.mat");
        AssetDatabase.SaveAssets();

        // Build Side-by-Side Scene
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

        Material matWhite = new Material(Shader.Find("Standard")) { color = new Color(0.88f, 0.88f, 0.88f) };

        GameObject mirInst = UnityEngine.Object.Instantiate(miragePrefab);
        mirInst.name = "Mirage_Official_Reference";
        mirInst.transform.position = new Vector3(3.5f, 0.0f, 0.0f);
        SkinnedMeshRenderer m00 = null, m01 = null, mGR = null, mGL = null;
        foreach (var smr in mirInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name.EndsWith("_00")) { smr.sharedMaterials = new[] { matWhite, matWhite }; smr.updateWhenOffscreen = true; m00 = smr; }
            else if (smr.name.EndsWith("_01")) { smr.sharedMaterials = new[] { matWhite, matWhite, matWhite }; smr.updateWhenOffscreen = true; m01 = smr; }
            else if (smr.name.Contains("blaster_right")) { smr.sharedMaterials = new[] { matWhite }; smr.updateWhenOffscreen = true; mGR = smr; }
            else if (smr.name.Contains("blaster_left")) { smr.sharedMaterials = new[] { matWhite }; smr.updateWhenOffscreen = true; mGL = smr; }
            else smr.enabled = false;
        }

        GameObject dsInst = UnityEngine.Object.Instantiate(miragePrefab);
        dsInst.name = "DragStrip_Candidate";
        dsInst.transform.position = new Vector3(-3.5f, 0.0f, 0.0f);
        SkinnedMeshRenderer d00 = null, d01 = null, dGR = null, dGL = null;
        foreach (var smr in dsInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name.EndsWith("_00")) { smr.sharedMesh = graftedRobot; smr.sharedMaterials = new[] { matDS }; smr.updateWhenOffscreen = true; d00 = smr; }
            else if (smr.name.EndsWith("_01")) { smr.sharedMesh = graftedVeh; smr.sharedMaterials = new[] { matDS }; smr.updateWhenOffscreen = true; d01 = smr; }
            else if (smr.name.Contains("blaster_right")) { smr.sharedMesh = graftedGunR; smr.sharedMaterials = new[] { matWpn }; smr.updateWhenOffscreen = true; dGR = smr; }
            else if (smr.name.Contains("blaster_left")) { smr.sharedMesh = graftedGunL; smr.sharedMaterials = new[] { matWpn }; smr.updateWhenOffscreen = true; dGL = smr; }
            else smr.enabled = false;
        }

        foreach (var t in mirInst.GetComponentsInChildren<Transform>(true)) GameObjectUtility.RemoveMonoBehavioursWithMissingScript(t.gameObject);
        foreach (var t in dsInst.GetComponentsInChildren<Transform>(true)) GameObjectUtility.RemoveMonoBehavioursWithMissingScript(t.gameObject);

        Animator animMir = mirInst.GetComponent<Animator>();
        Animator animDS = dsInst.GetComponent<Animator>();
        if (officialAvatar00 != null) { animMir.avatar = officialAvatar00; animDS.avatar = officialAvatar00; }
        animMir.cullingMode = AnimatorCullingMode.AlwaysAnimate;
        animDS.cullingMode = AnimatorCullingMode.AlwaysAnimate;
        animMir.applyRootMotion = false;
        animDS.applyRootMotion = false;

        Transform trMir = FindChildRecursive(mirInst.transform, "transformed");
        Transform trDS = FindChildRecursive(dsInst.transform, "transformed");
        Animator animTrMir = trMir != null ? (trMir.GetComponent<Animator>() ?? trMir.gameObject.AddComponent<Animator>()) : null;
        Animator animTrDS = trDS != null ? (trDS.GetComponent<Animator>() ?? trDS.gameObject.AddComponent<Animator>()) : null;
        if (officialAvatar01 != null) {
            if (animTrMir != null) { animTrMir.avatar = officialAvatar01; animTrMir.cullingMode = AnimatorCullingMode.AlwaysAnimate; animTrMir.applyRootMotion = false; }
            if (animTrDS != null) { animTrDS.avatar = officialAvatar01; animTrDS.cullingMode = AnimatorCullingMode.AlwaysAnimate; animTrDS.applyRootMotion = false; }
        }

        EditorSceneManager.SaveScene(scene, SCENE_PATH);
        Debug.Log("[✓] Inspection Scene saved to " + SCENE_PATH);

        RenderPoses(mirInst, dsInst, animMir, animDS, animTrMir, animTrDS, m00, m01, mGR, mGL, d00, d01, dGR, dGL, trMir, trDS, procBundle, mirageBundle, miragePrevBundle, cam);
        BuildMeshAssetBundle();

        Debug.Log("[✓] Gate 3 DragStrip Inspection Scene, Renders, and Mesh Bundle complete!");
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

        Bounds tmpB = new Bounds(nv[0], Vector3.zero);
        for (int i = 1; i < nv.Length; i++) tmpB.Encapsulate(nv[i]);
        double outerDot = 0.0;
        for (int i = 0; i < nv.Length; i++) {
            Vector3 d = nv[i] - tmpB.center;
            if (d.sqrMagnitude > 0.25f * tmpB.extents.sqrMagnitude) outerDot += Vector3.Dot(d.normalized, nn[i]);
        }
        if (outerDot < 0.0) for (int i = 0; i < nn.Length; i++) nn[i] = -nn[i];

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
                for (int t = 0; t + 2 < tris.Length; t += 3) { int tmp = tris[t + 1]; tris[t + 1] = tris[t + 2]; tris[t + 2] = tmp; }
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
        GameObject mirInst, GameObject dsInst,
        Animator animMir, Animator animDS, Animator animTrMir, Animator animTrDS,
        SkinnedMeshRenderer m00, SkinnedMeshRenderer m01, SkinnedMeshRenderer mGR, SkinnedMeshRenderer mGL,
        SkinnedMeshRenderer d00, SkinnedMeshRenderer d01, SkinnedMeshRenderer dGR, SkinnedMeshRenderer dGL,
        Transform trMir, Transform trDS,
        AssetBundle procBundle, AssetBundle mirageBundle, AssetBundle miragePrevBundle, Camera cam
    ) {
        Dictionary<string, AnimationClip> clips = new Dictionary<string, AnimationClip>();
        CollectClips(mirageBundle, clips);
        CollectClips(miragePrevBundle, clips);
        CollectClips(procBundle, clips);
        Debug.Log($"[Render] Collected {clips.Count} clips total (has TeamSelect={clips.ContainsKey("TeamSelect_Agile_idle")}, has DualPistol={clips.ContainsKey("dual pistols_attackRanged_gun_01")}, has MirVeh={clips.ContainsKey("frontend_Agile_Mirage_levelup_vehicle_idle_transformed")})");

        var initPos = new Dictionary<Transform, Vector3>();
        var initRot = new Dictionary<Transform, Quaternion>();
        var initScl = new Dictionary<Transform, Vector3>();
        foreach (var t in mirInst.GetComponentsInChildren<Transform>(true)) { initPos[t] = t.localPosition; initRot[t] = t.localRotation; initScl[t] = t.localScale; }
        foreach (var t in dsInst.GetComponentsInChildren<Transform>(true)) { initPos[t] = t.localPosition; initRot[t] = t.localRotation; initScl[t] = t.localScale; }

        void RestoreInit() {
            foreach (var kv in initPos) {
                if (kv.Key != null) { kv.Key.localPosition = kv.Value; kv.Key.localRotation = initRot[kv.Key]; kv.Key.localScale = initScl[kv.Key]; }
            }
            mirInst.transform.SetPositionAndRotation(new Vector3(3.5f, 0f, 0f), Quaternion.identity);
            dsInst.transform.SetPositionAndRotation(new Vector3(-3.5f, 0f, 0f), Quaternion.identity);
        }

        Transform hipsMir = FindChildRecursive(mirInst.transform, "Hips");
        Transform hipsDS = FindChildRecursive(dsInst.transform, "Hips");

        RenderTexture rt = new RenderTexture(1280, 960, 24, RenderTextureFormat.ARGB32) { antiAliasing = 8 };
        cam.targetTexture = rt;

        void RenderShot(string name, string clipName, float t, Vector3 camP, Vector3 look, bool vehMode, bool gunVis) {
            RestoreInit();
            if (trMir != null) trMir.gameObject.SetActive(vehMode);
            if (trDS != null) trDS.gameObject.SetActive(vehMode);
            m00.enabled = !vehMode; m01.gameObject.SetActive(vehMode); m01.enabled = vehMode;
            d00.enabled = !vehMode; d01.gameObject.SetActive(vehMode); d01.enabled = vehMode;
            mGR.enabled = gunVis && !vehMode; mGL.enabled = gunVis && !vehMode;
            dGR.enabled = gunVis && !vehMode; dGL.enabled = gunVis && !vehMode;

            if (!string.IsNullOrEmpty(clipName) && clips.TryGetValue(clipName, out AnimationClip c)) {
                EvalPairGraph(animMir, animDS, c, t);
            } else if (!string.IsNullOrEmpty(clipName)) {
                Debug.LogWarning($"[Shot {name}] Missing clip '{clipName}'");
            }

            if (!vehMode && hipsMir != null && hipsDS != null) {
                Vector3 dM = hipsMir.position - mirInst.transform.position;
                mirInst.transform.position = new Vector3(3.5f - dM.x, 0f, -dM.z);
                Vector3 dD = hipsDS.position - dsInst.transform.position;
                dsInst.transform.position = new Vector3(-3.5f - dD.x, 0f, -dD.z);
            } else if (vehMode && trMir != null && trDS != null) {
                // Keep transformed root horizontal upright (COG at ground origin!)
                trMir.SetPositionAndRotation(new Vector3(3.5f, 0f, 0f), Quaternion.identity);
                trDS.SetPositionAndRotation(new Vector3(-3.5f, 0f, 0f), Quaternion.identity);
            }

            var activeSmrs = new List<SkinnedMeshRenderer>();
            if (vehMode) { activeSmrs.Add(m01); activeSmrs.Add(d01); }
            else { activeSmrs.Add(m00); activeSmrs.Add(d00); if (gunVis) { activeSmrs.Add(mGR); activeSmrs.Add(mGL); activeSmrs.Add(dGR); activeSmrs.Add(dGL); } }

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

        RenderShot("gate3_00_rest_pose.png", null, 0f, new Vector3(0, 5.0f, 16.5f), new Vector3(0, 4.7f, 0), false, false);
        RenderShot("gate3_01_combat_idle.png", "agile_normal_idle", 0.40f, new Vector3(0, 5.0f, 16.5f), new Vector3(0, 4.7f, 0), false, false);
        RenderShot("gate3_01b_frontend_idle.png", "TeamSelect_Agile_idle", 0.50f, new Vector3(0, 5.0f, 16.5f), new Vector3(0, 4.7f, 0), false, false);
        RenderShot("gate3_01c_frontend_torso_closeup.png", "TeamSelect_Agile_idle", 0.50f, new Vector3(-2.4f, 6.1f, 7.6f), new Vector3(-3.5f, 5.5f, 0), false, false);
        RenderShot("gate3_02_head_chest_closeup.png", "agile_normal_idle", 0.40f, new Vector3(-3.5f, 7.6f, 6.2f), new Vector3(-3.5f, 7.2f, 0), false, false);
        RenderShot("gate3_03_back_3q.png", "agile_normal_idle", 0.40f, new Vector3(5.5f, 5.5f, -15.0f), new Vector3(0, 4.7f, 0), false, false);
        RenderShot("gate3_04_jab_punch.png", "agile_normal_attackLight_01_jab_R", 0.30f, new Vector3(0, 5.2f, 16.5f), new Vector3(0, 4.7f, 0), false, false);
        RenderShot("gate3_04b_jab_fist_closeup.png", "agile_normal_attackLight_01_jab_R", 0.30f, new Vector3(-0.8f, 5.8f, 6.8f), new Vector3(-3.2f, 5.3f, 0.2f), false, false);
        RenderShot("gate3_05_ranged_dual_guns.png", "dual pistols_attackRanged_gun_01", 0.35f, new Vector3(0, 5.2f, 16.5f), new Vector3(0, 4.8f, 0), false, true);
        RenderShot("gate3_05b_guns_closeup.png", "dual pistols_attackRanged_gun_01", 0.35f, new Vector3(-0.2f, 6.0f, 7.2f), new Vector3(-3.3f, 5.2f, 0.4f), false, true);
        RenderShot("gate3_07_high_kick.png", "agile_normal_attackLight_04_sidekick_R", 0.35f, new Vector3(0, 5.0f, 16.5f), new Vector3(0, 4.7f, 0), false, false);
        RenderShot("gate3_08_sp1_mirage.png", "Mirage_Normal_attackSpecial_01", 0.45f, new Vector3(0, 5.2f, 17.0f), new Vector3(0, 4.8f, 0), false, false);
        RenderShot("gate3_08b_sp1_open_hand.png", "Mirage_Normal_attackSpecial_01", 0.45f, new Vector3(-3.0f, 5.5f, 7.8f), new Vector3(-6.2f, 4.2f, 0.5f), false, false);
        string vicClip = null;
        foreach (var kv in clips) {
            if (kv.Key.IndexOf("backflip_victory_idle", StringComparison.OrdinalIgnoreCase) >= 0) {
                vicClip = kv.Key; break;
            }
        }
        if (vicClip == null) foreach (var kv in clips) if (kv.Key.IndexOf("agile", StringComparison.OrdinalIgnoreCase) >= 0 && kv.Key.IndexOf("victory", StringComparison.OrdinalIgnoreCase) >= 0 && kv.Key.IndexOf("idle", StringComparison.OrdinalIgnoreCase) >= 0) { vicClip = kv.Key; break; }
        Debug.Log($"[Render] Victory clip resolved: '{vicClip}'");
        if (vicClip != null) {
            RenderShot("gate3_09_victory.png", vicClip, 0.35f, new Vector3(0, 4.2f, 14.5f), new Vector3(0, 2.8f, 0), false, false);
            RenderShot("gate3_09b_victory_hands.png", vicClip, 0.35f, new Vector3(-2.0f, 3.2f, 7.2f), new Vector3(-3.8f, 2.2f, 0.8f), false, false);
        }
        RenderShot("gate3_06_f1_3q.png", null, 0f, new Vector3(6.5f, 6.2f, 12.0f), new Vector3(0f, 1.2f, 0f), true, false);
        RenderShot("gate3_06b_f1_side.png", null, 0f, new Vector3(-11.5f, 3.0f, 2.5f), new Vector3(-3.5f, 1.2f, 0f), true, false);

        RestoreInit();
        m00.enabled = true; m01.gameObject.SetActive(false); mGR.enabled = false; mGL.enabled = false;
        d00.enabled = true; d01.gameObject.SetActive(false); dGR.enabled = false; dGL.enabled = false;
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
        string bundleDir = @"E:\Agent\TFTF-blender\3rd-party-models\DragStrip\04_unity_bundles";
        Directory.CreateDirectory(bundleDir);
        AssetBundleBuild[] builds = new AssetBundleBuild[1];
        builds[0].assetBundleName = "dragstrip_mesh.assetbundle";
        builds[0].assetNames = new[] { ROBOT_ASSET, VEH_ASSET, GUN_R_ASSET, GUN_L_ASSET };
        BuildPipeline.BuildAssetBundles(
            bundleDir,
            builds,
            BuildAssetBundleOptions.ForceRebuildAssetBundle | BuildAssetBundleOptions.ChunkBasedCompression,
            BuildTarget.Android
        );
        Debug.Log("[✓] Built Android Mesh AssetBundle to " + Path.Combine(bundleDir, "dragstrip_mesh.assetbundle"));
    }
}
