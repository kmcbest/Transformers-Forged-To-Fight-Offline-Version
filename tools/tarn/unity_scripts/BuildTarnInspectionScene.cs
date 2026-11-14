using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;
using UnityEngine.SceneManagement;

public static class BuildTarnInspectionScene {
    private const string UM_ANIM_BUNDLE = @"E:\Agent\TFTF-blender\toolchain\ultramagnus_anims_registered.assetbundle";
    private const string UM_FALLBACK_BUNDLE = @"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\ultramagnus_gs_leader_odr\ultramagnus_gs_leader.assetbundle";
    private const string PROC_ANIM_BUNDLE = @"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle";
    private const string SCRATCH_DIR = @"C:\Users\Xiangli496\.gemini\antigravity\brain\66aaeff3-2652-4f24-8fc9-00b0ef375582\scratch";

    private const string ROBOT_FBX = "Assets/Tarn/tarn_robot_prepared.fbx";
    private const string VEH_FBX = "Assets/Tarn/tarn_tank_prepared.fbx";
    private const string OUT_ROBOT_MESH = "Assets/Tarn/cha_tarn_gs_00.asset";
    private const string OUT_VEH_MESH = "Assets/Tarn/cha_tarn_gs_01.asset";
    private const string SCENE_PATH = "Assets/Scenes/Tarn_Inspection.unity";

    struct AxisSpec {
        public bool zIsHeight;
        public float sx;
        public float sz;
        public float det;
    }

    [MenuItem("TFTF/Build Tarn vs UltraMagnus Inspection Scene")]
    public static void Build() {
        Debug.Log("=== [Tarn] Building Authoritative Side-by-Side Inspection Scene (Donor: UltraMagnus_GS_Leader) ===");
        Directory.CreateDirectory(SCRATCH_DIR);
        Directory.CreateDirectory(Path.Combine(Application.dataPath, "Tarn/UltraMagnus"));
        Directory.CreateDirectory(Path.Combine(Application.dataPath, "Scenes"));
        AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);

        // 1. Configure NormalMap importers & FBX importers
        string[] normalMaps = {
            "Assets/Tarn/cha_tarn_main_NM_std.png",
            "Assets/Tarn/cha_tarn_tform_misc_NM_std.png",
            "Assets/Tarn/UltraMagnus/tex_main_NM.png",
            "Assets/Tarn/UltraMagnus/tex_tform_misc_NM.png",
            "Assets/Tarn/UltraMagnus/tex_wpns_NM.png"
        };
        foreach (string np in normalMaps) {
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

        // 2. Load Ultra Magnus bundle & Procedural animations bundle
        foreach (var b in AssetBundle.GetAllLoadedAssetBundles()) b.Unload(false);

        string umPath = File.Exists(UM_ANIM_BUNDLE) ? UM_ANIM_BUNDLE : UM_FALLBACK_BUNDLE;
        AssetBundle umBundle = AssetBundle.LoadFromFile(umPath);
        if (umBundle == null) {
            Debug.LogError("[Tarn] Failed to load Ultra Magnus bundle: " + umPath);
            EditorApplication.Exit(1);
            return;
        }
        AssetBundle procBundle = File.Exists(PROC_ANIM_BUNDLE) ? AssetBundle.LoadFromFile(PROC_ANIM_BUNDLE) : null;

        GameObject umPrefab = umBundle.LoadAsset<GameObject>("assets/bundles/characters/merged/ultramagnus_gs_leader/ultramagnus_gs_leader.prefab");
        if (umPrefab == null) umPrefab = umBundle.LoadAsset<GameObject>("UltraMagnus_GS_Leader");
        if (umPrefab == null) {
            foreach (var g in umBundle.LoadAllAssets<GameObject>()) {
                if (g.name.ToLower().Contains("ultramagnus") && !g.name.ToLower().Contains("_lw")) { umPrefab = g; break; }
            }
        }
        if (umPrefab == null) {
            Debug.LogError("[Tarn] Missing UltraMagnus_GS_Leader prefab!");
            EditorApplication.Exit(1);
            return;
        }

        SkinnedMeshRenderer umPrefabSmr00 = null, umPrefabSmr01 = null;
        foreach (var smr in umPrefab.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name.Contains("_00") && !smr.name.Contains("wpns")) umPrefabSmr00 = smr;
            else if (smr.name.Contains("_01")) umPrefabSmr01 = smr;
        }
        if (umPrefabSmr00 == null || umPrefabSmr01 == null) {
            Debug.LogError("[Tarn] Missing _00 or _01 SMR on UltraMagnus prefab!");
            EditorApplication.Exit(1);
            return;
        }

        Mesh umSaved00 = SaveClonedMesh(umPrefabSmr00.sharedMesh, "cha_ultramagnus_official_00", "Assets/Tarn/UltraMagnus/cha_ultramagnus_official_00.asset");
        Mesh umSaved01 = SaveClonedMesh(umPrefabSmr01.sharedMesh, "cha_ultramagnus_official_01", "Assets/Tarn/UltraMagnus/cha_ultramagnus_official_01.asset");

        Avatar av00 = umPrefab.GetComponent<Animator>() != null ? umPrefab.GetComponent<Animator>().avatar : null;
        Transform prefabTr = FindChildRecursive(umPrefab.transform, "transformed");
        Avatar av01 = (prefabTr != null && prefabTr.GetComponent<Animator>() != null) ? prefabTr.GetComponent<Animator>().avatar : null;

        // 3. Determine exact Blender->Unity AxisSpec from Robot FBX vs Ultra Magnus 53-bone landmarks
        AxisSpec spec = DetectAxisSpec(ROBOT_FBX, umPrefabSmr00);

