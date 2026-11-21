using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;
using UnityEngine.SceneManagement;

public static class BuildSideswipeInspectionScene {
    private const string BARR_BUNDLE_PATH = @"E:\Agent\TFTF\extracted_apk\assets\assetpack\barricade_cin_dotm_odr\barricade_cin_dotm.assetbundle";
    private const string PROC_BUNDLE_PATH = @"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle";
    private const string RENDERS_DIR = @"E:\Agent\TFTF-blender\renders\sideswipe";

    private const string ROBOT_FBX = "Assets/Sideswipe/sideswipe_robot_prepared.fbx";
    private const string VH_FBX = "Assets/Sideswipe/sideswipe_vh_prepared.fbx";
    private const string ROBOT_ASSET = "Assets/Sideswipe/cha_sideswipe_cin_rotf_00.asset";
    private const string VH_ASSET = "Assets/Sideswipe/cha_sideswipe_cin_rotf_01.asset";
    private const string SCENE_PATH = "Assets/Scenes/Sideswipe_Inspection.unity";

    struct AxisSpec {
        public bool zIsHeight;
        public float sx;
        public float sz;
        public float det;
    }

    [MenuItem("TFTF/Build Sideswipe vs Barricade Inspection Scene")]
    public static void Build() {
        Debug.Log("=== [Sideswipe] Gate 3 Authoritative Side-by-Side Inspection Scene (Donor: Barricade_Cin_DOTM) ===");
        Directory.CreateDirectory(RENDERS_DIR);
        Directory.CreateDirectory(Path.Combine(Application.dataPath, "Sideswipe/Barricade"));
        Directory.CreateDirectory(Path.Combine(Application.dataPath, "Scenes"));

        AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);

        // 1. Configure Normal Maps & FBX ModelImporters
        string[] normPaths = {
            "Assets/Sideswipe/Textures/cha_sideswipe_main_Normal_unity.png",
            "Assets/Sideswipe/Textures/cha_sideswipe_tform_misc_Normal_unity.png",
            "Assets/Sideswipe/Barricade/tex_main_NM.png",
            "Assets/Sideswipe/Barricade/tex_wpns_NM.png",
            "Assets/Sideswipe/Barricade/tex_tform_misc_NM.png",
        };
        foreach (string np in normPaths) {
            var ti = AssetImporter.GetAtPath(np) as TextureImporter;
            if (ti != null && ti.textureType != TextureImporterType.NormalMap) {
                ti.textureType = TextureImporterType.NormalMap;
                ti.SaveAndReimport();
            }
        }

        foreach (string fp in new[] { ROBOT_FBX, VH_FBX }) {
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

        // 2. Load Barricade Donor Bundle & Procedural Animations
        foreach (var b in AssetBundle.GetAllLoadedAssetBundles()) b.Unload(false);
        AssetBundle barrBundle = AssetBundle.LoadFromFile(BARR_BUNDLE_PATH);
        if (barrBundle == null) {
            Debug.LogError("[Sideswipe] Missing Barricade donor bundle: " + BARR_BUNDLE_PATH);
            if (Application.isBatchMode) EditorApplication.Exit(1);
            return;
        }
        AssetBundle procBundle = File.Exists(PROC_BUNDLE_PATH) ? AssetBundle.LoadFromFile(PROC_BUNDLE_PATH) : null;

        GameObject barrPrefab = barrBundle.LoadAsset<GameObject>("assets/bundles/characters/merged/barricade_cin_dotm/barricade_cin_dotm.prefab");
        if (barrPrefab == null) {
            foreach (var g in barrBundle.LoadAllAssets<GameObject>()) {
                if (g.name.ToLower().Contains("barricade_cin_dotm") && !g.name.ToLower().Contains("_lw")) {
                    barrPrefab = g; break;
                }
            }
        }
        if (barrPrefab == null) {
            Debug.LogError("[Sideswipe] Missing Barricade prefab!");
            if (Application.isBatchMode) EditorApplication.Exit(1);
            return;
        }

        SkinnedMeshRenderer barrSmr00 = null, barrSmr01 = null;
        foreach (var smr in barrPrefab.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name == "cha_barricade_cin_dotm_00") barrSmr00 = smr;
            else if (smr.name == "cha_barricade_cin_dotm_01") barrSmr01 = smr;
        }
        if (barrSmr00 == null || barrSmr01 == null) {
            Debug.LogError("[Sideswipe] Missing _00 or _01 SMR on Barricade prefab!");
            if (Application.isBatchMode) EditorApplication.Exit(1);
            return;
        }

