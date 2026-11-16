using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;
using UnityEngine.SceneManagement;

public static class BuildBrawlInspectionScene {
    private const string MEG_BUNDLE_PATH = @"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle";
    private const string PROC_BUNDLE_PATH = @"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle";
    private const string RENDERS_DIR = @"E:\Agent\TFTF-blender\renders\brawl";

    private const string ROBOT_FBX = "Assets/Brawl/brawl_robot_prepared.fbx";
    private const string TANK_FBX = "Assets/Brawl/brawl_tank_prepared.fbx";
    private const string ROBOT_ASSET = "Assets/Brawl/cha_brawl_gs_00.asset";
    private const string TANK_ASSET = "Assets/Brawl/cha_brawl_gs_01.asset";
    private const string SCENE_PATH = "Assets/Scenes/Brawl_Inspection.unity";

    struct AxisSpec {
        public bool zIsHeight;
        public float sx;
        public float sz;
        public float det;
    }

    [MenuItem("TFTF/Build Brawl vs Megatron Inspection Scene")]
    public static void Build() {
        Debug.Log("=== [Brawl] Gate 3 Authoritative Side-by-Side Inspection Scene (Donor: Megatron_Cin_ROTF) ===");
        Directory.CreateDirectory(RENDERS_DIR);
        Directory.CreateDirectory(Path.Combine(Application.dataPath, "Brawl/Megatron"));
        Directory.CreateDirectory(Path.Combine(Application.dataPath, "Scenes"));

        AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);

        // 1. Configure Normal Maps & FBX ModelImporters
        string[] normPaths = {
            "Assets/Brawl/Textures/cha_brawl_main_Normal_unity.png",
            "Assets/Brawl/Textures/cha_brawl_tform_misc_Normal_unity.png",
            "Assets/Brawl/Megatron/tex_main_NM.png",
            "Assets/Brawl/Megatron/tex_wpns_NM.png",
            "Assets/Brawl/Megatron/tex_tform_misc_NM.png",
        };
        foreach (string np in normPaths) {
            var ti = AssetImporter.GetAtPath(np) as TextureImporter;
            if (ti != null && ti.textureType != TextureImporterType.NormalMap) {
                ti.textureType = TextureImporterType.NormalMap;
                ti.SaveAndReimport();
            }
        }

        foreach (string fp in new[] { ROBOT_FBX, TANK_FBX }) {
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

        // 2. Load Megatron Donor Bundle & Procedural Animations
        foreach (var b in AssetBundle.GetAllLoadedAssetBundles()) b.Unload(false);
        AssetBundle megBundle = AssetBundle.LoadFromFile(MEG_BUNDLE_PATH);
        if (megBundle == null) {
            Debug.LogError("[Brawl] Missing Megatron donor bundle: " + MEG_BUNDLE_PATH);
            if (Application.isBatchMode) EditorApplication.Exit(1);
            return;
        }
        AssetBundle procBundle = File.Exists(PROC_BUNDLE_PATH) ? AssetBundle.LoadFromFile(PROC_BUNDLE_PATH) : null;

        GameObject megPrefab = megBundle.LoadAsset<GameObject>("assets/bundles/characters/merged/megatron_cin_rotf/megatron_cin_rotf.prefab");
        if (megPrefab == null) {
            foreach (var g in megBundle.LoadAllAssets<GameObject>()) {
                if (g.name.ToLower().Contains("megatron_cin_rotf") && !g.name.ToLower().Contains("_lw")) {
                    megPrefab = g; break;
                }
            }
        }
        if (megPrefab == null) {
            Debug.LogError("[Brawl] Missing Megatron prefab!");
            if (Application.isBatchMode) EditorApplication.Exit(1);
            return;
        }

        SkinnedMeshRenderer megSmr00 = null, megSmr01 = null;
        foreach (var smr in megPrefab.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name == "cha_megatron_cin_rotf_00") megSmr00 = smr;
            else if (smr.name == "cha_megatron_cin_rotf_01") megSmr01 = smr;
        }
        if (megSmr00 == null || megSmr01 == null) {
            Debug.LogError("[Brawl] Missing _00 or _01 SMR on Megatron prefab!");
            if (Application.isBatchMode) EditorApplication.Exit(1);
            return;
        }

        Mesh megSaved00 = SaveClonedMesh(megSmr00.sharedMesh, "cha_megatron_official_00", "Assets/Brawl/Megatron/cha_megatron_official_00.asset");
        Mesh megSaved01 = SaveClonedMesh(megSmr01.sharedMesh, "cha_megatron_official_01", "Assets/Brawl/Megatron/cha_megatron_official_01.asset");

        Avatar officialAvatar00 = megPrefab.GetComponent<Animator>() != null ? megPrefab.GetComponent<Animator>().avatar : null;
        Transform prefabTr = FindChildRecursive(megPrefab.transform, "transformed");
        Avatar officialAvatar01 = (prefabTr != null && prefabTr.GetComponent<Animator>() != null) ? prefabTr.GetComponent<Animator>().avatar : null;
        Debug.Log($"[Avatars] avatar00={(officialAvatar00 != null ? officialAvatar00.name + " human=" + officialAvatar00.isHuman : "NULL")} | avatar01={(officialAvatar01 != null ? officialAvatar01.name : "NULL")}");

        // 3. Auto-Calibrate AxisSpec from Robot FBX vs Megatron's 39-Bone Landmarks (No X-Flip Ever!)
        AxisSpec spec = DetectAxisSpec(ROBOT_FBX, megSmr00);
        Mesh graftedRobot = BuildGraftedMesh(ROBOT_FBX, megSmr00, spec, "cha_brawl_gs_00", "Spine1", null);
        SaveOrReplaceMeshAsset(graftedRobot, ROBOT_ASSET);
        Mesh savedRobot00 = AssetDatabase.LoadAssetAtPath<Mesh>(ROBOT_ASSET);

