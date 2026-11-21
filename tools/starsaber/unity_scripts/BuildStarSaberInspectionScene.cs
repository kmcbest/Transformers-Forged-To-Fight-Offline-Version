using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;
using UnityEngine.SceneManagement;

public static class BuildStarSaberInspectionScene {
    private const string JET_BUNDLE_PATH = @"E:\Agent\TFTF\extracted_apk\assets\assetpack\jetfire_gs_leader2014_odr\jetfire_gs_leader2014.assetbundle";
    private const string PROC_BUNDLE_PATH = @"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle";
    private const string RENDERS_DIR = @"E:\Agent\TFTF-blender\renders\starsaber";

    private const string ROBOT_FBX = "Assets/StarSaber/starsaber_robot_prepared.fbx";
    private const string VEH_FBX = "Assets/StarSaber/starsaber_veh_prepared.fbx";
    private const string ROBOT_ASSET = "Assets/StarSaber/cha_jetfire_gs_leader2014_00.asset";
    private const string VEH_ASSET = "Assets/StarSaber/cha_jetfire_gs_leader2014_01.asset";
    private const string SCENE_PATH = "Assets/Scenes/StarSaber_Inspection.unity";

    struct AxisSpec {
        public bool zIsHeight;
        public float sx;
        public float sz;
        public float det;
    }

    [MenuItem("TFTF/Build StarSaber vs Jetfire Inspection Scene")]
    public static void Build() {
        Debug.Log("=== [StarSaber] Gate 3 Authoritative Side-by-Side Inspection Scene (Donor: Jetfire_GS_Leader2014) ===");
        Directory.CreateDirectory(RENDERS_DIR);
        Directory.CreateDirectory(Path.Combine(Application.dataPath, "StarSaber/Jetfire"));
        Directory.CreateDirectory(Path.Combine(Application.dataPath, "Scenes"));

        AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);

        // 1. Configure Normal Maps & FBX ModelImporters
        string[] normPaths = {
            "Assets/StarSaber/Textures/cha_starsaber_main_Normal_unity.png",
            "Assets/StarSaber/Textures/cha_starsaber_wpns_Normal_unity.png",
            "Assets/StarSaber/Jetfire/main_NM.png",
            "Assets/StarSaber/Jetfire/tform_misc_NM.png",
            "Assets/StarSaber/Jetfire/wpns_NM.png",
        };
        foreach (string np in normPaths) {
            var ti = AssetImporter.GetAtPath(np) as TextureImporter;
            if (ti != null && ti.textureType != TextureImporterType.NormalMap) {
                ti.textureType = TextureImporterType.NormalMap;
                ti.SaveAndReimport();
            }
        }

        foreach (string fp in new[] { ROBOT_FBX, VEH_FBX }) {
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

        // 2. Load Jetfire Donor Bundle
        foreach (var b in AssetBundle.GetAllLoadedAssetBundles()) b.Unload(false);
        AssetBundle jetBundle = AssetBundle.LoadFromFile(JET_BUNDLE_PATH);
        if (jetBundle == null) {
            Debug.LogError("[StarSaber] Missing Jetfire donor bundle: " + JET_BUNDLE_PATH);
            if (Application.isBatchMode) EditorApplication.Exit(1);
            return;
        }
        AssetBundle procBundle = File.Exists(PROC_BUNDLE_PATH) ? AssetBundle.LoadFromFile(PROC_BUNDLE_PATH) : null;

        GameObject jetPrefab = null;
        foreach (var g in jetBundle.LoadAllAssets<GameObject>()) {
            if (g.name.ToLower().Contains("jetfire") && !g.name.ToLower().Contains("_lw")) {
                jetPrefab = g; break;
            }
        }
        if (jetPrefab == null) {
            Debug.LogError("[StarSaber] Missing Jetfire prefab!");
            if (Application.isBatchMode) EditorApplication.Exit(1);
            return;
        }

        SkinnedMeshRenderer jetSmr00 = null, jetSmr01 = null;
        foreach (var smr in jetPrefab.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name.Contains("_00")) jetSmr00 = smr;
            else if (smr.name.Contains("_01")) jetSmr01 = smr;
        }
        if (jetSmr00 == null || jetSmr01 == null) {
            Debug.LogError("[StarSaber] Missing _00 or _01 SMR on Jetfire prefab!");
            if (Application.isBatchMode) EditorApplication.Exit(1);
            return;
        }