        Mesh barrSaved00 = SaveClonedMesh(barrSmr00.sharedMesh, "cha_barricade_official_00", "Assets/Sideswipe/Barricade/cha_barricade_official_00.asset");
        Mesh barrSaved01 = SaveClonedMesh(barrSmr01.sharedMesh, "cha_barricade_official_01", "Assets/Sideswipe/Barricade/cha_barricade_official_01.asset");

        Avatar officialAvatar00 = barrPrefab.GetComponent<Animator>() != null ? barrPrefab.GetComponent<Animator>().avatar : null;
        Transform prefabTr = FindChildRecursive(barrPrefab.transform, "transformed");
        Avatar officialAvatar01 = (prefabTr != null && prefabTr.GetComponent<Animator>() != null) ? prefabTr.GetComponent<Animator>().avatar : null;
        Debug.Log($"[Avatars] avatar00={(officialAvatar00 != null ? officialAvatar00.name + " human=" + officialAvatar00.isHuman : "NULL")} | avatar01={(officialAvatar01 != null ? officialAvatar01.name : "NULL")}");

        // 3. Auto-Calibrate AxisSpec from Robot FBX vs Barricade's 77-Bone Landmarks (No X-Flip Ever!)
        AxisSpec spec = DetectAxisSpec(ROBOT_FBX, barrSmr00);
        Mesh graftedRobot = BuildGraftedMesh(ROBOT_FBX, barrSmr00, spec, "cha_sideswipe_cin_rotf_00", "Spine1", null);
        SaveOrReplaceMeshAsset(graftedRobot, ROBOT_ASSET);
        Mesh savedRobot00 = AssetDatabase.LoadAssetAtPath<Mesh>(ROBOT_ASSET);

        VerifyLeftFingerJointAlignment(ROBOT_FBX, barrSmr00, spec);

        Mesh graftedVh = BuildGraftedMesh(VH_FBX, barrSmr01, spec, "cha_sideswipe_cin_rotf_01", "BodyBase", "BodyBase");
        SaveOrReplaceMeshAsset(graftedVh, VH_ASSET);
        Mesh savedVh01 = AssetDatabase.LoadAssetAtPath<Mesh>(VH_ASSET);

        // 4. Create Clean Preview Materials
        Material matBarrMain = CreateOrUpdateMat("Assets/Sideswipe/Barricade/M_Barr_Main.mat",
            "Assets/Sideswipe/Barricade/tex_cha_barricade_cin_dotm_main_a.png",
            "Assets/Sideswipe/Barricade/tex_main_NM.png", null, 0.45f, 0.25f, Vector2.one, Vector2.zero);
        Material matBarrMisc = CreateOrUpdateMat("Assets/Sideswipe/Barricade/M_Barr_Misc.mat",
            "Assets/Sideswipe/Barricade/tex_tform_misc_A.png",
            "Assets/Sideswipe/Barricade/tex_tform_misc_NM.png", null, 0.40f, 0.25f, Vector2.one, Vector2.zero);
        Material matBarrWpns = CreateOrUpdateMat("Assets/Sideswipe/Barricade/M_Barr_Wpns.mat",
            "Assets/Sideswipe/Barricade/tex_cha_barricade_cin_dotm_wpns_a.png",
            "Assets/Sideswipe/Barricade/tex_wpns_NM.png", null, 0.45f, 0.30f, Vector2.one, Vector2.zero);

        Material matSideswipeMain = CreateOrUpdateMat("Assets/Sideswipe/M_Sideswipe_Main.mat",
            "Assets/Sideswipe/Textures/cha_sideswipe_main_Diffuse.png",
            "Assets/Sideswipe/Textures/cha_sideswipe_main_Normal_unity.png",
            "Assets/Sideswipe/Textures/cha_sideswipe_main_Emission.png", 0.55f, 0.35f, Vector2.one, Vector2.zero);
        Material matSideswipeVh = CreateOrUpdateMat("Assets/Sideswipe/M_Sideswipe_Vh.mat",
            "Assets/Sideswipe/Textures/cha_sideswipe_tform_misc_Diffuse.png",
            "Assets/Sideswipe/Textures/cha_sideswipe_tform_misc_Normal_unity.png",
            "Assets/Sideswipe/Textures/cha_sideswipe_tform_misc_Emission.png", 0.58f, 0.38f, Vector2.one, Vector2.zero);

        // 5. Build Clean Side-by-Side Scene
        Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        CreateDirLight("Key Light", new Vector3(26f, -150f, 0f), 1.35f, new Color(1.0f, 0.98f, 0.95f));
        CreateDirLight("Fill Light", new Vector3(16f, 145f, 0f), 0.75f, new Color(0.88f, 0.93f, 1.0f));
        CreateDirLight("Back Rim Light", new Vector3(24f, 12f, 0f), 0.85f, new Color(0.96f, 0.95f, 1.0f));