        VerifyLeftFingerJointAlignment(ROBOT_FBX, megSmr00, spec);

        Mesh graftedTank = BuildGraftedMesh(TANK_FBX, megSmr01, spec, "cha_brawl_gs_01", "COG", "COG");
        SaveOrReplaceMeshAsset(graftedTank, TANK_ASSET);
        Mesh savedTank01 = AssetDatabase.LoadAssetAtPath<Mesh>(TANK_ASSET);

        // 4. Create Clean Preview Materials (Brawl uses _Emission.png for eyes/conduits; Megatron uses no false RAOE emission)
        Material matMegMain = CreateOrUpdateMat("Assets/Brawl/Megatron/M_Meg_Main.mat",
            "Assets/Brawl/Megatron/tex_cha_megatron_cin_rotf_main_a.png",
            "Assets/Brawl/Megatron/tex_main_NM.png", null, 0.42f, 0.25f, Vector2.one, Vector2.zero);
        Material matMegMisc = CreateOrUpdateMat("Assets/Brawl/Megatron/M_Meg_Misc.mat",
            "Assets/Brawl/Megatron/tex_tform_misc_A.png",
            "Assets/Brawl/Megatron/tex_tform_misc_NM.png", null, 0.40f, 0.25f, new Vector2(1f, 0.5f), new Vector2(0f, 0.5f));
        Material matMegWpns = CreateOrUpdateMat("Assets/Brawl/Megatron/M_Meg_Wpns.mat",
            "Assets/Brawl/Megatron/tex_cha_megatron_cin_rotf_wpns_a.png",
            "Assets/Brawl/Megatron/tex_wpns_NM.png", null, 0.45f, 0.30f, Vector2.one, Vector2.zero);

        Material matBrawlMain = CreateOrUpdateMat("Assets/Brawl/M_Brawl_Main.mat",
            "Assets/Brawl/Textures/cha_brawl_main_Diffuse.png",
            "Assets/Brawl/Textures/cha_brawl_main_Normal_unity.png",
            "Assets/Brawl/Textures/cha_brawl_main_Emission.png", 0.38f, 0.22f, Vector2.one, Vector2.zero);
        Material matBrawlVh = CreateOrUpdateMat("Assets/Brawl/M_Brawl_Vh.mat",
            "Assets/Brawl/Textures/cha_brawl_tform_misc_Diffuse.png",
            "Assets/Brawl/Textures/cha_brawl_tform_misc_Normal_unity.png",
            "Assets/Brawl/Textures/cha_brawl_tform_misc_Emission.png", 0.40f, 0.24f, Vector2.one, Vector2.zero);

        // 5. Build Clean Side-by-Side Scene
        Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        CreateDirLight("Key Light", new Vector3(26f, -150f, 0f), 1.35f, new Color(1.0f, 0.98f, 0.95f));
        CreateDirLight("Fill Light", new Vector3(16f, 145f, 0f), 0.72f, new Color(0.88f, 0.93f, 1.0f));
        CreateDirLight("Back Rim Light", new Vector3(24f, 12f, 0f), 0.85f, new Color(0.96f, 0.95f, 1.0f));

        GameObject camGo = new GameObject("Main Camera");
        camGo.tag = "MainCamera";
        Camera cam = camGo.AddComponent<Camera>();
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color(0.13f, 0.14f, 0.18f);
        cam.fieldOfView = 42.0f;
        cam.nearClipPlane = 0.1f;
        cam.farClipPlane = 180.0f;
        camGo.transform.position = new Vector3(0f, 6.2f, 20.5f);
        camGo.transform.LookAt(new Vector3(0f, 5.6f, 0f));