        // 3. Detect Axis & Build Grafted Meshes (CRITICAL: preserve HITL-baked 00 robot+sword mesh if already present!)
        Mesh graftedRobot = AssetDatabase.LoadAssetAtPath<Mesh>(ROBOT_ASSET);
        if (graftedRobot != null && graftedRobot.vertexCount >= 15000 && graftedRobot.subMeshCount >= 2) {
            Debug.Log($"[BuildStarSaberInspectionScene] Preserved existing HITL-baked {ROBOT_ASSET} (verts={graftedRobot.vertexCount}, submeshes={graftedRobot.subMeshCount})");
        } else {
            AxisSpec robotSpec = DetectAxisSpec(ROBOT_FBX, jetSmr00);
            graftedRobot = BuildGraftedMesh(ROBOT_FBX, jetSmr00, robotSpec, "cha_jetfire_gs_leader2014_00", "Hips", null);
            if (AssetDatabase.LoadAssetAtPath<Mesh>(ROBOT_ASSET) != null) AssetDatabase.DeleteAsset(ROBOT_ASSET);
            AssetDatabase.CreateAsset(graftedRobot, ROBOT_ASSET);
        }

        AxisSpec vehSpec = new AxisSpec { zIsHeight = false, sx = 1.0f, sz = 1.0f, det = 1.0f };
        Mesh graftedVeh = BuildGraftedMesh(VEH_FBX, jetSmr01, vehSpec, "cha_jetfire_gs_leader2014_01", "chop1_torso_backpack_outer_center", "chop1_torso_backpack_outer_center");
        if (AssetDatabase.LoadAssetAtPath<Mesh>(VEH_ASSET) != null) AssetDatabase.DeleteAsset(VEH_ASSET);
        AssetDatabase.CreateAsset(graftedVeh, VEH_ASSET);
        AssetDatabase.SaveAssets();