        // Build Robot Mesh (<= 65535 verts asserted)
        Mesh tarnRobotMesh = BuildGraftedMesh(ROBOT_FBX, umPrefabSmr00, spec, "cha_tarn_gs_00", "Spine1", null);
        if (tarnRobotMesh.vertexCount > 65535) {
            Debug.LogError($"[Tarn] Vertex budget exceeded: {tarnRobotMesh.vertexCount} > 65535!");
            EditorApplication.Exit(1);
            return;
        }
        SaveOrReplaceMeshAsset(tarnRobotMesh, OUT_ROBOT_MESH);
        Mesh savedTarn00 = AssetDatabase.LoadAssetAtPath<Mesh>(OUT_ROBOT_MESH);

        // Verify 30-finger joint alignment against UM bindposes
        VerifyFingerJointAlignment(ROBOT_FBX, umPrefabSmr00, spec);

        // Initial Vehicle Mesh bound to chop1_torso_center (will audit all _01 bones on live clips below!)
        Mesh tarnVehMesh = BuildGraftedMesh(VEH_FBX, umPrefabSmr01, spec, "cha_tarn_gs_01", "chop1_torso_center", "chop1_torso_center");
        if (tarnVehMesh.vertexCount > 65535) {
            Debug.LogError($"[Tarn] Vehicle vertex budget exceeded: {tarnVehMesh.vertexCount} > 65535!");
            EditorApplication.Exit(1);
            return;
        }
        SaveOrReplaceMeshAsset(tarnVehMesh, OUT_VEH_MESH);
        Mesh savedTarn01 = AssetDatabase.LoadAssetAtPath<Mesh>(OUT_VEH_MESH);

        // 4. Create Materials (Tarn Single-Submesh + UM Multi-Submesh Reference)
        Material matUmMain = CreateOrUpdateMat("Assets/Tarn/UltraMagnus/M_UM_Main.mat",
            "Assets/Tarn/UltraMagnus/tex_cha_ultramagnus_gs_leader_main_a.png",
            "Assets/Tarn/UltraMagnus/tex_main_NM.png", null, 0.42f, 0.25f, new Vector2(1f, 1f), Vector2.zero);
        Material matUmMiscTop = CreateOrUpdateMat("Assets/Tarn/UltraMagnus/M_UM_MiscTop.mat",
            "Assets/Tarn/UltraMagnus/tex_tform_misc_A.png",
            "Assets/Tarn/UltraMagnus/tex_tform_misc_NM.png", null, 0.40f, 0.25f, new Vector2(1f, 0.5f), new Vector2(0f, 0.5f));
        Material matUmMiscBot = CreateOrUpdateMat("Assets/Tarn/UltraMagnus/M_UM_MiscBot.mat",
            "Assets/Tarn/UltraMagnus/tex_tform_misc_A.png",
            "Assets/Tarn/UltraMagnus/tex_tform_misc_NM.png", null, 0.40f, 0.25f, new Vector2(1f, 0.5f), Vector2.zero);
        Material matUmWpns = CreateOrUpdateMat("Assets/Tarn/UltraMagnus/M_UM_Wpns.mat",
            "Assets/Tarn/UltraMagnus/tex_cha_ultramagnus_gs_leader_wpns_a.png",
            "Assets/Tarn/UltraMagnus/tex_wpns_NM.png", null, 0.45f, 0.30f, Vector2.one, Vector2.zero);

        Material matTarnMain = CreateOrUpdateMat("Assets/Tarn/M_Tarn_Main.mat",
            "Assets/Tarn/cha_tarn_main_a.png",
            "Assets/Tarn/cha_tarn_main_NM_std.png",
            "Assets/Tarn/cha_tarn_main_Emission.png", 0.46f, 0.28f, Vector2.one, Vector2.zero);
        Material matTarnVh = CreateOrUpdateMat("Assets/Tarn/M_Tarn_Vh.mat",
            "Assets/Tarn/cha_tarn_tform_misc_A.png",
            "Assets/Tarn/cha_tarn_tform_misc_NM_std.png",
            "Assets/Tarn/cha_tarn_tform_misc_Emission.png", 0.46f, 0.28f, Vector2.one, Vector2.zero);

        // 5. Build Clean Side-by-Side Scene
        Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        CreateDirLight("Key Light", new Vector3(24f, -152f, 0f), 1.30f, new Color(1.0f, 0.98f, 0.95f));
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
        camGo.transform.position = new Vector3(0f, 6.2f, 21.0f);
        camGo.transform.LookAt(new Vector3(0f, 5.8f, 0f));