        // Left of Screen (+X): Megatron Official Reference at X = +4.4
        GameObject megInst = UnityEngine.Object.Instantiate(megPrefab);
        megInst.name = "Megatron_Official_Reference";
        megInst.transform.SetPositionAndRotation(new Vector3(4.4f, 0f, 0f), Quaternion.identity);
        SkinnedMeshRenderer megActiveSmr00 = null, megActiveSmr01 = null;
        foreach (var smr in megInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name == "cha_megatron_cin_rotf_00") {
                smr.sharedMesh = megSaved00;
                smr.sharedMaterials = new[] { matMegMain, matMegWpns };
                smr.updateWhenOffscreen = true;
                smr.enabled = true;
                megActiveSmr00 = smr;
            } else if (smr.name == "cha_megatron_cin_rotf_01") {
                smr.sharedMesh = megSaved01;
                smr.sharedMaterials = new[] { matMegMisc };
                smr.updateWhenOffscreen = true;
                smr.enabled = false;
                megActiveSmr01 = smr;
            } else {
                smr.enabled = false;
            }
        }

        // Right of Screen (-X): Brawl Candidate at X = -4.4
        GameObject brawlInst = UnityEngine.Object.Instantiate(megPrefab);
        brawlInst.name = "Brawl_Candidate";
        brawlInst.transform.SetPositionAndRotation(new Vector3(-4.4f, 0f, 0f), Quaternion.identity);
        SkinnedMeshRenderer brawlSmr00 = null, brawlSmr01 = null;
        foreach (var smr in brawlInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name == "cha_megatron_cin_rotf_00") {
                smr.gameObject.name = "cha_brawl_gs_00";
                smr.sharedMesh = savedRobot00;
                smr.sharedMaterials = new[] { matBrawlMain };
                smr.updateWhenOffscreen = true;
                smr.enabled = true;
                brawlSmr00 = smr;
            } else if (smr.name == "cha_megatron_cin_rotf_01") {
                smr.gameObject.name = "cha_brawl_gs_01";
                smr.sharedMesh = savedTank01;
                smr.sharedMaterials = new[] { matBrawlVh };
                smr.updateWhenOffscreen = true;
                smr.enabled = false;
                brawlSmr01 = smr;
            } else {
                smr.enabled = false;
                smr.sharedMesh = null;
                smr.gameObject.SetActive(false);
            }
        }

        foreach (var t in megInst.GetComponentsInChildren<Transform>(true)) GameObjectUtility.RemoveMonoBehavioursWithMissingScript(t.gameObject);
        foreach (var t in brawlInst.GetComponentsInChildren<Transform>(true)) GameObjectUtility.RemoveMonoBehavioursWithMissingScript(t.gameObject);

        Animator animMeg = megInst.GetComponent<Animator>();
        Animator animBrawl = brawlInst.GetComponent<Animator>();
        if (officialAvatar00 != null) { animMeg.avatar = officialAvatar00; animBrawl.avatar = officialAvatar00; }
        animMeg.cullingMode = AnimatorCullingMode.AlwaysAnimate;
        animBrawl.cullingMode = AnimatorCullingMode.AlwaysAnimate;
        animMeg.applyRootMotion = false;
        animBrawl.applyRootMotion = false;

        Transform trMeg = FindChildRecursive(megInst.transform, "transformed");
        Transform trBrawl = FindChildRecursive(brawlInst.transform, "transformed");
        Animator animTrMeg = trMeg != null ? (trMeg.GetComponent<Animator>() ?? trMeg.gameObject.AddComponent<Animator>()) : null;
        Animator animTrBrawl = trBrawl != null ? (trBrawl.GetComponent<Animator>() ?? trBrawl.gameObject.AddComponent<Animator>()) : null;
        if (officialAvatar01 != null) {
            if (animTrMeg != null) { animTrMeg.avatar = officialAvatar01; animTrMeg.cullingMode = AnimatorCullingMode.AlwaysAnimate; animTrMeg.applyRootMotion = false; }
            if (animTrBrawl != null) { animTrBrawl.avatar = officialAvatar01; animTrBrawl.cullingMode = AnimatorCullingMode.AlwaysAnimate; animTrBrawl.applyRootMotion = false; }
        }

        var fingerTester = brawlInst.GetComponent<BrawlFingerTester>() ?? brawlInst.AddComponent<BrawlFingerTester>();
        fingerTester.leftHandAxis = BrawlFingerTester.CurlAxis.Forward_Z;
        fingerTester.autoWiggle = false;
        fingerTester.InitializeBones();

        GameObject ctrlGo = new GameObject("BrawlPreviewController");
        var ctrl = ctrlGo.AddComponent<BrawlPreviewController>();
        ctrl.animOfficialMegatron = animMeg;
        ctrl.animBrawl = animBrawl;

        // Collect all clips
        Dictionary<string, AnimationClip> allClips = new Dictionary<string, AnimationClip>();
        CollectClipsFromGo(megPrefab, allClips);
        foreach (var c in megBundle.LoadAllAssets<AnimationClip>()) if (c != null && !allClips.ContainsKey(c.name)) allClips[c.name] = c;
        if (procBundle != null) {
            foreach (string ap in procBundle.GetAllAssetNames()) {
                foreach (var sub in procBundle.LoadAssetWithSubAssets(ap)) {
                    if (sub is AnimationClip ac && !allClips.ContainsKey(ac.name)) allClips[ac.name] = ac;
                }
            }
        }
        Debug.Log($"[ClipAudit] Collected {allClips.Count} AnimationClips.");

        var initPos = new Dictionary<Transform, Vector3>();
        var initRot = new Dictionary<Transform, Quaternion>();
        var initScl = new Dictionary<Transform, Vector3>();
        foreach (var t in megInst.GetComponentsInChildren<Transform>(true)) { initPos[t] = t.localPosition; initRot[t] = t.localRotation; initScl[t] = t.localScale; }
        foreach (var t in brawlInst.GetComponentsInChildren<Transform>(true)) { initPos[t] = t.localPosition; initRot[t] = t.localRotation; initScl[t] = t.localScale; }

        void RestoreInitialPose() {
            foreach (var kv in initPos) {
                if (kv.Key != null) {
                    kv.Key.localPosition = kv.Value;
                    kv.Key.localRotation = initRot[kv.Key];
                    kv.Key.localScale = initScl[kv.Key];
                }
            }
            megInst.transform.SetPositionAndRotation(new Vector3(4.4f, 0f, 0f), Quaternion.identity);
            brawlInst.transform.SetPositionAndRotation(new Vector3(-4.4f, 0f, 0f), Quaternion.identity);
        }

        // 6. Audit Vehicle Mode Clips & Steady Bone (Horizontal Grounded Verification!)
        string chosenVehRoot = null;
        string chosenVehTrans = "frontend_Megatron_levelup_vehicle_idle_transformed";
        float chosenVehT = 0f;
        string bestVehBone = AuditVehicleBonesAndClips(megInst, megActiveSmr01, animMeg, animTrMeg, trMeg, allClips, RestoreInitialPose,
            out chosenVehRoot, out chosenVehTrans, out chosenVehT);
        if (!string.IsNullOrEmpty(bestVehBone) && bestVehBone != "COG") {
            Debug.Log($"[VehRebind] Rebinding cha_brawl_gs_01 cleanly to '{bestVehBone}'!");
            Mesh rebound = BuildGraftedMesh(TANK_FBX, megSmr01, spec, "cha_brawl_gs_01", bestVehBone, bestVehBone);
            SaveOrReplaceMeshAsset(rebound, TANK_ASSET);
            savedTank01 = AssetDatabase.LoadAssetAtPath<Mesh>(TANK_ASSET);
            brawlSmr01.sharedMesh = savedTank01;
        }

        float jabPeakT = FindPeakForwardHandTime(megInst, animMeg, allClips, "brawler_normal_attackLight_01_jab", RestoreInitialPose, 0.35f);
        float heavyT = FindClipFracTime(allClips, "brawler_normal_attackHeavy", 0.40f, 0.45f);
        float kickT = FindClipFracTime(allClips, "brawler_normal_attackLight_04_frontkick", 0.38f, 0.36f);
        float vicT = FindClipFracTime(allClips, "Brawler_Normal_Victory", 0.70f, 1.50f);

        // 7. Render Gate 3 Synchronized Action Screenshots (CPU BakeMesh + PlayableGraph!)
        int w = 1920, h = 1080;
        RenderTexture rt = new RenderTexture(w, h, 24, RenderTextureFormat.ARGB32) { antiAliasing = 8 };
        Texture2D ss = new Texture2D(w, h, TextureFormat.RGB24, false);
        Transform hipsMeg = FindChildRecursive(megInst.transform, "Hips");
        Transform hipsBrawl = FindChildRecursive(brawlInst.transform, "Hips");

        void RenderPoseShot(string clipName, float sampleTime, Vector3 camPos, Vector3 lookTarget, string fileName,
                            bool vehicleMode = false, string transClipName = null, float curlAngle = 0f, bool hideMeg = false) {
            RestoreInitialPose();

            if (trMeg != null) trMeg.gameObject.SetActive(vehicleMode);
            if (trBrawl != null) trBrawl.gameObject.SetActive(vehicleMode);
            megActiveSmr00.enabled = !vehicleMode && !hideMeg;
            megActiveSmr01.gameObject.SetActive(vehicleMode);
            megActiveSmr01.enabled = vehicleMode && !hideMeg;
            brawlSmr00.enabled = !vehicleMode;
            brawlSmr01.gameObject.SetActive(vehicleMode);
            brawlSmr01.enabled = vehicleMode;

            if (clipName != null && allClips.TryGetValue(clipName, out AnimationClip c)) {
                EvalPairGraph(animMeg, animBrawl, c, sampleTime);
            } else if (clipName != null) {
                Debug.LogWarning($"[Shot {fileName}] Missing root clip '{clipName}'");
            }
            if (vehicleMode && transClipName != null && allClips.TryGetValue(transClipName, out AnimationClip tc) && animTrMeg != null && animTrBrawl != null) {
                EvalPairGraph(animTrMeg, animTrBrawl, tc, sampleTime);
            }

            if (Mathf.Abs(curlAngle) > 0.1f) {
                fingerTester.CaptureCurrentAsRest();
                fingerTester.curlAll = curlAngle;
                fingerTester.curlThumb = curlAngle * 0.65f;
                fingerTester.EvaluatePoseNow();
            } else {
                fingerTester.curlAll = 0f;
                fingerTester.curlThumb = 0f;
            }

            float spacing = 4.6f;
            if (!vehicleMode && hipsMeg != null && hipsBrawl != null) {
                Vector3 dM = hipsMeg.position - megInst.transform.position;
                megInst.transform.position = new Vector3(spacing - dM.x, 0f, -dM.z);
                Vector3 dB = hipsBrawl.position - brawlInst.transform.position;
                brawlInst.transform.position = new Vector3(-spacing - dB.x, 0f, -dB.z);
            }

            SkinnedMeshRenderer[] activeSmrs = vehicleMode
                ? (hideMeg ? new[] { brawlSmr01 } : new[] { megActiveSmr01, brawlSmr01 })
                : (hideMeg ? new[] { brawlSmr00 } : new[] { megActiveSmr00, brawlSmr00 });

            List<GameObject> tempGos = new List<GameObject>();
            List<Mesh> tempMeshes = new List<Mesh>();
            for (int idx = 0; idx < activeSmrs.Length; idx++) {
                var smr = activeSmrs[idx];
                if (smr == null) continue;
                Mesh bm = new Mesh();
                smr.BakeMesh(bm, true);
                bm.RecalculateBounds();
                GameObject bgo = new GameObject("TempBaked_" + smr.name);
                bgo.transform.SetPositionAndRotation(smr.transform.position, smr.transform.rotation);
                bgo.transform.localScale = Vector3.one;
                bgo.AddComponent<MeshFilter>().sharedMesh = bm;
                var mr = bgo.AddComponent<MeshRenderer>();
                mr.sharedMaterials = smr.sharedMaterials;
                smr.enabled = false;
                tempGos.Add(bgo);
                tempMeshes.Add(bm);

                if (vehicleMode) {
                    Bounds wb = mr.bounds;
                    float targetX = (!hideMeg && idx == 0) ? spacing : -spacing;
                    bgo.transform.position += new Vector3(targetX - wb.center.x, -wb.min.y, -wb.center.z);
                    Debug.Log($"[BakedVeh {fileName}] {smr.name}: worldSize={wb.size:F2} worldCenter={mr.bounds.center:F2}");
                }
            }

            cam.targetTexture = rt;
            cam.transform.position = camPos;
            cam.transform.LookAt(lookTarget);
            cam.Render();
            RenderTexture.active = rt;
            ss.ReadPixels(new Rect(0, 0, w, h), 0, 0);
            ss.Apply();
            cam.targetTexture = null;
            RenderTexture.active = null;
            File.WriteAllBytes(Path.Combine(RENDERS_DIR, fileName), ss.EncodeToPNG());
            Debug.Log("[✓] Gate 3 screenshot saved: " + fileName);

            foreach (var g in tempGos) UnityEngine.Object.DestroyImmediate(g);
            foreach (var m in tempMeshes) UnityEngine.Object.DestroyImmediate(m);
            fingerTester.ResetAll();
        }

        // 9+ Authoritative Gate 3 Verification Shots + Finger Closeups:
        RenderPoseShot(null, 0f, new Vector3(0f, 6.0f, 21.0f), new Vector3(0f, 5.6f, 0f), "unity_sbs_00_rest_pose.png");
        RenderPoseShot("brawler_normal_idle", 0.35f, new Vector3(0f, 6.0f, 21.0f), new Vector3(0f, 5.6f, 0f), "unity_sbs_01_combat_idle_front.png");
        string selClip = allClips.ContainsKey("TeamSelect_Feral_idle") ? "TeamSelect_Feral_idle" : "frontend_prefight_brawler_idle";
        RenderPoseShot(selClip, 0.50f, new Vector3(6.5f, 6.4f, 20.0f), new Vector3(0f, 5.6f, 0f), "unity_sbs_02_teamselect_idle_34.png");
        RenderPoseShot("brawler_normal_idle", 0.35f, new Vector3(-7.0f, 7.0f, -20.0f), new Vector3(0f, 5.8f, 0f), "unity_sbs_03_back_cannons_view.png");
        RenderPoseShot("brawler_normal_attackLight_01_jab", jabPeakT, new Vector3(-7.5f, 6.2f, 20.5f), new Vector3(0f, 5.6f, 0f), "unity_sbs_04_light_punch_action.png");
        string canonClip = allClips.ContainsKey("brawler_normal_attackHeavy") ? "brawler_normal_attackHeavy" : "brawler_normal_attackSpecial_01";
        RenderPoseShot(canonClip, heavyT, new Vector3(-7.5f, 6.2f, 20.5f), new Vector3(0f, 5.6f, 0f), "unity_sbs_05_heavy_cannon_blast.png");
        RenderPoseShot(chosenVehRoot, chosenVehT, new Vector3(-6.2f, 5.2f, 18.5f), new Vector3(0f, 2.0f, 0f), "unity_sbs_06_vehicle_mode_sbs.png", true, chosenVehTrans);
        RenderPoseShot(chosenVehRoot, chosenVehT, new Vector3(-16.0f, 2.8f, 2.0f), new Vector3(-4.6f, 1.8f, 0f), "unity_sbs_06b_vehicle_side.png", true, chosenVehTrans);
        RenderPoseShot("brawler_normal_attackLight_04_frontkick", kickT, new Vector3(-7.2f, 6.0f, 20.5f), new Vector3(0f, 5.4f, 0f), "unity_sbs_07_high_kick_action.png");
        RenderPoseShot("Brawler_Normal_Victory", vicT, new Vector3(0f, 6.2f, 21.0f), new Vector3(0f, 5.6f, 0f), "unity_sbs_08_victory_pose.png");

        // Left Hand 15-Finger Articulation Micro-Check (Open vs Curled Fist)
        RestoreInitialPose();
        Vector3 lHandPos = FindChildRecursive(brawlInst.transform, "LeftHand").position + new Vector3(0f, -0.55f, 0.05f);
        RenderPoseShot(null, 0f, lHandPos + new Vector3(-2.6f, 0.25f, 2.4f), lHandPos, "unity_10a_left_hand_open.png", false, null, 0f, true);
        RenderPoseShot(null, 0f, lHandPos + new Vector3(-2.6f, 0.25f, 2.4f), lHandPos, "unity_10b_left_hand_curled.png", false, null, 68f, true);

        // Right Hand & Spiked Hammer Grip Close-Up (Brawl's Right arm is at Hips.x - (-LeftHand.x) -> in Unity Hips=-4.6, RightForeArm is -4.6 + 2.47 = -2.13)
        RestoreInitialPose();
        Vector3 rForePos = FindChildRecursive(brawlInst.transform, "RightForeArm").position;
        Vector3 hipsInitPos = hipsBrawl.position;
        Vector3 rWorldFocus = new Vector3(-4.6f + (rForePos.x - hipsInitPos.x), rForePos.y - 1.9f, rForePos.z - hipsInitPos.z + 0.5f);
        RenderPoseShot(null, 0f, rWorldFocus + new Vector3(3.6f, 0.9f, 3.8f), rWorldFocus, "unity_10c_right_hand_hammer.png", false, null, 0f, true);
        RenderPoseShot("brawler_normal_idle", 0.35f, new Vector3(-4.6f + 2.4f, 7.6f, 6.8f), new Vector3(-4.6f + 1.5f, 7.2f, 0.6f), "unity_10d_right_hand_idle_closeup.png", false, null, 0f, true);

        // Restore Clean Scene & Make Scenes[0] = Brawl_Inspection.unity
        RestoreInitialPose();
        if (trMeg != null) trMeg.gameObject.SetActive(false);
        if (trBrawl != null) trBrawl.gameObject.SetActive(false);
        megActiveSmr00.enabled = true; megActiveSmr01.enabled = false;
        brawlSmr00.enabled = true; brawlSmr01.enabled = false;

        cam.targetTexture = null;
        RenderTexture.active = null;
        UnityEngine.Object.DestroyImmediate(rt);
        UnityEngine.Object.DestroyImmediate(ss);
        cam.transform.position = new Vector3(0f, 6.0f, 21.0f);
        cam.transform.LookAt(new Vector3(0f, 5.6f, 0f));

        animMeg.avatar = null;
        animBrawl.avatar = null;
        if (animTrMeg != null) animTrMeg.avatar = null;
        if (animTrBrawl != null) animTrBrawl.avatar = null;

        EditorSceneManager.SaveScene(scene, SCENE_PATH);
        var ebScenes = new List<EditorBuildSettingsScene> { new EditorBuildSettingsScene(SCENE_PATH, true) };
        EditorBuildSettings.scenes = ebScenes.ToArray();
        Debug.Log("[✓] Saved inspection scene & set EditorBuildSettings.scenes[0]: " + SCENE_PATH);

        if (procBundle != null) procBundle.Unload(false);
        megBundle.Unload(false);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();

        // Pack Android Mesh AssetBundle (brawl_mesh.assetbundle)
        string outAbDir = @"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles";
        Directory.CreateDirectory(outAbDir);
        AssetBundleBuild[] builds = new AssetBundleBuild[1];
        builds[0].assetBundleName = "brawl_mesh.assetbundle";
        builds[0].assetNames = new[] { ROBOT_ASSET, TANK_ASSET };
        var manifest = BuildPipeline.BuildAssetBundles(
            outAbDir,
            builds,
            BuildAssetBundleOptions.ForceRebuildAssetBundle | BuildAssetBundleOptions.ChunkBasedCompression,
            BuildTarget.Android
        );
        if (manifest != null) {
            Debug.Log("[✓] Successfully packed brawl_mesh.assetbundle!");
        }

        Debug.Log("=== [Brawl] Gate 3 Complete! All Verification Renders Exported! ===");
        if (Application.isBatchMode) EditorApplication.Exit(0);
    }

    static AxisSpec DetectAxisSpec(string fbxPath, SkinnedMeshRenderer megSmr00) {
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

        // Megatron coords: LeftHand.x < 0 (-2.47), LeftToeBase.z > 0 (+0.56)
        float sx = (cLH.x <= 0f) ? 1f : -1f;
        float toeDepth = zIsHeight ? cToe.y : cToe.z;
        float sz = (toeDepth >= 0f) ? 1f : -1f;
        float det = (zIsHeight ? -1f : 1f) * sx * sz;
        Debug.Log($"[AxisSpec] rawBounds={raw.bounds} cLH={cLH} cRH={cRH} cToe={cToe} -> zIsHeight={zIsHeight}, sx={sx}, sz={sz}, det={det}");
        return new AxisSpec { zIsHeight = zIsHeight, sx = sx, sz = sz, det = det };
    }

    static Mesh BuildGraftedMesh(string fbxPath, SkinnedMeshRenderer megSmr, AxisSpec spec, string meshName, string fallbackBone, string forceSingleBone) {
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
        if (forceSingleBone != null) {
            // For tank FBX: raw Z is height (~3.2m, center.z ~1.6m), raw Y is length (~8.7m, center.y ~0)
            useZHeight = (Mathf.Abs(raw.bounds.center.z) > Mathf.Abs(raw.bounds.center.y)) || (raw.bounds.size.z > raw.bounds.size.y * 1.15f);
        }

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

        Transform[] megBones = megSmr.bones;
        Dictionary<string, int> megMap = new Dictionary<string, int>();
        for (int i = 0; i < megBones.Length; i++) if (megBones[i] != null) megMap[megBones[i].name] = i;
        int fbIdx = megMap.ContainsKey(fallbackBone) ? megMap[fallbackBone] : 0;

        int[] remap = new int[srcSmr.bones.Length];
        int matched = 0;
        for (int j = 0; j < srcSmr.bones.Length; j++) {
            string bn = srcSmr.bones[j] != null ? srcSmr.bones[j].name : "";
            if (megMap.TryGetValue(bn, out int idx)) { remap[j] = idx; matched++; }
            else remap[j] = fbIdx;
        }

        BoneWeight[] origBw = raw.boneWeights;
        BoneWeight[] newBw = new BoneWeight[rv.Length];
        if (!string.IsNullOrEmpty(forceSingleBone) && megMap.TryGetValue(forceSingleBone, out int forcedIdx)) {
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
        outMesh.bindposes = megSmr.sharedMesh.bindposes;

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
            Debug.Log($"[BuildGraftedMesh] {meshName} matched={matched}/{srcSmr.bones.Length} outerDot={outerDot:F1} flipped={(dotSum < 0.0)} verts={rv.Length}");
            outMesh.SetTriangles(tris, s);
        }
        outMesh.RecalculateBounds();
        Debug.Log($"[BuildGraftedMesh] {meshName} boundsCenter={outMesh.bounds.center:F3} size={outMesh.bounds.size:F3}");
        return outMesh;
    }

    static void VerifyLeftFingerJointAlignment(string fbxPath, SkinnedMeshRenderer megSmr00, AxisSpec spec) {
        GameObject fbx = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
        SkinnedMeshRenderer srcSmr = fbx.GetComponentInChildren<SkinnedMeshRenderer>(true);
        Dictionary<string, Transform> fbxBones = new Dictionary<string, Transform>();
        foreach (var b in srcSmr.bones) if (b != null) fbxBones[b.name] = b;

        Transform[] megBones = megSmr00.bones;
        Matrix4x4[] megBps = megSmr00.sharedMesh.bindposes;
        Matrix4x4[] fbxBps = srcSmr.sharedMesh.bindposes;
        Dictionary<string, int> fbxIdxMap = new Dictionary<string, int>();
        for (int j = 0; j < srcSmr.bones.Length; j++) if (srcSmr.bones[j] != null) fbxIdxMap[srcSmr.bones[j].name] = j;

        float maxErrMm = 0f;
        int checkedCount = 0;
        for (int i = 0; i < megBones.Length && i < megBps.Length; i++) {
            string bn = megBones[i].name;
            string bl = bn.ToLower();
            if (!(bl.Contains("thumb") || bl.Contains("index") || bl.Contains("middle") || bl.Contains("ring") || bl.Contains("pinky"))) continue;
            if (!fbxIdxMap.TryGetValue(bn, out int fi) || fi >= fbxBps.Length) continue;
            Vector3 fp = fbxBps[fi].inverse.MultiplyPoint3x4(Vector3.zero);
            Vector3 fUnity = spec.zIsHeight ? new Vector3(spec.sx * fp.x, fp.z, spec.sz * fp.y) : new Vector3(spec.sx * fp.x, fp.y, spec.sz * fp.z);
            Vector3 megPos = megBps[i].inverse.MultiplyPoint3x4(Vector3.zero);
            float errMm = Vector3.Distance(fUnity, megPos) * 1000f;
            if (errMm > maxErrMm) maxErrMm = errMm;
            checkedCount++;
        }
        Debug.Log($"[FingerAudit] Checked {checkedCount}/15 Left finger bones against Megatron BindPose: maxPosDelta={maxErrMm:F3} mm");
    }

    static string AuditVehicleBonesAndClips(
            GameObject megInst, SkinnedMeshRenderer megSmr01, Animator animMeg, Animator animTrMeg, Transform trMeg,
            Dictionary<string, AnimationClip> allClips, Action restoreFn,
            out string chosenVehRoot, out string chosenVehTrans, out float chosenVehT) {
        string[] candClips = {
            "frontend_Megatron_levelup_vehicle_idle_transformed",
            "BattleIntro_Trucks_megatron_transformed",
            "megatron_cin_attackSpecial_03_transformed",
            "megatron_cin_attackSpecial_03_transformed",
            "megatron_cin_attackSpecial_03_transformed",
            "megatron_cin_attackSpecial_03_transformed",
        };
        string[] rootPairs = {
            null,
            "BattleIntro_Trucks",
            null,
            null,
            null,
            null,
        };
        float[] sampleTimes = { 0.30f, 0.50f, 1.00f, 2.00f, 3.00f, 4.00f };

        string[] candBones = { "COG" };
        Transform[] bones01 = megSmr01.bones;
        Matrix4x4[] bps01 = megSmr01.sharedMesh.bindposes;
        Dictionary<string, int> bIdxMap = new Dictionary<string, int>();
        for (int i = 0; i < bones01.Length; i++) if (bones01[i] != null) bIdxMap[bones01[i].name] = i;

        chosenVehRoot = null;
        chosenVehTrans = "frontend_Megatron_levelup_vehicle_idle_transformed";
        chosenVehT = 0.30f;
        string bestBone = "COG";
        float bestScore = -999f;

        if (trMeg != null) trMeg.gameObject.SetActive(true);
        megSmr01.enabled = true;

        for (int ci = 0; ci < candClips.Length; ci++) {
            string tClip = candClips[ci];
            string rClip = rootPairs[ci];
            if (!allClips.TryGetValue(tClip, out AnimationClip tc)) continue;
            float t = Mathf.Min(sampleTimes[ci], Mathf.Max(0f, tc.length * 0.5f));
            restoreFn();
            if (rClip != null && allClips.TryGetValue(rClip, out AnimationClip rc)) EvalSingleGraph(animMeg, rc, t);
            if (animTrMeg != null) EvalSingleGraph(animTrMeg, tc, t);

            Mesh bm = new Mesh();
            megSmr01.BakeMesh(bm, true);
            GameObject tgo = new GameObject("TempMegVehAudit");
            tgo.transform.SetPositionAndRotation(megSmr01.transform.position, megSmr01.transform.rotation);
            tgo.AddComponent<MeshFilter>().sharedMesh = bm;
            var mr = tgo.AddComponent<MeshRenderer>();
            Bounds wb = mr.bounds;
            Debug.Log($"[VehClipAudit] clip='{tClip}' (t={t:F2}s) Meg01 worldSize={wb.size:F2}");
            UnityEngine.Object.DestroyImmediate(tgo);
            UnityEngine.Object.DestroyImmediate(bm);

            foreach (string bn in candBones) {
                Transform trNode = bIdxMap.TryGetValue(bn, out int bi) ? bones01[bi] : FindChildRecursive(megInst.transform, bn);
                if (trNode == null) continue;
                Matrix4x4 mRel = megInst.transform.worldToLocalMatrix * trNode.localToWorldMatrix * (bIdxMap.ContainsKey(bn) ? bps01[bi] : Matrix4x4.identity);
                Vector3 up = mRel.MultiplyVector(Vector3.up);
                Vector3 fwd = mRel.MultiplyVector(Vector3.forward);
                Vector3 scl = new Vector3(mRel.GetColumn(0).magnitude, mRel.GetColumn(1).magnitude, mRel.GetColumn(2).magnitude);
                float score = up.y + fwd.z - Mathf.Abs(scl.x - 1f) - Mathf.Abs(scl.y - 1f) - Mathf.Abs(scl.z - 1f);
                Debug.Log($"   [VehBoneAudit] {bn,-24} up={up:F2} fwd={fwd:F2} scl={scl:F2} score={score:F2}");
                if (wb.size.z > wb.size.y * 1.1f && up.y > 0.85f && score > bestScore) {
                    bestScore = score;
                    bestBone = bn;
                    chosenVehRoot = rClip;
                    chosenVehTrans = tClip;
                    chosenVehT = t;
                }
            }
        }
        restoreFn();
        Debug.Log($"[VehBoneWinner] clip='{chosenVehTrans}' t={chosenVehT:F2}s bestBone='{bestBone}' score={bestScore:F2}");
        return bestBone;
    }

    static float FindPeakForwardHandTime(GameObject inst, Animator anim, Dictionary<string, AnimationClip> clips, string clipName, Action restoreFn, float fallbackT) {
        if (!clips.TryGetValue(clipName, out AnimationClip c)) return fallbackT;
        Transform hips = FindChildRecursive(inst.transform, "Hips");
        Transform rh = FindChildRecursive(inst.transform, "RightForeArm");
        Transform lh = FindChildRecursive(inst.transform, "LeftHand");
        if (hips == null || rh == null || lh == null) return fallbackT;
        float bestZ = -999f, bestT = fallbackT;
        float dur = Mathf.Max(0.2f, c.length);
        for (float t = 0.05f; t <= dur; t += 0.05f) {
            restoreFn();
            EvalSingleGraph(anim, c, t);
            float dz = Mathf.Max(rh.position.z - hips.position.z, lh.position.z - hips.position.z);
            if (dz > bestZ) { bestZ = dz; bestT = t; }
        }
        restoreFn();
        Debug.Log($"[PeakPose] '{clipName}' -> bestT={bestT:F2}s (dz={bestZ:F2})");
        return bestT;
    }

    static float FindClipFracTime(Dictionary<string, AnimationClip> clips, string clipName, float frac, float fallbackT) {
        if (clips.TryGetValue(clipName, out AnimationClip c) && c.length > 0.05f) return c.length * frac;
        return fallbackT;
    }

    static void EvalSingleGraph(Animator anim, AnimationClip clip, float t) {
        if (anim == null || clip == null) return;
        var g = PlayableGraph.Create("EvalSingle");
        g.SetTimeUpdateMode(DirectorUpdateMode.Manual);
        var o = AnimationPlayableOutput.Create(g, "Out", anim);
        var p = AnimationClipPlayable.Create(g, clip);
        p.SetApplyFootIK(false); p.SetTime(t);
        o.SetSourcePlayable(p);
        g.Play(); g.Evaluate(0f); g.Destroy();
    }

    static void EvalPairGraph(Animator a0, Animator a1, AnimationClip clip, float t) {
        var g = PlayableGraph.Create("EvalPair");
        g.SetTimeUpdateMode(DirectorUpdateMode.Manual);
        if (a0 != null) {
            var o0 = AnimationPlayableOutput.Create(g, "Out0", a0);
            var p0 = AnimationClipPlayable.Create(g, clip);
            p0.SetApplyFootIK(false); p0.SetTime(t);
            o0.SetSourcePlayable(p0);
        }
        if (a1 != null) {
            var o1 = AnimationPlayableOutput.Create(g, "Out1", a1);
            var p1 = AnimationClipPlayable.Create(g, clip);
            p1.SetApplyFootIK(false); p1.SetTime(t);
            o1.SetSourcePlayable(p1);
        }
        g.Play(); g.Evaluate(0f); g.Destroy();
    }

    static void CollectClipsFromGo(GameObject go, Dictionary<string, AnimationClip> map) {
        if (go == null) return;
        foreach (var anim in go.GetComponentsInChildren<Animator>(true)) {
            if (anim.runtimeAnimatorController != null) {
                foreach (var c in anim.runtimeAnimatorController.animationClips) {
                    if (c != null && !map.ContainsKey(c.name)) map[c.name] = c;
                }
            }
        }
    }

    static Mesh SaveClonedMesh(Mesh src, string name, string assetPath) {
        Mesh m = UnityEngine.Object.Instantiate(src);
        m.name = name;
        SaveOrReplaceMeshAsset(m, assetPath);
        return AssetDatabase.LoadAssetAtPath<Mesh>(assetPath);
    }

    static void SaveOrReplaceMeshAsset(Mesh built, string assetPath) {
        Mesh existing = AssetDatabase.LoadAssetAtPath<Mesh>(assetPath);
        if (existing != null) {
            existing.Clear(false);
            if (built.vertexCount > 65535) existing.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;
            existing.name = built.name;
            existing.vertices = built.vertices;
            existing.normals = built.normals;
            existing.tangents = built.tangents;
            existing.uv = built.uv;
            existing.boneWeights = built.boneWeights;
            existing.bindposes = built.bindposes;
            existing.subMeshCount = built.subMeshCount;
            for (int s = 0; s < built.subMeshCount; s++) existing.SetTriangles(built.GetTriangles(s), s);
            existing.RecalculateBounds();
            EditorUtility.SetDirty(existing);
        } else {
            AssetDatabase.CreateAsset(built, assetPath);
        }
    }

    static Material CreateOrUpdateMat(string matPath, string diffPath, string normPath, string emPath,
            float gloss, float metallic, Vector2 scale, Vector2 offset) {
        Material m = AssetDatabase.LoadAssetAtPath<Material>(matPath);
        if (m == null) {
            m = new Material(Shader.Find("Standard"));
            m.name = Path.GetFileNameWithoutExtension(matPath);
            AssetDatabase.CreateAsset(m, matPath);
        }
        m.shader = Shader.Find("Standard");
        m.SetFloat("_Mode", 0f);
        m.SetInt("_ZWrite", 1);
        m.SetFloat("_Glossiness", gloss);
        m.SetFloat("_Metallic", metallic);
        Texture2D td = AssetDatabase.LoadAssetAtPath<Texture2D>(diffPath);
        if (td != null) {
            m.mainTexture = td;
            m.mainTextureScale = scale;
            m.mainTextureOffset = offset;
        }
        if (!string.IsNullOrEmpty(normPath)) {
            Texture2D tn = AssetDatabase.LoadAssetAtPath<Texture2D>(normPath);
            if (tn != null) {
                m.EnableKeyword("_NORMALMAP");
                m.SetTexture("_BumpMap", tn);
                m.SetTextureScale("_BumpMap", scale);
                m.SetTextureOffset("_BumpMap", offset);
            }
        }
        if (!string.IsNullOrEmpty(emPath)) {
            Texture2D te = AssetDatabase.LoadAssetAtPath<Texture2D>(emPath);
            if (te != null) {
                m.EnableKeyword("_EMISSION");
                m.SetTexture("_EmissionMap", te);
                m.SetColor("_EmissionColor", Color.white * 1.25f);
            }
        } else {
            m.DisableKeyword("_EMISSION");
            m.SetColor("_EmissionColor", Color.black);
        }
        EditorUtility.SetDirty(m);
        return m;
    }

    static void CreateDirLight(string name, Vector3 euler, float intensity, Color col) {
        GameObject go = new GameObject(name);
        Light l = go.AddComponent<Light>();
        l.type = LightType.Directional;
        l.intensity = intensity;
        l.color = col;
        go.transform.rotation = Quaternion.Euler(euler);
    }

    static Transform FindChildRecursive(Transform parent, string name) {
        if (parent == null) return null;
        if (parent.name == name) return parent;
        for (int i = 0; i < parent.childCount; i++) {
            var f = FindChildRecursive(parent.GetChild(i), name);
            if (f != null) return f;
        }
        return null;
    }
}