        // 4. Create PBR Materials for Star Saber
        Material matBody = new Material(Shader.Find("Standard"));
        matBody.name = "cha_starsaber_main";
        matBody.mainTexture = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/StarSaber/Textures/cha_starsaber_main_Diffuse.png");
        matBody.SetTexture("_BumpMap", AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/StarSaber/Textures/cha_starsaber_main_Normal_unity.png"));
        matBody.SetTexture("_EmissionMap", AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/StarSaber/Textures/cha_starsaber_main_Emission.png"));
        matBody.SetColor("_EmissionColor", Color.white);
        matBody.EnableKeyword("_EMISSION");
        matBody.EnableKeyword("_NORMALMAP");
        matBody.SetFloat("_Glossiness", 0.45f);
        matBody.SetFloat("_Metallic", 0.08f);

        Material matWpn = new Material(Shader.Find("Standard"));
        matWpn.name = "cha_starsaber_wpns";
        matWpn.mainTexture = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/StarSaber/Textures/cha_starsaber_wpns_Diffuse.png");
        matWpn.SetTexture("_BumpMap", AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/StarSaber/Textures/cha_starsaber_wpns_Normal_unity.png"));
        matWpn.SetTexture("_EmissionMap", AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/StarSaber/Textures/cha_starsaber_wpns_Emission.png"));
        matWpn.SetColor("_EmissionColor", Color.white);
        matWpn.EnableKeyword("_EMISSION");
        matWpn.EnableKeyword("_NORMALMAP");
        matWpn.SetFloat("_Glossiness", 0.60f);
        matWpn.SetFloat("_Metallic", 0.35f);

        if (AssetDatabase.LoadAssetAtPath<Material>("Assets/StarSaber/cha_starsaber_main.mat") != null) AssetDatabase.DeleteAsset("Assets/StarSaber/cha_starsaber_main.mat");
        if (AssetDatabase.LoadAssetAtPath<Material>("Assets/StarSaber/cha_starsaber_wpns.mat") != null) AssetDatabase.DeleteAsset("Assets/StarSaber/cha_starsaber_wpns.mat");
        AssetDatabase.CreateAsset(matBody, "Assets/StarSaber/cha_starsaber_main.mat");
        AssetDatabase.CreateAsset(matWpn, "Assets/StarSaber/cha_starsaber_wpns.mat");
        AssetDatabase.SaveAssets();

        // 5. Build Inspection Scene
        Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        // Ground & Lighting
        GameObject lightGo = new GameObject("Directional Light Front");
        Light light = lightGo.AddComponent<Light>();
        light.type = LightType.Directional;
        light.intensity = 1.2f;
        lightGo.transform.rotation = Quaternion.Euler(45.0f, 150.0f, 0.0f);

        GameObject lightBackGo = new GameObject("Directional Light Back");
        Light lightBack = lightBackGo.AddComponent<Light>();
        lightBack.type = LightType.Directional;
        lightBack.intensity = 0.7f;
        lightBackGo.transform.rotation = Quaternion.Euler(35.0f, -30.0f, 0.0f);

        GameObject camGo = new GameObject("Main Camera");
        Camera cam = camGo.AddComponent<Camera>();
        cam.tag = "MainCamera";
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color(0.12f, 0.14f, 0.18f);

        // Instantiate Jetfire (Reference) at X = +3.5
        GameObject jetInst = UnityEngine.Object.Instantiate(jetPrefab);
        jetInst.name = "Jetfire_Official_Reference";
        jetInst.transform.position = new Vector3(3.5f, 0.0f, 0.0f);

        // Fix Jetfire materials for Windows Standalone Editor preview
        Material jetMain = new Material(Shader.Find("Standard"));
        jetMain.mainTexture = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/StarSaber/Jetfire/cha_jetfire_gs_leader2014_main_a.png");
        Material jetWpn = new Material(Shader.Find("Standard"));
        jetWpn.mainTexture = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/StarSaber/Jetfire/cha_jetfire_gs_leader2014_wpns_a.png");

        foreach (var r in jetInst.GetComponentsInChildren<Renderer>(true)) {
            Material[] mats = new Material[r.sharedMaterials.Length];
            for (int i = 0; i < mats.Length; i++) {
                mats[i] = (i == 1) ? jetWpn : jetMain;
            }
            r.sharedMaterials = mats;
        }

        // Instantiate StarSaber (Candidate) at X = -3.5
        GameObject saberInst = UnityEngine.Object.Instantiate(jetPrefab);
        saberInst.name = "StarSaber_Candidate";
        saberInst.transform.position = new Vector3(-3.5f, 0.0f, 0.0f);

        // Replace meshes on Candidate
        foreach (var smr in saberInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name.Contains("_00")) {
                smr.sharedMesh = graftedRobot;
                smr.sharedMaterials = new Material[] { matBody, matWpn };
            } else if (smr.name.Contains("_01")) {
                smr.sharedMesh = graftedVeh;
                smr.sharedMaterials = new Material[] { matBody };
            } else if (smr.name.Contains("wpns") || smr.name.Contains("rifle") || smr.name.Contains("sword")) {
                smr.enabled = false;
            }
        }

        var ctrl = camGo.AddComponent<StarSaberPreviewController>();
        ctrl.animOfficialJetfire = jetInst.GetComponent<Animator>();
        ctrl.animStarSaber = saberInst.GetComponent<Animator>();

        EditorSceneManager.SaveScene(scene, SCENE_PATH);
        Debug.Log("[✓] Inspection Scene built and saved to " + SCENE_PATH);

        // 6. Render 9+ Authoritative Verification PNGs
        RenderInspectionPoses(jetInst, saberInst, procBundle, jetBundle, cam);

        // 7. Build AssetBundle for Stage 4
        BuildMeshAssetBundle();

        Debug.Log("[✓] Gate 3 Scene, Renders, and Mesh Bundle fully built!");
        if (Application.isBatchMode) EditorApplication.Exit(0);
    }

    static AxisSpec DetectAxisSpec(string fbxPath, SkinnedMeshRenderer jetSmr00) {
        GameObject fbx = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
        if (fbx == null) throw new Exception("Missing FBX: " + fbxPath);
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
        Vector3 cRH = CentroidOf("RightForeArm");
        Vector3 cToe = CentroidOf("LeftToeBase");
        if (cToe == Vector3.zero) cToe = CentroidOf("LeftFoot");

        // In Jetfire donor: LeftHand.x < 0 (-2.816)
        float sx = (cLH.x <= 0f) ? 1f : -1f;
        float toeDepth = zIsHeight ? cToe.y : cToe.z;
        float sz = (toeDepth >= 0f) ? 1f : -1f;
        float det = (zIsHeight ? -1f : 1f) * sx * sz;
        Debug.Log($"[AxisSpec] rawBounds={raw.bounds} cLH={cLH} cRH={cRH} cToe={cToe} -> zIsHeight={zIsHeight}, sx={sx}, sz={sz}, det={det}");
        return new AxisSpec { zIsHeight = zIsHeight, sx = sx, sz = sz, det = det };
    }

    static Mesh BuildGraftedMesh(string fbxPath, SkinnedMeshRenderer donorSmr, AxisSpec spec, string meshName, string fallbackBone, string forceSingleBone) {
        GameObject fbx = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
        SkinnedMeshRenderer srcSmr = fbx.GetComponentInChildren<SkinnedMeshRenderer>(true);
        Mesh raw = srcSmr.sharedMesh;

        Vector3[] rv = raw.vertices;
        Vector3[] rn = raw.normals;
        Vector4[] rt = raw.tangents;
        Vector3[] nv = new Vector3[rv.Length];
        Vector3[] nn = new Vector3[rn.Length];
        Vector4[] nt = new Vector4[rt != null ? rt.Length : 0];

        bool useZHeight = spec.zIsHeight;
        float useSx = spec.sx;
        float useSz = spec.sz;

        for (int i = 0; i < rv.Length; i++) {
            Vector3 v = rv[i];
            nv[i] = useZHeight ? new Vector3(useSx * v.x, v.z, useSz * v.y) : new Vector3(useSx * v.x, v.y, useSz * v.z);
        }
        for (int i = 0; i < rn.Length; i++) {
            Vector3 n = rn[i];
            nn[i] = (useZHeight ? new Vector3(useSx * n.x, n.z, useSz * n.y) : new Vector3(useSx * n.x, n.y, useSz * n.z)).normalized;
        }
        if (rt != null) {
            for (int i = 0; i < rt.Length; i++) {
                Vector4 t = rt[i];
                float tw = (spec.det < 0f && forceSingleBone == null) ? -t.w : t.w;
                nt[i] = useZHeight ? new Vector4(useSx * t.x, t.z, useSz * t.y, tw) : new Vector4(useSx * t.x, t.y, useSz * t.z, tw);
            }
        }

        // Outward normal check
        Bounds tmpB = new Bounds(nv[0], Vector3.zero);
        for (int i = 1; i < nv.Length; i++) tmpB.Encapsulate(nv[i]);
        double outerDot = 0.0;
        for (int i = 0; i < nv.Length; i++) {
            Vector3 d = nv[i] - tmpB.center;
            if (d.sqrMagnitude > 0.25f * tmpB.extents.sqrMagnitude) outerDot += Vector3.Dot(d.normalized, nn[i]);
        }
        if (outerDot < 0.0) {
            Debug.LogWarning($"[NormalGuard] {meshName} outerDot={outerDot:F1} < 0! Flipping normals.");
            for (int i = 0; i < nn.Length; i++) nn[i] = -nn[i];
        }

        Transform[] donorBones = donorSmr.bones;
        Dictionary<string, int> donorMap = new Dictionary<string, int>();
        for (int i = 0; i < donorBones.Length; i++) if (donorBones[i] != null) donorMap[donorBones[i].name] = i;
        int fbIdx = donorMap.ContainsKey(fallbackBone) ? donorMap[fallbackBone] : 0;

        int[] remap = new int[srcSmr.bones.Length];
        for (int j = 0; j < srcSmr.bones.Length; j++) {
            string bn = srcSmr.bones[j] != null ? srcSmr.bones[j].name : "";
            if (donorMap.TryGetValue(bn, out int idx)) remap[j] = idx;
            else remap[j] = fbIdx;
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
            int triCount = 0;
            for (int t = 0; t + 2 < tris.Length; t += 3) {
                Vector3 c = Vector3.Cross(nv[tris[t + 1]] - nv[tris[t]], nv[tris[t + 2]] - nv[tris[t]]);
                if (c.sqrMagnitude > 1e-12f) {
                    dotSum += Vector3.Dot(c.normalized, nn[tris[t]]);
                    triCount++;
                }
            }
            if (dotSum < 0.0) {
                for (int t = 0; t + 2 < tris.Length; t += 3) {
                    int tmp = tris[t + 1]; tris[t + 1] = tris[t + 2]; tris[t + 2] = tmp;
                }
            }
            Debug.Log($"[BuildGraftedMesh] {meshName} submesh={s} outerDot={outerDot:F1} flipped={(dotSum < 0.0)} verts={rv.Length}");
            outMesh.SetTriangles(tris, s);
        }
        outMesh.RecalculateBounds();
        Debug.Log($"[BuildGraftedMesh] {meshName} verts={rv.Length} boundsCenter={outMesh.bounds.center:F3} size={outMesh.bounds.size:F3}");
        return outMesh;
    }

    static void RenderInspectionPoses(GameObject jetInst, GameObject saberInst, AssetBundle procBundle, AssetBundle jetBundle, Camera cam) {
        Dictionary<string, AnimationClip> clips = new Dictionary<string, AnimationClip>();
        foreach (var b in new[] { procBundle, jetBundle }) {
            if (b == null) continue;
            foreach (var c in b.LoadAllAssets<AnimationClip>()) {
                if (c != null) clips[c.name] = c;
            }
            foreach (var rac in b.LoadAllAssets<RuntimeAnimatorController>()) {
                if (rac == null) continue;
                foreach (var c in rac.animationClips) {
                    if (c != null && !clips.ContainsKey(c.name)) clips[c.name] = c;
                }
            }
        }
        Debug.Log($"[Render] Loaded {clips.Count} clips total (has veh_idle={clips.ContainsKey("frontend_Jetfire_gs_levelup_vehicle_idle_transformed")}, sp3_veh={clips.ContainsKey("Jetfire_GS_attackSpecial_03_transformed")})");

        RenderTexture rt = new RenderTexture(1280, 960, 24);
        cam.targetTexture = rt;

        var animJet = jetInst.GetComponent<Animator>();
        var animSaber = saberInst.GetComponent<Animator>();

        var poses = new[] {
            new { name = "00_Rest_Pose.png", clip = (string)null, t = 0f, camP = new Vector3(0, 6.0f, 20f), look = new Vector3(0, 5.5f, 0) },
            new { name = "01_Combat_Idle.png", clip = "tactical_normal_idle", t = 0.5f, camP = new Vector3(0, 6.0f, 20f), look = new Vector3(0, 5.5f, 0) },
            new { name = "02_Showroom_45deg.png", clip = "tactical_normal_idle", t = 0.5f, camP = new Vector3(-8f, 6.5f, 16f), look = new Vector3(0, 5.5f, 0) },
            new { name = "03_Back_View.png", clip = "tactical_normal_idle", t = 0.5f, camP = new Vector3(0, 6.0f, -20f), look = new Vector3(0, 5.5f, 0) },
            new { name = "04_Light_Punch.png", clip = "tactical_normal_attacklight_01_jab_L", t = 0.35f, camP = new Vector3(0, 6.0f, 20f), look = new Vector3(0, 5.5f, 0) },
            new { name = "05_Special_Ranged.png", clip = "tactical_normal_attacklight_04_uppercut_R", t = 0.40f, camP = new Vector3(0, 6.0f, 20f), look = new Vector3(0, 5.5f, 0) },
            new { name = "07_High_Kick.png", clip = "tactical_normal_attackMedium_02_kick_R", t = 0.45f, camP = new Vector3(0, 6.0f, 20f), look = new Vector3(0, 5.5f, 0) },
            new { name = "08_Victory_CloseUp.png", clip = "tactical_normal_victory", t = 1.0f, camP = new Vector3(-3.5f, 8.5f, 6.5f), look = new Vector3(-3.5f, 8.0f, 0f) },
            new { name = "09_Left_Hand_Open.png", clip = "tactical_normal_idle", t = 0.0f, camP = new Vector3(-5.25f, 5.0f, 3.0f), look = new Vector3(-5.25f, 5.0f, 0f) },
            new { name = "10_Left_Hand_Curled.png", clip = "tactical_normal_attacklight_01_jab_L", t = 0.35f, camP = new Vector3(-5.25f, 5.0f, 3.0f), look = new Vector3(-5.25f, 5.0f, 0f) },
            new { name = "11_Sword_Grip_CloseUp.png", clip = "tactical_normal_idle", t = 0.5f, camP = new Vector3(-1.4f, 5.2f, 3.2f), look = new Vector3(-1.8f, 4.8f, 0.3f) },
        };

        foreach (var p in poses) {
            jetInst.transform.position = new Vector3(3.5f, 0.0f, 0.0f);
            jetInst.transform.rotation = Quaternion.identity;
            saberInst.transform.position = new Vector3(-3.5f, 0.0f, 0.0f);
            saberInst.transform.rotation = Quaternion.identity;

            cam.transform.position = p.camP;
            cam.transform.LookAt(p.look);

            if (!string.IsNullOrEmpty(p.clip) && clips.TryGetValue(p.clip, out AnimationClip c)) {
                EvalPair(animJet, animSaber, c, p.t);
            }

            cam.Render();
            SaveRenderTexture(rt, Path.Combine(RENDERS_DIR, p.name));
            Debug.Log($"[Render] Output pose: {p.name}");
        }

        jetInst.transform.position = new Vector3(4.8f, 0.0f, 0.0f);
        jetInst.transform.rotation = Quaternion.identity;
        saberInst.transform.position = new Vector3(-4.8f, 0.0f, 0.0f);
        saberInst.transform.rotation = Quaternion.identity;
        SetVehicleMode(jetInst, saberInst, true);

        AnimationClip vehClip = null;
        foreach (string cand in new[] {
            "Jetfire_GS_attackSpecial_03_transformed",
            "frontend_Jetfire_gs_levelup_vehicle_idle_transformed",
            "frontend_Windblade_levelup_vehicle_idle_transformed",
            "frontend_Starscream_levelup_vehicle_idle_transformed",
            "BattleIntro_Jets_windblade_transformed",
            "windblade_Normal_attackHeavy_transformed"
        }) {
            if (clips.TryGetValue(cand, out vehClip)) break;
        }
        if (vehClip != null) {
            EvalPair(animJet, animSaber, vehClip, 0.5f);
            Debug.Log($"[Render] Vehicle clip evaluated: {vehClip.name}");
        }

        // Compute saberInst _01 rendered center so side camera never misses it
        Vector3 vehCenter = new Vector3(0f, 2.0f, 3.0f);
        foreach (var smr in saberInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name.Contains("_01")) {
                vehCenter = smr.bounds.center;
                Debug.Log($"[Render] StarSaber _01 runtime bounds center={vehCenter:F3}, size={smr.bounds.size:F3}");
                break;
            }
        }

        cam.transform.position = new Vector3(0f, vehCenter.y + 24.0f, vehCenter.z);
        cam.transform.LookAt(new Vector3(0f, vehCenter.y, vehCenter.z));
        cam.Render();
        SaveRenderTexture(rt, Path.Combine(RENDERS_DIR, "06_Vehicle_Horizontal.png"));
        Debug.Log("[Render] Output pose: 06_Vehicle_Horizontal.png");

        cam.transform.position = new Vector3(-22.0f, vehCenter.y + 2.5f, vehCenter.z);
        cam.transform.LookAt(new Vector3(0f, vehCenter.y, vehCenter.z));
        cam.Render();
        SaveRenderTexture(rt, Path.Combine(RENDERS_DIR, "06b_Vehicle_Side.png"));
        Debug.Log("[Render] Output pose: 06b_Vehicle_Side.png");
        SetVehicleMode(jetInst, saberInst, false);

        cam.targetTexture = null;
        UnityEngine.Object.DestroyImmediate(rt);
    }

    static void EvalPair(Animator a0, Animator a1, AnimationClip clip, float t) {
        if (clip == null) return;
        var g = PlayableGraph.Create("EvalPair");
        g.SetTimeUpdateMode(DirectorUpdateMode.Manual);
        if (a0 != null) {
            a0.applyRootMotion = false;
            var o0 = AnimationPlayableOutput.Create(g, "Out0", a0);
            var p0 = AnimationClipPlayable.Create(g, clip);
            p0.SetApplyFootIK(false);
            p0.SetTime(t);
            o0.SetSourcePlayable(p0);
        }
        if (a1 != null) {
            a1.applyRootMotion = false;
            var o1 = AnimationPlayableOutput.Create(g, "Out1", a1);
            var p1 = AnimationClipPlayable.Create(g, clip);
            p1.SetApplyFootIK(false);
            p1.SetTime(t);
            o1.SetSourcePlayable(p1);
        }
        g.Play();
        g.Evaluate(0f);
        g.Destroy();
    }

    static void SetVehicleMode(GameObject jetInst, GameObject saberInst, bool isVeh) {
        foreach (var smr in jetInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name.Contains("_00")) smr.enabled = !isVeh;
            else if (smr.name.Contains("_01")) smr.enabled = isVeh;
        }
        foreach (var smr in saberInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name.Contains("_00")) smr.enabled = !isVeh;
            else if (smr.name.Contains("_01")) smr.enabled = isVeh;
        }
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
        string bundleDir = @"E:\Agent\TFTF-blender\3rd-party-models\StarSaber\04_unity_bundles";
        Directory.CreateDirectory(bundleDir);

        AssetBundleBuild[] builds = new AssetBundleBuild[1];
        builds[0].assetBundleName = "starsaber_mesh.assetbundle";
        builds[0].assetNames = new[] { ROBOT_ASSET, VEH_ASSET };

        BuildPipeline.BuildAssetBundles(
            bundleDir,
            builds,
            BuildAssetBundleOptions.ForceRebuildAssetBundle | BuildAssetBundleOptions.ChunkBasedCompression,
            BuildTarget.Android
        );
        Debug.Log("[✓] Built Android Mesh AssetBundle to " + Path.Combine(bundleDir, "starsaber_mesh.assetbundle"));
    }
}