        // Left of Screen (looking from +Z toward 0, +X is Screen Left!):
        // Official Ultra Magnus at X = +4.2f; Tarn Candidate at X = -4.2f
        GameObject umInst = UnityEngine.Object.Instantiate(umPrefab);
        umInst.name = "UltraMagnus_Official_Reference";
        umInst.transform.SetPositionAndRotation(new Vector3(4.2f, 0f, 0f), Quaternion.identity);
        SkinnedMeshRenderer umSmr00 = null, umSmr01 = null;
        foreach (var smr in umInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name.Contains("_00") && !smr.name.Contains("wpns")) {
                smr.sharedMesh = umSaved00;
                smr.sharedMaterials = new[] { matUmMain, matUmMiscTop };
                smr.updateWhenOffscreen = true;
                smr.enabled = true;
                umSmr00 = smr;
            } else if (smr.name.Contains("_01")) {
                smr.sharedMesh = umSaved01;
                smr.sharedMaterials = new[] { matUmMiscTop, matUmMain, matUmMiscBot };
                smr.updateWhenOffscreen = true;
                smr.enabled = false;
                umSmr01 = smr;
            } else {
                smr.sharedMaterials = new[] { matUmWpns };
                smr.enabled = false;
            }
        }

        GameObject tarnInst = UnityEngine.Object.Instantiate(umPrefab);
        tarnInst.name = "Tarn_Candidate";
        tarnInst.transform.SetPositionAndRotation(new Vector3(-4.2f, 0f, 0f), Quaternion.identity);
        SkinnedMeshRenderer tarnSmr00 = null, tarnSmr01 = null;
        foreach (var smr in tarnInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            string ln = smr.name.ToLower();
            if (smr.name.Contains("_00") && !ln.Contains("wpns")) {
                smr.gameObject.name = "cha_tarn_gs_00";
                smr.sharedMesh = savedTarn00;
                smr.sharedMaterials = new[] { matTarnMain };
                smr.updateWhenOffscreen = true;
                smr.enabled = true;
                tarnSmr00 = smr;
            } else if (smr.name.Contains("_01")) {
                smr.gameObject.name = "cha_tarn_gs_01";
                smr.sharedMesh = savedTarn01;
                smr.sharedMaterials = new[] { matTarnVh };
                smr.updateWhenOffscreen = true;
                smr.enabled = false;
                tarnSmr01 = smr;
            } else {
                // Design A1: Hide/Disable ALL donor weapon SMRs (axe, rightgun, leftgun) on Tarn
                smr.enabled = false;
                smr.sharedMesh = null;
                smr.gameObject.SetActive(false);
            }
        }
        // Also deactivate weapon holder subtrees (axe / rightgun / leftgun) on Tarn per A1
        foreach (var t in tarnInst.GetComponentsInChildren<Transform>(true)) {
            if (t.name == "axe" || t.name == "rightgun" || t.name == "leftgun") {
                t.gameObject.SetActive(false);
            }
        }

        // Remove missing MonoBehaviours from instantiated prefabs (in case Kabam scripts fail in Editor)
        foreach (var t in umInst.GetComponentsInChildren<Transform>(true)) GameObjectUtility.RemoveMonoBehavioursWithMissingScript(t.gameObject);
        foreach (var t in tarnInst.GetComponentsInChildren<Transform>(true)) GameObjectUtility.RemoveMonoBehavioursWithMissingScript(t.gameObject);

        Animator animUm = umInst.GetComponent<Animator>();
        Animator animTarn = tarnInst.GetComponent<Animator>();
        if (av00 != null) { animUm.avatar = av00; animTarn.avatar = av00; }
        animUm.cullingMode = AnimatorCullingMode.AlwaysAnimate;
        animTarn.cullingMode = AnimatorCullingMode.AlwaysAnimate;
        animUm.applyRootMotion = false;
        animTarn.applyRootMotion = false;

        Transform trUm = FindChildRecursive(umInst.transform, "transformed");
        Transform trTarn = FindChildRecursive(tarnInst.transform, "transformed");
        Animator animTrUm = trUm != null ? (trUm.GetComponent<Animator>() ?? trUm.gameObject.AddComponent<Animator>()) : null;
        Animator animTrTarn = trTarn != null ? (trTarn.GetComponent<Animator>() ?? trTarn.gameObject.AddComponent<Animator>()) : null;
        if (av01 != null) {
            if (animTrUm != null) { animTrUm.avatar = av01; animTrUm.cullingMode = AnimatorCullingMode.AlwaysAnimate; animTrUm.applyRootMotion = false; }
            if (animTrTarn != null) { animTrTarn.avatar = av01; animTrTarn.cullingMode = AnimatorCullingMode.AlwaysAnimate; animTrTarn.applyRootMotion = false; }
        }

        // Attach TarnFingerTester + TarnPreviewController
        var fingerTester = tarnInst.GetComponent<TarnFingerTester>() ?? tarnInst.AddComponent<TarnFingerTester>();
        fingerTester.leftHandAxis = TarnFingerTester.CurlAxis.Forward_Z;
        fingerTester.rightHandAxis = TarnFingerTester.CurlAxis.Back_NegZ;
        fingerTester.autoWiggle = false;
        fingerTester.InitializeBones();

        GameObject ctrlGo = new GameObject("TarnPreviewController");
        var ctrl = ctrlGo.AddComponent<TarnPreviewController>();
        ctrl.animOfficialUM = animUm;
        ctrl.animTarn = animTarn;

        // Collect all AnimationClips cleanly
        Dictionary<string, AnimationClip> allClips = new Dictionary<string, AnimationClip>();
        CollectClipsFromGo(umPrefab, allClips);
        foreach (var c in umBundle.LoadAllAssets<AnimationClip>()) if (c != null && !allClips.ContainsKey(c.name)) allClips[c.name] = c;
        if (procBundle != null) {
            foreach (string ap in procBundle.GetAllAssetNames()) {
                foreach (var sub in procBundle.LoadAssetWithSubAssets(ap)) {
                    if (sub is AnimationClip ac && !allClips.ContainsKey(ac.name)) allClips[ac.name] = ac;
                }
            }
        }
        Debug.Log($"[ClipAudit] Collected {allClips.Count} AnimationClips total.");
        foreach (var kv in allClips) {
            string kl = kv.Key.ToLower();
            if (kl.Contains("magnus") || kl.Contains("tact") || kl.Contains("pistol") || kl.Contains("brawler") || kl.Contains("brute") || kl.Contains("vehicle")) {
                Debug.Log($"  [Clip] {kv.Key} len={kv.Value.length:F2}s human={kv.Value.humanMotion}");
            }
        }

        // Snapshot initial rest pose
        var initPos = new Dictionary<Transform, Vector3>();
        var initRot = new Dictionary<Transform, Quaternion>();
        var initScl = new Dictionary<Transform, Vector3>();
        foreach (var t in umInst.GetComponentsInChildren<Transform>(true)) { initPos[t] = t.localPosition; initRot[t] = t.localRotation; initScl[t] = t.localScale; }
        foreach (var t in tarnInst.GetComponentsInChildren<Transform>(true)) { initPos[t] = t.localPosition; initRot[t] = t.localRotation; initScl[t] = t.localScale; }

        void RestoreInitialPose() {
            foreach (var kv in initPos) {
                if (kv.Key != null) {
                    kv.Key.localPosition = kv.Value;
                    kv.Key.localRotation = initRot[kv.Key];
                    kv.Key.localScale = initScl[kv.Key];
                }
            }
            umInst.transform.SetPositionAndRotation(new Vector3(4.2f, 0f, 0f), Quaternion.identity);
            tarnInst.transform.SetPositionAndRotation(new Vector3(-4.2f, 0f, 0f), Quaternion.identity);
        }

        // 6. Comprehensive _01 Vehicle Bone & Clip Uprightness Audit!
        string chosenVehRoot = null;
        string chosenVehTrans = "frontend_Ultramagnus_gs_levelup_vehicle_idle_transformed";
        float chosenVehT = 0.0f;
        string bestVehBone = AuditVehicleBonesAndClips(umInst, umSmr01, animUm, animTrUm, trUm, allClips, RestoreInitialPose,
            out chosenVehRoot, out chosenVehTrans, out chosenVehT);

        if (!string.IsNullOrEmpty(bestVehBone) && bestVehBone != "chop1_torso_center") {
            Debug.Log($"[VehRebind] Rebinding cha_tarn_gs_01 cleanly to audited steady bone '{bestVehBone}'!");
            Mesh reboundVeh = BuildGraftedMesh(VEH_FBX, umPrefabSmr01, spec, "cha_tarn_gs_01", bestVehBone, bestVehBone);
            SaveOrReplaceMeshAsset(reboundVeh, OUT_VEH_MESH);
            savedTarn01 = AssetDatabase.LoadAssetAtPath<Mesh>(OUT_VEH_MESH);
            tarnSmr01.sharedMesh = savedTarn01;
        }

        // Find peak timing for Ranged Dual-Cannon & Light Jab & SP1/SP3
        float rangedPeakT = FindPeakForwardHandTime(umInst, animUm, allClips, "dual pistols_attackRanged_gun_01", RestoreInitialPose, 0.35f);
        float jabPeakT = FindPeakForwardHandTime(umInst, animUm, allClips, "tactical_normal_attacklight_01_jab_L", RestoreInitialPose, 0.25f);
        float sp1PeakT = FindClipFracTime(allClips, "ultra_magnus_attackSpecial_01", 0.45f, 0.65f);
        float sp2PeakT = FindClipFracTime(allClips, "ultra_magnus_attackSpecial_02", 0.45f, 0.70f);
        float sp3RobotT = FindClipFracTime(allClips, "UltraMagnus_gs_attackSpecial_03", 0.20f, 0.35f);
        float heavyRobotT = FindClipFracTime(allClips, "UltraMagnus_Normal_attackHeavy", 0.45f, 0.50f);
        float vicT = FindClipFracTime(allClips, "Ultramagnus_Normal_victory", 0.75f, 1.40f);

        // 7. Render Gate 3 Synchronized Action Screenshots (CPU BakeMesh + PlayableGraph!)
        int w = 1920, h = 1080;
        RenderTexture rt = new RenderTexture(w, h, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
        Texture2D ss = new Texture2D(w, h, TextureFormat.RGB24, false);
        Transform hipsUm = FindChildRecursive(umInst.transform, "Hips");
        Transform hipsTarn = FindChildRecursive(tarnInst.transform, "Hips");

        void RenderShot(string clipName, float sampleTime, Vector3 camPos, Vector3 lookTarget, string fileName,
                        bool vehicleMode = false, string transClipName = null, float curlAngle = 0f, bool hideUm = false) {
            RestoreInitialPose();

            if (trUm != null) trUm.gameObject.SetActive(vehicleMode);
            if (trTarn != null) trTarn.gameObject.SetActive(vehicleMode);
            umSmr00.enabled = !vehicleMode && !hideUm;
            umSmr01.gameObject.SetActive(vehicleMode);
            umSmr01.enabled = vehicleMode && !hideUm;
            tarnSmr00.enabled = !vehicleMode;
            tarnSmr01.gameObject.SetActive(vehicleMode);
            tarnSmr01.enabled = vehicleMode;

            if (clipName != null && allClips.TryGetValue(clipName, out AnimationClip c)) {
                EvalPairGraph(animUm, animTarn, c, sampleTime);
            } else if (clipName != null) {
                Debug.LogWarning($"[Shot {fileName}] Missing root clip '{clipName}'");
            }
            if (vehicleMode && transClipName != null && allClips.TryGetValue(transClipName, out AnimationClip tc) && animTrUm != null && animTrTarn != null) {
                EvalPairGraph(animTrUm, animTrTarn, tc, sampleTime);
            } else if (vehicleMode && transClipName != null) {
                Debug.LogWarning($"[Shot {fileName}] Missing trans clip '{transClipName}'");
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

            float spacing = vehicleMode ? 5.0f : 5.0f;
            if (!vehicleMode && hipsUm != null && hipsTarn != null) {
                Vector3 dU = hipsUm.position - umInst.transform.position;
                umInst.transform.position = new Vector3(spacing - dU.x, 0f, -dU.z);
                Vector3 dT = hipsTarn.position - tarnInst.transform.position;
                tarnInst.transform.position = new Vector3(-spacing - dT.x, 0f, -dT.z);
            }

            SkinnedMeshRenderer[] activeSmrs = vehicleMode
                ? (hideUm ? new[] { tarnSmr01 } : new[] { umSmr01, tarnSmr01 })
                : (hideUm ? new[] { tarnSmr00 } : new[] { umSmr00, tarnSmr00 });

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
                    float targetX = (!hideUm && idx == 0) ? spacing : -spacing;
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
            File.WriteAllBytes(Path.Combine(SCRATCH_DIR, fileName), ss.EncodeToPNG());
            Debug.Log("[✓] Gate 3 screenshot saved: " + fileName);

            foreach (var g in tempGos) UnityEngine.Object.DestroyImmediate(g);
            foreach (var m in tempMeshes) UnityEngine.Object.DestroyImmediate(m);
            fingerTester.ResetAll();
        }

        // Render all Gate 3 Shots:
        RenderShot(null, 0f, new Vector3(0f, 6.2f, 21.5f), new Vector3(0f, 5.8f, 0f), "gate3_00_bind_pose_sbs.png");
        RenderShot("UltraMagnus_gs_CombatIdle", 0.25f, new Vector3(0f, 6.2f, 21.5f), new Vector3(0f, 5.8f, 0f), "gate3_01_combat_idle_sbs.png");
        RenderShot("TeamSelect_Brawler_idle", 0.40f, new Vector3(6.8f, 6.5f, 20.5f), new Vector3(0f, 5.8f, 0f), "gate3_02_teamselect_34_sbs.png");
        RenderShot("UltraMagnus_gs_CombatIdle", 0.25f, new Vector3(-7.2f, 7.2f, -20.5f), new Vector3(0f, 6.0f, 0f), "gate3_03_back_34_sbs.png");
        RenderShot("tactical_normal_attacklight_01_jab_L", jabPeakT, new Vector3(-7.5f, 6.4f, 21.5f), new Vector3(0f, 5.8f, 0f), "gate3_04_light_jab_sbs.png");
        RenderShot("dual pistols_attackRanged_gun_01", rangedPeakT, new Vector3(-8.5f, 6.6f, 21.5f), new Vector3(0f, 6.0f, 0f), "gate3_05_ranged_cannon_sbs.png");
        RenderShot("UltraMagnus_Normal_attackHeavy", heavyRobotT, new Vector3(-7.5f, 5.2f, 19.0f), new Vector3(0f, 2.3f, 0f), "gate3_06_heavy_attack_sbs.png", true, "UltraMagnus_Normal_attackHeavy_transformed");
        RenderShot(chosenVehRoot, chosenVehT, new Vector3(-6.2f, 5.2f, 18.5f), new Vector3(0f, 2.2f, 0f), "gate3_07_vehicle_sbs.png", true, chosenVehTrans);
        RenderShot(chosenVehRoot, chosenVehT, new Vector3(-16.5f, 2.8f, 2.0f), new Vector3(-5.0f, 2.2f, 0f), "gate3_08_vehicle_side.png", true, chosenVehTrans);
        RenderShot("ultra_magnus_attackSpecial_01", sp1PeakT, new Vector3(-7.5f, 6.6f, 21.5f), new Vector3(0f, 5.8f, 0f), "gate3_09_sp1_sbs.png");
        RenderShot("ultra_magnus_attackSpecial_02", sp2PeakT, new Vector3(7.0f, 6.6f, 21.5f), new Vector3(0f, 5.8f, 0f), "gate3_10_sp2_sbs.png");
        RenderShot("UltraMagnus_gs_attackSpecial_03", 0.35f, new Vector3(-7.0f, 6.8f, 22.0f), new Vector3(0f, 5.8f, 0f), "gate3_11_sp3_sbs.png");
        RenderShot("UltraMagnus_gs_attackSpecial_03", 2.50f, new Vector3(-7.0f, 5.4f, 19.5f), new Vector3(0f, 2.3f, 0f), "gate3_11b_sp3_vehicle_sbs.png", true, "UltraMagnus_gs_attackSpecial_03_transformed");
        RenderShot("Ultramagnus_Normal_victory", vicT, new Vector3(0f, 6.4f, 21.5f), new Vector3(0f, 5.8f, 0f), "gate3_12_victory_sbs.png");

        // 30-Finger Open + Curled Fist Closeups (aimed directly at Tarn's LeftHand & RightHand!)
        RestoreInitialPose();
        Vector3 lHandPos = FindChildRecursive(tarnInst.transform, "LeftHand").position + new Vector3(0f, -0.55f, 0.1f);
        Vector3 rHandPos = FindChildRecursive(tarnInst.transform, "RightHand").position + new Vector3(0f, -0.55f, 0.1f);
        RenderShot(null, 0f, lHandPos + new Vector3(-2.6f, 0.25f, 2.4f), lHandPos, "gate3_13a_left_hand_open.png", false, null, 0f, true);
        RenderShot(null, 0f, rHandPos + new Vector3(2.6f, 0.25f, 2.4f), rHandPos, "gate3_13b_right_hand_open.png", false, null, 0f, true);
        RenderShot(null, 0f, lHandPos + new Vector3(-2.6f, 0.25f, 2.4f), lHandPos, "gate3_13c_left_hand_curled.png", false, null, 68f, true);
        RenderShot(null, 0f, rHandPos + new Vector3(2.6f, 0.25f, 2.4f), rHandPos, "gate3_13d_right_hand_curled.png", false, null, 68f, true);

        // Restore pristine unmutated scene state & save Tarn_Inspection.unity
        RestoreInitialPose();
        if (trUm != null) trUm.gameObject.SetActive(false);
        if (trTarn != null) trTarn.gameObject.SetActive(false);
        umSmr00.enabled = true; umSmr01.enabled = false;
        tarnSmr00.enabled = true; tarnSmr01.enabled = false;

        cam.targetTexture = null; RenderTexture.active = null;
        UnityEngine.Object.DestroyImmediate(rt);
        UnityEngine.Object.DestroyImmediate(ss);
        cam.transform.position = new Vector3(0f, 6.2f, 21.0f);
        cam.transform.LookAt(new Vector3(0f, 5.8f, 0f));

        // Clear temporary bundle Avatar refs before saving scene; TarnPreviewController.Start() rebinds at Play
        animUm.avatar = null;
        animTarn.avatar = null;
        if (animTrUm != null) animTrUm.avatar = null;
        if (animTrTarn != null) animTrTarn.avatar = null;

        EditorSceneManager.SaveScene(scene, SCENE_PATH);
        if (procBundle != null) procBundle.Unload(false);
        umBundle.Unload(false);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("=== [Tarn] Gate 3 Scene & Verification Renders Complete! ===");
    }

    static AxisSpec DetectAxisSpec(string fbxPath, SkinnedMeshRenderer umSmr00) {
        GameObject fbx = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
        if (fbx == null) throw new Exception("DetectAxisSpec: Failed to load FBX: " + fbxPath);
        SkinnedMeshRenderer smr = fbx.GetComponentInChildren<SkinnedMeshRenderer>(true);
        if (smr == null || smr.sharedMesh == null) {
            Mesh assetMesh = AssetDatabase.LoadAssetAtPath<Mesh>(fbxPath);
            throw new Exception($"DetectAxisSpec: No SkinnedMeshRenderer in {fbxPath} (fallback Mesh={(assetMesh != null ? assetMesh.name : "null")})");
        }
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
        if (cLH == Vector3.zero) cLH = CentroidOf("LeftHandMiddle1");
        Vector3 cRH = CentroidOf("RightHand");
        Vector3 cToe = CentroidOf("LeftToeBase");
        if (cToe == Vector3.zero) cToe = CentroidOf("LeftFoot");

        // Compare against UltraMagnus_GS_Leader official coords: LeftHand.x < 0 (-2.64), LeftToeBase.z > 0 (+0.596)
        float sx = (cLH.x <= 0f) ? 1f : -1f;
        float toeDepth = zIsHeight ? cToe.y : cToe.z;
        float sz = (toeDepth >= 0f) ? 1f : -1f;
        float det = (zIsHeight ? -1f : 1f) * sx * sz;
        Debug.Log($"[AxisSpec] rawBounds={raw.bounds} cLH={cLH} cRH={cRH} cToe={cToe} -> zIsHeight={zIsHeight}, sx={sx}, sz={sz}, det={det}");
        return new AxisSpec { zIsHeight = zIsHeight, sx = sx, sz = sz, det = det };
    }

    static Mesh BuildGraftedMesh(string fbxPath, SkinnedMeshRenderer umSmr, AxisSpec spec, string meshName, string fallbackBone, string forceSingleBone) {
        GameObject fbx = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
        SkinnedMeshRenderer srcSmr = fbx.GetComponentInChildren<SkinnedMeshRenderer>(true);
        Mesh raw = srcSmr.sharedMesh;

        Vector3[] rv = raw.vertices;
        Vector3[] rn = raw.normals;
        Vector4[] rt = raw.tangents;
        Vector3[] nv = new Vector3[rv.Length];
        Vector3[] nn = new Vector3[rn.Length];
        Vector4[] nt = new Vector4[rt.Length];

        for (int i = 0; i < rv.Length; i++) {
            Vector3 v = rv[i];
            nv[i] = spec.zIsHeight ? new Vector3(spec.sx * v.x, v.z, spec.sz * v.y) : new Vector3(spec.sx * v.x, v.y, spec.sz * v.z);
        }
        for (int i = 0; i < rn.Length; i++) {
            Vector3 n = rn[i];
            nn[i] = (spec.zIsHeight ? new Vector3(spec.sx * n.x, n.z, spec.sz * n.y) : new Vector3(spec.sx * n.x, n.y, spec.sz * n.z)).normalized;
        }
        for (int i = 0; i < rt.Length; i++) {
            Vector4 t = rt[i];
            float tw = (spec.det < 0f) ? -t.w : t.w;
            nt[i] = spec.zIsHeight ? new Vector4(spec.sx * t.x, t.z, spec.sz * t.y, tw) : new Vector4(spec.sx * t.x, t.y, spec.sz * t.z, tw);
        }

        // Outer-shell outward check: verify vertex normals point outward from mesh bounds center
        Bounds tmpB = new Bounds(nv[0], Vector3.zero);
        for (int i = 1; i < nv.Length; i++) tmpB.Encapsulate(nv[i]);
        double outerDot = 0.0;
        for (int i = 0; i < nv.Length; i++) {
            Vector3 d = nv[i] - tmpB.center;
            if (d.sqrMagnitude > 0.25f * tmpB.extents.sqrMagnitude) outerDot += Vector3.Dot(d.normalized, nn[i]);
        }
        if (outerDot < 0.0) {
            Debug.LogWarning($"[NormalGuard] {meshName} outerDot={outerDot:F1} < 0! Flipping vertex normals.");
            for (int i = 0; i < nn.Length; i++) nn[i] = -nn[i];
        }

        // Map bones to exact UM SMR bone indices
        Transform[] umBones = umSmr.bones;
        Dictionary<string, int> umMap = new Dictionary<string, int>();
        for (int i = 0; i < umBones.Length; i++) if (umBones[i] != null) umMap[umBones[i].name] = i;
        int fbIdx = umMap.ContainsKey(fallbackBone) ? umMap[fallbackBone] : 0;

        int[] remap = new int[srcSmr.bones.Length];
        int matched = 0;
        for (int j = 0; j < srcSmr.bones.Length; j++) {
            string bn = srcSmr.bones[j] != null ? srcSmr.bones[j].name : "";
            if (umMap.TryGetValue(bn, out int idx)) { remap[j] = idx; matched++; }
            else remap[j] = fbIdx;
        }

        BoneWeight[] origBw = raw.boneWeights;
        BoneWeight[] newBw = new BoneWeight[rv.Length];
        if (!string.IsNullOrEmpty(forceSingleBone) && umMap.TryGetValue(forceSingleBone, out int forcedIdx)) {
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
        if (nt.Length == nv.Length) outMesh.tangents = nt;
        outMesh.uv = raw.uv;
        outMesh.boneWeights = newBw;
        outMesh.bindposes = umSmr.sharedMesh.bindposes;

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
            double avgDot = triCount > 0 ? Mathf.Abs((float)dotSum) / triCount : 0.0;
            Debug.Log($"[BuildGraftedMesh] {meshName} matched={matched}/{srcSmr.bones.Length} outerDot={outerDot:F1} rawFnVn={(triCount > 0 ? dotSum / triCount : 0):F3} -> flipped={(dotSum < 0.0)} verifiedAvgFnVn={avgDot:F3}");
            outMesh.SetTriangles(tris, s);
        }
        outMesh.RecalculateBounds();
        Debug.Log($"[BuildGraftedMesh] {meshName} verts={outMesh.vertexCount} boundsCenter={outMesh.bounds.center:F3} size={outMesh.bounds.size:F3}");
        return outMesh;
    }

    static void VerifyFingerJointAlignment(string fbxPath, SkinnedMeshRenderer umSmr00, AxisSpec spec) {
        GameObject fbx = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
        SkinnedMeshRenderer srcSmr = fbx.GetComponentInChildren<SkinnedMeshRenderer>(true);
        Dictionary<string, Transform> fbxBones = new Dictionary<string, Transform>();
        foreach (var b in srcSmr.bones) if (b != null) fbxBones[b.name] = b;

        Transform[] umBones = umSmr00.bones;
        Matrix4x4[] umBps = umSmr00.sharedMesh.bindposes;
        float maxErrMm = 0f;
        int checkedCount = 0;
        for (int i = 0; i < umBones.Length && i < umBps.Length; i++) {
            string bn = umBones[i].name;
            string bl = bn.ToLower();
            if (!(bl.Contains("thumb") || bl.Contains("index") || bl.Contains("middle") || bl.Contains("ring") || bl.Contains("pinky"))) continue;
            if (!fbxBones.TryGetValue(bn, out Transform fb)) continue;
            // Compare FBX bone head local position against UM bindpose pos
            Vector3 fp = fb.position;
            Vector3 fUnity = spec.zIsHeight ? new Vector3(spec.sx * fp.x, fp.z, spec.sz * fp.y) : new Vector3(spec.sx * fp.x, fp.y, spec.sz * fp.z);
            Vector3 umPos = (umSmr00.transform.localToWorldMatrix * umBps[i].inverse).MultiplyPoint3x4(Vector3.zero);
            float errMm = Vector3.Distance(fUnity, umPos) * 1000f;
            if (errMm > maxErrMm) maxErrMm = errMm;
            checkedCount++;
        }
        Debug.Log($"[FingerAudit] Checked {checkedCount}/30 finger bones against UM BindPose: maxPosDelta={maxErrMm:F3} mm");
    }

    static string AuditVehicleBonesAndClips(
            GameObject umInst, SkinnedMeshRenderer umSmr01, Animator animUm, Animator animTrUm, Transform trUm,
            Dictionary<string, AnimationClip> allClips, Action restoreFn,
            out string chosenVehRoot, out string chosenVehTrans, out float chosenVehT) {
        string[] candClips = {
            "frontend_Ultramagnus_gs_levelup_vehicle_idle_transformed",
            "frontend_Ultramagnus_gs_levelup_vehicle_idle_transformed",
            "BattleIntro_Trucks_ultramagnus_transformed",
            "UltraMagnus_Normal_attackHeavy_transformed",
            "UltraMagnus_gs_attackSpecial_03_transformed",
            "UltraMagnus_gs_attackSpecial_03_transformed",
            "UltraMagnus_gs_attackSpecial_03_transformed",
            "UltraMagnus_gs_attackSpecial_03_transformed",
            "UltraMagnus_gs_attackSpecial_03_transformed"
        };
        string[] rootPairs = {
            null,
            "frontend_Agile_Mirage_levelup_vehicle_idle",
            "BattleIntro_Trucks",
            "UltraMagnus_Normal_attackHeavy",
            "UltraMagnus_gs_attackSpecial_03",
            "UltraMagnus_gs_attackSpecial_03",
            "UltraMagnus_gs_attackSpecial_03",
            "UltraMagnus_gs_attackSpecial_03",
            "UltraMagnus_gs_attackSpecial_03"
        };
        float[] sampleTimes = { 0.0f, 0.25f, 0.25f, 0.45f, 1.50f, 2.50f, 3.50f, 4.50f, 5.50f };

        string[] candBones = { "BodyBase", "Trailer", "chop1_torso_center", "chop1_torso_hidden", "chop2_hip_center", "chop2_head_center", "chop1_backpack_main_center", "COG" };
        Transform[] bones01 = umSmr01.bones;
        Matrix4x4[] bps01 = umSmr01.sharedMesh.bindposes;
        Dictionary<string, int> bIdxMap = new Dictionary<string, int>();
        for (int i = 0; i < bones01.Length; i++) if (bones01[i] != null) bIdxMap[bones01[i].name] = i;

        chosenVehRoot = null;
        chosenVehTrans = "frontend_Ultramagnus_gs_levelup_vehicle_idle_transformed";
        chosenVehT = 0f;
        string bestBone = "chop1_torso_center";
        float bestClipScore = -999f;

        if (trUm != null) trUm.gameObject.SetActive(true);
        umSmr01.enabled = true;

        for (int ci = 0; ci < candClips.Length; ci++) {
            string tClip = candClips[ci];
            string rClip = rootPairs[ci];
            if (!allClips.TryGetValue(tClip, out AnimationClip tc)) continue;
            float t = Mathf.Min(sampleTimes[ci], Mathf.Max(0f, tc.length * 0.5f));
            restoreFn();
            if (rClip != null && allClips.TryGetValue(rClip, out AnimationClip rc)) EvalSingleGraph(animUm, rc, t);
            if (animTrUm != null) EvalSingleGraph(animTrUm, tc, t);

            // Check official UM truck world bounds
            Mesh bm = new Mesh();
            umSmr01.BakeMesh(bm, true);
            GameObject tgo = new GameObject("TempUmTruckAudit");
            tgo.transform.SetPositionAndRotation(umSmr01.transform.position, umSmr01.transform.rotation);
            tgo.AddComponent<MeshFilter>().sharedMesh = bm;
            var mr = tgo.AddComponent<MeshRenderer>();
            Bounds wb = mr.bounds;
            Debug.Log($"[VehClipAudit] clip='{tClip}' (root='{rClip ?? "REST"}', t={t:F2}s, len={tc.length:F2}s) UM01 worldCenter={wb.center:F2} worldSize={wb.size:F2}");
            UnityEngine.Object.DestroyImmediate(tgo);
            UnityEngine.Object.DestroyImmediate(bm);

            foreach (string bn in candBones) {
                Transform trNode = bIdxMap.TryGetValue(bn, out int bi) ? bones01[bi] : FindChildRecursive(umInst.transform, bn);
                if (trNode == null) continue;
                Matrix4x4 mRel = umInst.transform.worldToLocalMatrix * trNode.localToWorldMatrix * (bIdxMap.ContainsKey(bn) ? bps01[bi] : Matrix4x4.identity);
                Vector3 up = mRel.MultiplyVector(Vector3.up);
                Vector3 fwd = mRel.MultiplyVector(Vector3.forward);
                Vector3 scl = new Vector3(
                    mRel.GetColumn(0).magnitude,
                    mRel.GetColumn(1).magnitude,
                    mRel.GetColumn(2).magnitude
                );
                float score = up.y + fwd.z - Mathf.Abs(scl.x - 1f) - Mathf.Abs(scl.y - 1f) - Mathf.Abs(scl.z - 1f);
                Debug.Log($"   [VehBoneAudit] {bn,-28} up={up:F2} fwd={fwd:F2} scl={scl:F2} score={score:F2}");
                // Prefer clips where UM truck is horizontally grounded (size.z > size.y) & bone up/fwd aligned
                if (wb.size.z > wb.size.y * 1.1f && up.y > 0.85f && score > bestClipScore) {
                    bestClipScore = score;
                    bestBone = bn;
                    chosenVehRoot = rClip;
                    chosenVehTrans = tClip;
                    chosenVehT = t;
                }
            }
        }
        restoreFn();
        Debug.Log($"[VehBoneWinner] clip='{chosenVehTrans}' root='{chosenVehRoot ?? "REST"}' t={chosenVehT:F2}s bestBone='{bestBone}' (inBps01={bIdxMap.ContainsKey(bestBone)})");
        if (!bIdxMap.ContainsKey(bestBone)) bestBone = "chop1_torso_center";
        return bestBone;
    }

    static float FindPeakForwardHandTime(GameObject inst, Animator anim, Dictionary<string, AnimationClip> clips, string clipName, Action restoreFn, float fallbackT) {
        if (!clips.TryGetValue(clipName, out AnimationClip c)) return fallbackT;
        Transform hips = FindChildRecursive(inst.transform, "Hips");
        Transform rh = FindChildRecursive(inst.transform, "RightHand");
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
        Debug.Log($"[PeakPose] '{clipName}' len={c.length:F2}s -> bestT={bestT:F2}s (dz={bestZ:F2})");
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
        p.SetApplyFootIK(false);
        p.SetTime(t);
        o.SetSourcePlayable(p);
        g.Play();
        g.Evaluate(0f);
        g.Destroy();
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
        g.Play();
        g.Evaluate(0f);
        g.Destroy();
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
                m.SetColor("_EmissionColor", Color.white * 1.15f);
            }
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
        if (parent.name == name) return parent;
        for (int i = 0; i < parent.childCount; i++) {
            Transform f = FindChildRecursive(parent.GetChild(i), name);
            if (f != null) return f;
        }
        return null;
    }
}