        GameObject camGo = new GameObject("Main Camera");
        camGo.tag = "MainCamera";
        Camera cam = camGo.AddComponent<Camera>();
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color(0.12f, 0.13f, 0.16f);
        cam.fieldOfView = 42.0f;
        cam.nearClipPlane = 0.1f;
        cam.farClipPlane = 180.0f;
        camGo.transform.position = new Vector3(0f, 5.8f, 21.0f);
        camGo.transform.LookAt(new Vector3(0f, 5.4f, 0f));

        // Left of Screen (+X): Barricade Official Reference at X = +4.2
        GameObject barrInst = UnityEngine.Object.Instantiate(barrPrefab);
        barrInst.name = "Barricade_Official_Reference";
        barrInst.transform.SetPositionAndRotation(new Vector3(4.2f, 0f, 0f), Quaternion.identity);
        SkinnedMeshRenderer barrActiveSmr00 = null, barrActiveSmr01 = null;
        foreach (var smr in barrInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name == "cha_barricade_cin_dotm_00") {
                smr.sharedMesh = barrSaved00;
                smr.sharedMaterials = new[] { matBarrMain, matBarrWpns };
                smr.updateWhenOffscreen = true;
                smr.enabled = true;
                barrActiveSmr00 = smr;
            } else if (smr.name == "cha_barricade_cin_dotm_01") {
                smr.sharedMesh = barrSaved01;
                smr.sharedMaterials = new[] { matBarrMisc, matBarrMain, matBarrWpns };
                smr.updateWhenOffscreen = true;
                smr.enabled = false;
                barrActiveSmr01 = smr;
            } else {
                smr.enabled = false;
            }
        }

        // Right of Screen (-X): Sideswipe Candidate at X = -4.2
        GameObject sideswipeInst = UnityEngine.Object.Instantiate(barrPrefab);
        sideswipeInst.name = "Sideswipe_Candidate";
        sideswipeInst.transform.SetPositionAndRotation(new Vector3(-4.2f, 0f, 0f), Quaternion.identity);
        SkinnedMeshRenderer sideswipeSmr00 = null, sideswipeSmr01 = null;
        foreach (var smr in sideswipeInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name == "cha_barricade_cin_dotm_00") {
                smr.gameObject.name = "cha_sideswipe_cin_rotf_00";
                smr.sharedMesh = savedRobot00;
                smr.sharedMaterials = new[] { matSideswipeMain };
                smr.updateWhenOffscreen = true;
                smr.enabled = true;
                sideswipeSmr00 = smr;
            } else if (smr.name == "cha_barricade_cin_dotm_01") {
                smr.gameObject.name = "cha_sideswipe_cin_rotf_01";
                smr.sharedMesh = savedVh01;
                smr.sharedMaterials = new[] { matSideswipeVh };
                smr.updateWhenOffscreen = true;
                smr.enabled = false;
                sideswipeSmr01 = smr;
            } else {
                smr.enabled = false;
                smr.sharedMesh = null;
                smr.gameObject.SetActive(false);
            }
        }

        foreach (var t in barrInst.GetComponentsInChildren<Transform>(true)) GameObjectUtility.RemoveMonoBehavioursWithMissingScript(t.gameObject);
        foreach (var t in sideswipeInst.GetComponentsInChildren<Transform>(true)) GameObjectUtility.RemoveMonoBehavioursWithMissingScript(t.gameObject);

        Animator animBarr = barrInst.GetComponent<Animator>();
        Animator animSideswipe = sideswipeInst.GetComponent<Animator>();
        if (officialAvatar00 != null) { animBarr.avatar = officialAvatar00; animSideswipe.avatar = officialAvatar00; }
        animBarr.cullingMode = AnimatorCullingMode.AlwaysAnimate;
        animSideswipe.cullingMode = AnimatorCullingMode.AlwaysAnimate;
        animBarr.applyRootMotion = false;
        animSideswipe.applyRootMotion = false;

        Transform trBarr = FindChildRecursive(barrInst.transform, "transformed");
        Transform trSideswipe = FindChildRecursive(sideswipeInst.transform, "transformed");
        Animator animTrBarr = trBarr != null ? (trBarr.GetComponent<Animator>() ?? trBarr.gameObject.AddComponent<Animator>()) : null;
        Animator animTrSideswipe = trSideswipe != null ? (trSideswipe.GetComponent<Animator>() ?? trSideswipe.gameObject.AddComponent<Animator>()) : null;
        if (officialAvatar01 != null) {
            if (animTrBarr != null) { animTrBarr.avatar = officialAvatar01; animTrBarr.cullingMode = AnimatorCullingMode.AlwaysAnimate; animTrBarr.applyRootMotion = false; }
            if (animTrSideswipe != null) { animTrSideswipe.avatar = officialAvatar01; animTrSideswipe.cullingMode = AnimatorCullingMode.AlwaysAnimate; animTrSideswipe.applyRootMotion = false; }
        }

        var fingerTester = sideswipeInst.GetComponent<SideswipeFingerTester>() ?? sideswipeInst.AddComponent<SideswipeFingerTester>();
        fingerTester.leftHandAxis = SideswipeFingerTester.CurlAxis.Forward_Z;
        fingerTester.autoWiggle = false;
        fingerTester.InitializeBones();

        GameObject ctrlGo = new GameObject("SideswipePreviewController");
        var ctrl = ctrlGo.AddComponent<SideswipePreviewController>();
        ctrl.animOfficialBarricade = animBarr;
        ctrl.animSideswipe = animSideswipe;

        // Collect all clips
        Dictionary<string, AnimationClip> allClips = new Dictionary<string, AnimationClip>();
        CollectClipsFromGo(barrPrefab, allClips);
        foreach (var c in barrBundle.LoadAllAssets<AnimationClip>()) if (c != null && !allClips.ContainsKey(c.name)) allClips[c.name] = c;
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
        foreach (var t in barrInst.GetComponentsInChildren<Transform>(true)) { initPos[t] = t.localPosition; initRot[t] = t.localRotation; initScl[t] = t.localScale; }
        foreach (var t in sideswipeInst.GetComponentsInChildren<Transform>(true)) { initPos[t] = t.localPosition; initRot[t] = t.localRotation; initScl[t] = t.localScale; }

        void RestoreInitialPose() {
            foreach (var kv in initPos) {
                if (kv.Key != null) {
                    kv.Key.localPosition = kv.Value;
                    kv.Key.localRotation = initRot[kv.Key];
                    kv.Key.localScale = initScl[kv.Key];
                }
            }
            barrInst.transform.SetPositionAndRotation(new Vector3(4.2f, 0f, 0f), Quaternion.identity);
            sideswipeInst.transform.SetPositionAndRotation(new Vector3(-4.2f, 0f, 0f), Quaternion.identity);
        }

        // 6. Vehicle Mode Clean Horizontal Stance (Rest pose on wheels)
        string chosenVehRoot = null;
        string chosenVehTrans = null; // Clean horizontal vehicle rest pose (avoids vertical level-up flips)
        float chosenVehT = 0f;

        float jabPeakT = FindPeakForwardHandTime(barrInst, animBarr, allClips, "feral_normal_attackLight_01_slash_R", RestoreInitialPose, 0.35f);
        float heavyT = FindClipFracTime(allClips, "Barricade_Normal_attackHeavy", 0.40f, 0.45f);
        float kickT = FindClipFracTime(allClips, "feral_normal_attackLight_04_two_hand_smash", 0.38f, 0.36f);
        float vicT = 1.50f; // Authoritative peak roar frame of feral_normal_victory (t=1.5s)

        // 7. Render Gate 3 Synchronized Action Screenshots (CPU BakeMesh + PlayableGraph!)
        int w = 1920, h = 1080;
        RenderTexture rt = new RenderTexture(w, h, 24, RenderTextureFormat.ARGB32) { antiAliasing = 8 };
        Texture2D ss = new Texture2D(w, h, TextureFormat.RGB24, false);
        Transform hipsBarr = FindChildRecursive(barrInst.transform, "Hips");
        Transform hipsSideswipe = FindChildRecursive(sideswipeInst.transform, "Hips");

        void RenderPoseShot(string clipName, float sampleTime, Vector3 camPos, Vector3 lookTarget, string fileName,
                            bool vehicleMode = false, string transClipName = null, float curlAngle = 0f, bool hideBarr = false) {
            RestoreInitialPose();

            if (trBarr != null) trBarr.gameObject.SetActive(vehicleMode);
            if (trSideswipe != null) trSideswipe.gameObject.SetActive(vehicleMode);
            barrActiveSmr00.enabled = !vehicleMode && !hideBarr;
            barrActiveSmr01.gameObject.SetActive(vehicleMode);
            barrActiveSmr01.enabled = vehicleMode && !hideBarr;
            sideswipeSmr00.enabled = !vehicleMode;
            sideswipeSmr01.gameObject.SetActive(vehicleMode);
            sideswipeSmr01.enabled = vehicleMode;

            if (clipName != null && allClips.TryGetValue(clipName, out AnimationClip c)) {
                EvalPairGraph(animBarr, animSideswipe, c, sampleTime);
            } else if (clipName != null) {
                Debug.LogWarning($"[Shot {fileName}] Missing root clip '{clipName}'");
            }
            if (vehicleMode && transClipName != null && allClips.TryGetValue(transClipName, out AnimationClip tc) && animTrBarr != null && animTrSideswipe != null) {
                EvalPairGraph(animTrBarr, animTrSideswipe, tc, sampleTime);
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

            float spacing = 4.2f;
            if (!vehicleMode && hipsBarr != null && hipsSideswipe != null) {
                Vector3 dM = hipsBarr.position - barrInst.transform.position;
                barrInst.transform.position = new Vector3(spacing - dM.x, 0f, -dM.z);
                Vector3 dB = hipsSideswipe.position - sideswipeInst.transform.position;
                sideswipeInst.transform.position = new Vector3(-spacing - dB.x, 0f, -dB.z);
            }

            SkinnedMeshRenderer[] activeSmrs = vehicleMode
                ? (hideBarr ? new[] { sideswipeSmr01 } : new[] { barrActiveSmr01, sideswipeSmr01 })
                : (hideBarr ? new[] { sideswipeSmr00 } : new[] { barrActiveSmr00, sideswipeSmr00 });

            List<GameObject> tempGos = new List<GameObject>();
            List<Mesh> tempMeshes = new List<Mesh>();
            for (int idx = 0; idx < activeSmrs.Length; idx++) {
                var smr = activeSmrs[idx];
                if (smr == null) continue;
                Mesh bm = new Mesh();
                smr.BakeMesh(bm, true);
                bm.RecalculateBounds();
                GameObject bgo = new GameObject("TempBaked_" + smr.name);
                if (vehicleMode) {
                    bgo.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
                } else {
                    bgo.transform.SetPositionAndRotation(smr.transform.position, smr.transform.rotation);
                }
                bgo.transform.localScale = Vector3.one;
                bgo.AddComponent<MeshFilter>().sharedMesh = bm;
                var mr = bgo.AddComponent<MeshRenderer>();
                mr.sharedMaterials = smr.sharedMaterials;
                smr.enabled = false;
                tempGos.Add(bgo);
                tempMeshes.Add(bm);

                if (vehicleMode) {
                    Bounds wb = mr.bounds;
                    float targetX = (!hideBarr && idx == 0) ? spacing : -spacing;
                    bgo.transform.position = new Vector3(targetX - wb.center.x, -wb.min.y, -wb.center.z);
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
        RenderPoseShot(null, 0f, new Vector3(0f, 5.8f, 21.0f), new Vector3(0f, 5.4f, 0f), "unity_sbs_00_rest_pose.png");
        string idleClip = allClips.ContainsKey("feral_normal_idle") ? "feral_normal_idle" : "feral_normal_idle_02";
        RenderPoseShot(idleClip, 0.35f, new Vector3(0f, 5.8f, 21.0f), new Vector3(0f, 5.4f, 0f), "unity_sbs_01_combat_idle_front.png");
        string selClip = allClips.ContainsKey("Frontend_Feral_idle") ? "Frontend_Feral_idle" : (allClips.ContainsKey("Prefight_Feral_idle") ? "Prefight_Feral_idle" : idleClip);
        RenderPoseShot(selClip, 0.50f, new Vector3(6.2f, 6.2f, 20.0f), new Vector3(0f, 5.4f, 0f), "unity_sbs_02_teamselect_idle_34.png");
        RenderPoseShot(idleClip, 0.35f, new Vector3(-6.5f, 6.8f, -20.0f), new Vector3(0f, 5.4f, 0f), "unity_sbs_03_back_blades_view.png");
        string slashClip = allClips.ContainsKey("feral_normal_attackLight_01_slash_R") ? "feral_normal_attackLight_01_slash_R" : "feral_normal_attackLight_02_slash_L";
        RenderPoseShot(slashClip, jabPeakT, new Vector3(-6.8f, 6.0f, 20.0f), new Vector3(0f, 5.4f, 0f), "unity_sbs_04_light_slash_action.png");
        string heavyClip = allClips.ContainsKey("Barricade_Normal_attackHeavy") ? "Barricade_Normal_attackHeavy" : "feral_normal_attackMedium_01_over_hand_slash_down_R";
        RenderPoseShot(heavyClip, heavyT, new Vector3(-6.8f, 6.0f, 20.0f), new Vector3(0f, 5.4f, 0f), "unity_sbs_05_heavy_attack_action.png");
        RenderPoseShot(null, 0f, new Vector3(0f, 4.8f, 16.5f), new Vector3(0f, 1.2f, 0f), "unity_sbs_06_vehicle_mode_sbs.png", true, null);
        RenderPoseShot(null, 0f, new Vector3(-13.5f, 2.5f, 0f), new Vector3(-4.2f, 1.2f, 0f), "unity_sbs_06b_vehicle_side.png", true, null);
        string smashClip = allClips.ContainsKey("feral_normal_attackLight_04_two_hand_smash") ? "feral_normal_attackLight_04_two_hand_smash" : "feral_normal_attackLight_03_up_slash_R";
        RenderPoseShot(smashClip, kickT, new Vector3(-6.8f, 5.8f, 20.0f), new Vector3(0f, 5.2f, 0f), "unity_sbs_07_finisher_action.png");
        string vicClip = allClips.ContainsKey("feral_normal_victory") ? "feral_normal_victory" : idleClip;
        RenderPoseShot(vicClip, vicT, new Vector3(0f, 5.8f, 21.0f), new Vector3(0f, 5.4f, 0f), "unity_sbs_08_victory_pose.png");

        // Left Hand 3-Finger Articulation Micro-Check (Open vs Curled Fist)
        RestoreInitialPose();
        Vector3 lHandPos = new Vector3(-6.35f, 5.65f, 0.45f);
        RenderPoseShot(null, 0f, lHandPos + new Vector3(-1.6f, 0.25f, 2.0f), lHandPos, "unity_10a_left_hand_open.png", false, null, 0f, true);
        RenderPoseShot(null, 0f, lHandPos + new Vector3(-1.6f, 0.25f, 2.0f), lHandPos, "unity_10b_left_hand_curled.png", false, null, 65f, true);

        // Forearm Blade & Hand Integration Closeup
        RenderPoseShot(null, 0f, lHandPos + new Vector3(-2.6f, 0.6f, 2.6f), lHandPos + new Vector3(0.2f, 0.5f, 0f), "unity_10c_arm_blade_closeup.png", false, null, 0f, true);

        // Restore Clean Scene & Make Scenes[0] = Sideswipe_Inspection.unity
        RestoreInitialPose();
        if (trBarr != null) trBarr.gameObject.SetActive(false);
        if (trSideswipe != null) trSideswipe.gameObject.SetActive(false);
        barrActiveSmr00.enabled = true; barrActiveSmr01.enabled = false;
        sideswipeSmr00.enabled = true; sideswipeSmr01.enabled = false;

        cam.targetTexture = null;
        RenderTexture.active = null;
        UnityEngine.Object.DestroyImmediate(rt);
        UnityEngine.Object.DestroyImmediate(ss);
        cam.transform.position = new Vector3(0f, 5.8f, 21.0f);
        cam.transform.LookAt(new Vector3(0f, 5.4f, 0f));

        animBarr.avatar = null;
        animSideswipe.avatar = null;
        if (animTrBarr != null) animTrBarr.avatar = null;
        if (animTrSideswipe != null) animTrSideswipe.avatar = null;

        EditorSceneManager.SaveScene(scene, SCENE_PATH);
        var ebScenes = new List<EditorBuildSettingsScene> { new EditorBuildSettingsScene(SCENE_PATH, true) };
        EditorBuildSettings.scenes = ebScenes.ToArray();
        Debug.Log("[✓] Saved inspection scene & set EditorBuildSettings.scenes[0]: " + SCENE_PATH);

        if (procBundle != null) procBundle.Unload(false);
        barrBundle.Unload(false);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();

        // Pack Android Mesh AssetBundle (sideswipe_mesh.assetbundle)
        string outAbDir = @"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles";
        Directory.CreateDirectory(outAbDir);
        AssetBundleBuild[] builds = new AssetBundleBuild[1];
        builds[0].assetBundleName = "sideswipe_mesh.assetbundle";
        builds[0].assetNames = new[] { ROBOT_ASSET, VH_ASSET };
        var manifest = BuildPipeline.BuildAssetBundles(
            outAbDir,
            builds,
            BuildAssetBundleOptions.ForceRebuildAssetBundle | BuildAssetBundleOptions.ChunkBasedCompression,
            BuildTarget.Android
        );
        if (manifest != null) {
            Debug.Log("[✓] Successfully packed sideswipe_mesh.assetbundle!");
        }

        Debug.Log("=== [Sideswipe] Gate 3 Complete! All Verification Renders Exported! ===");
        if (Application.isBatchMode) EditorApplication.Exit(0);
    }

    static AxisSpec DetectAxisSpec(string fbxPath, SkinnedMeshRenderer barrSmr00) {
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

        // Barricade coords: LeftHand.x < 0 (-2.05), LeftToeBase.z > 0 (+0.46)
        float sx = (cLH.x <= 0f) ? 1f : -1f;
        // Authoritative axis mapping: In Blender standard, Front is -Y, Back is +Y, Up is +Z.
        // In Unity, Front is +Z, Back is -Z, Up is +Y.
        // When zIsHeight is true, FBX Y is depth, which must be inverted to map Blender -Y to Unity +Z (sz = -1.0f).
        // This guarantees det = (-1) * (1) * (-1) = +1.0 (positive determinant, preserving chirality and outward normals).
        float sz = zIsHeight ? -1f : 1f;
        float det = (zIsHeight ? -1f : 1f) * sx * sz;
        Debug.Log($"[AxisSpec] rawBounds={raw.bounds} cLH={cLH} cRH={cRH} cToe={cToe} -> zIsHeight={zIsHeight}, sx={sx}, sz={sz}, det={det}");
        return new AxisSpec { zIsHeight = zIsHeight, sx = sx, sz = sz, det = det };
    }

    static Mesh BuildGraftedMesh(string fbxPath, SkinnedMeshRenderer barrSmr, AxisSpec spec, string meshName, string fallbackBone, string forceSingleBone) {
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
            // Vehicle FBX has v.z as height (2.58m) and v.y as length (11.20m, front hood at +Y).
            // Mapping: Unity_Y = v.z (height), Unity_Z = +1.0 * v.y (front hood at +Z forward).
            useZHeight = true;
            useSx = 1f;
            useSz = 1f;
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

        Transform[] barrBones = barrSmr.bones;
        Dictionary<string, int> barrMap = new Dictionary<string, int>();
        for (int i = 0; i < barrBones.Length; i++) if (barrBones[i] != null) barrMap[barrBones[i].name] = i;
        int fbIdx = barrMap.ContainsKey(fallbackBone) ? barrMap[fallbackBone] : 0;

        int[] remap = new int[srcSmr.bones.Length];
        int matched = 0;
        for (int j = 0; j < srcSmr.bones.Length; j++) {
            string bn = srcSmr.bones[j] != null ? srcSmr.bones[j].name : "";
            if (barrMap.TryGetValue(bn, out int idx)) { remap[j] = idx; matched++; }
            else remap[j] = fbIdx;
        }

        BoneWeight[] origBw = raw.boneWeights;
        BoneWeight[] newBw = new BoneWeight[rv.Length];
        if (!string.IsNullOrEmpty(forceSingleBone) && barrMap.TryGetValue(forceSingleBone, out int forcedIdx)) {
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
        outMesh.bindposes = barrSmr.sharedMesh.bindposes;

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

    static void VerifyLeftFingerJointAlignment(string fbxPath, SkinnedMeshRenderer barrSmr00, AxisSpec spec) {
        GameObject fbx = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
        SkinnedMeshRenderer srcSmr = fbx.GetComponentInChildren<SkinnedMeshRenderer>(true);

        Transform[] barrBones = barrSmr00.bones;
        Matrix4x4[] barrBps = barrSmr00.sharedMesh.bindposes;
        Matrix4x4[] fbxBps = srcSmr.sharedMesh.bindposes;
        Dictionary<string, int> fbxIdxMap = new Dictionary<string, int>();
        for (int j = 0; j < srcSmr.bones.Length; j++) if (srcSmr.bones[j] != null) fbxIdxMap[srcSmr.bones[j].name] = j;

        float maxErrMm = 0f;
        int checkedCount = 0;
        for (int i = 0; i < barrBones.Length && i < barrBps.Length; i++) {
            string bn = barrBones[i].name;
            string bl = bn.ToLower();
            if (!(bl.Contains("thumb") || bl.Contains("index") || bl.Contains("middle") || bl.Contains("ring") || bl.Contains("pinky"))) continue;
            if (!fbxIdxMap.TryGetValue(bn, out int fi) || fi >= fbxBps.Length) continue;
            Vector3 fp = fbxBps[fi].inverse.MultiplyPoint3x4(Vector3.zero);
            Vector3 fUnity = spec.zIsHeight ? new Vector3(spec.sx * fp.x, fp.z, spec.sz * fp.y) : new Vector3(spec.sx * fp.x, fp.y, spec.sz * fp.z);
            Vector3 barrPos = barrBps[i].inverse.MultiplyPoint3x4(Vector3.zero);
            float errMm = Vector3.Distance(fUnity, barrPos) * 1000f;
            if (errMm > maxErrMm) maxErrMm = errMm;
            checkedCount++;
        }
        Debug.Log($"[FingerAudit] Checked {checkedCount}/15 Left finger bones against Barricade BindPose: maxPosDelta={maxErrMm:F3} mm");
    }

    static string AuditVehicleBonesAndClips(
            GameObject barrInst, SkinnedMeshRenderer barrSmr01, Animator animBarr, Animator animTrBarr, Transform trBarr,
            Dictionary<string, AnimationClip> allClips, Action restoreFn,
            out string chosenVehRoot, out string chosenVehTrans, out float chosenVehT) {
        string[] candClips = {
            "frontend_Barricade_levelup_vehicle_idle_transformed",
            "BattleIntro_Cars_barricade_transformed",
            "barricade_cin_attackSpecial_03_transformed",
            "frontend_Barricade_levelup_enter_transformed",
            "frontend_Barricade_levelup_exit_transformed"
        };
        string[] rootPairs = {
            null,
            null,
            null,
            null,
            null
        };
        float[] sampleTimes = { 0.30f, 0.50f, 1.00f, 0.50f, 0.50f };

        string[] candBones = { "BodyBase", "COG" };
        Transform[] bones01 = barrSmr01.bones;
        Matrix4x4[] bps01 = barrSmr01.sharedMesh.bindposes;
        Dictionary<string, int> bIdxMap = new Dictionary<string, int>();
        for (int i = 0; i < bones01.Length; i++) if (bones01[i] != null) bIdxMap[bones01[i].name] = i;

        chosenVehRoot = null;
        chosenVehTrans = "frontend_Barricade_levelup_vehicle_idle_transformed";
        chosenVehT = 0.30f;
        string bestBone = "BodyBase";
        float bestScore = -999f;

        if (trBarr != null) trBarr.gameObject.SetActive(true);
        barrSmr01.enabled = true;

        for (int ci = 0; ci < candClips.Length; ci++) {
            string tClip = candClips[ci];
            string rClip = rootPairs[ci];
            if (!allClips.TryGetValue(tClip, out AnimationClip tc)) continue;
            float t = Mathf.Min(sampleTimes[ci], Mathf.Max(0f, tc.length * 0.5f));
            restoreFn();
            if (rClip != null && allClips.TryGetValue(rClip, out AnimationClip rc)) EvalSingleGraph(animBarr, rc, t);
            if (animTrBarr != null) EvalSingleGraph(animTrBarr, tc, t);

            Mesh bm = new Mesh();
            barrSmr01.BakeMesh(bm, true);
            GameObject tgo = new GameObject("TempBarrVehAudit");
            tgo.transform.SetPositionAndRotation(barrSmr01.transform.position, barrSmr01.transform.rotation);
            tgo.AddComponent<MeshFilter>().sharedMesh = bm;
            var mr = tgo.AddComponent<MeshRenderer>();
            Bounds wb = mr.bounds;
            Debug.Log($"[VehClipAudit] clip='{tClip}' (t={t:F2}s) Barr01 worldSize={wb.size:F2}");
            UnityEngine.Object.DestroyImmediate(tgo);
            UnityEngine.Object.DestroyImmediate(bm);

            foreach (string bn in candBones) {
                Transform trNode = bIdxMap.TryGetValue(bn, out int bi) ? bones01[bi] : FindChildRecursive(barrInst.transform, bn);
                if (trNode == null) continue;
                Matrix4x4 mRel = barrInst.transform.worldToLocalMatrix * trNode.localToWorldMatrix * (bIdxMap.ContainsKey(bn) ? bps01[bi] : Matrix4x4.identity);
                Vector3 up = mRel.MultiplyVector(Vector3.up);
                Vector3 fwd = mRel.MultiplyVector(Vector3.forward);
                Vector3 scl = new Vector3(mRel.GetColumn(0).magnitude, mRel.GetColumn(1).magnitude, mRel.GetColumn(2).magnitude);
                float score = up.y + fwd.z - Mathf.Abs(scl.x - 1f) - Mathf.Abs(scl.y - 1f) - Mathf.Abs(scl.z - 1f);
                Debug.Log($"   [VehBoneAudit] {bn,-24} up={up:F2} fwd={fwd:F2} scl={scl:F2} score={score:F2}");
                if (wb.size.z > wb.size.y * 1.1f && up.y > 0.80f && score > bestScore) {
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
