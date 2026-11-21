using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;
using UnityEngine.SceneManagement;

public static class BuildSwoopInspectionScene {
    private const string RAMJET_BUNDLE_PATH = @"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle";
    private const string PROC_BUNDLE_PATH = @"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle";
    private const string RENDERS_DIR = @"E:\Agent\TFTF-blender\renders\swoop";

    private const string ROBOT_FBX = "Assets/Swoop/swoop_prepared.fbx";
    private const string VH_FBX = "Assets/Swoop/swoop_vh_prepared.fbx";
    private const string ROBOT_ASSET = "Assets/Swoop/cha_swoop_gs_00.asset";
    private const string VH_ASSET = "Assets/Swoop/cha_swoop_gs_01.asset";
    private const string SCENE_PATH = "Assets/Scenes/Swoop_Inspection.unity";

    struct AxisSpec {
        public bool zIsHeight;
        public float sx;
        public float sz;
        public float det;
    }

    [Serializable]
    private class FlapKey {
        public int frame;
        public float time;
        public float px, py, pz;
        public float rx, ry, rz, rw;
    }

    [Serializable]
    private class FlapTrack {
        public string bone;
        public FlapKey[] keys;
    }

    [Serializable]
    private class FlapClipJson {
        public string clip_name;
        public float fps;
        public int frame_count;
        public float duration;
        public FlapTrack[] tracks;
    }

    private static AnimationClip BuildSwoopWingFlapClip() {
        string jsonPath = Path.Combine(Application.dataPath, "Swoop/swoop_native_wing_flap_58frames.json");
        if (!File.Exists(jsonPath)) {
            Debug.LogWarning("[WingFlap] Missing JSON: " + jsonPath);
            return null;
        }
        FlapClipJson data = JsonUtility.FromJson<FlapClipJson>(File.ReadAllText(jsonPath));
        if (data == null || data.tracks == null) return null;

        string animAssetPath = "Assets/Swoop/Swoop_Vehicle_WingFlap_transformed.anim";
        AnimationClip clip = AssetDatabase.LoadAssetAtPath<AnimationClip>(animAssetPath);
        if (clip == null) {
            clip = new AnimationClip { name = "Swoop_Vehicle_WingFlap_transformed", frameRate = 30f };
            AssetDatabase.CreateAsset(clip, animAssetPath);
        } else {
            clip.ClearCurves();
            clip.name = "Swoop_Vehicle_WingFlap_transformed";
            clip.frameRate = 30f;
        }

        foreach (var trk in data.tracks) {
            if (trk.keys == null || trk.keys.Length == 0) continue;
            string relPath = "Reference/COG/" + trk.bone;
            AnimationCurve cx = new AnimationCurve(), cy = new AnimationCurve(), cz = new AnimationCurve();
            AnimationCurve qx = new AnimationCurve(), qy = new AnimationCurve(), qz = new AnimationCurve(), qw = new AnimationCurve();
            foreach (var k in trk.keys) {
                cx.AddKey(k.time, k.px);
                cy.AddKey(k.time, k.py);
                cz.AddKey(k.time, k.pz);
                qx.AddKey(k.time, k.rx);
                qy.AddKey(k.time, k.ry);
                qz.AddKey(k.time, k.rz);
                qw.AddKey(k.time, k.rw);
            }
            clip.SetCurve(relPath, typeof(Transform), "localPosition.x", cx);
            clip.SetCurve(relPath, typeof(Transform), "localPosition.y", cy);
            clip.SetCurve(relPath, typeof(Transform), "localPosition.z", cz);
            clip.SetCurve(relPath, typeof(Transform), "localRotation.x", qx);
            clip.SetCurve(relPath, typeof(Transform), "localRotation.y", qy);
            clip.SetCurve(relPath, typeof(Transform), "localRotation.z", qz);
            clip.SetCurve(relPath, typeof(Transform), "localRotation.w", qw);
        }
        clip.EnsureQuaternionContinuity();
        AnimationClipSettings settings = AnimationUtility.GetAnimationClipSettings(clip);
        settings.loopTime = true;
        AnimationUtility.SetAnimationClipSettings(clip, settings);
        EditorUtility.SetDirty(clip);
        Debug.Log($"[✓] Built native 58-frame Swoop Wing-Flap AnimationClip ({data.tracks.Length} tracks, {data.duration:F2}s): {animAssetPath}");
        return clip;
    }

    [MenuItem("TFTF/Build Swoop vs Ramjet Inspection Scene")]
    public static void Build() {
        Debug.Log("=== [Swoop] Gate 3 Authoritative Side-by-Side Inspection Scene (Donor: Ramjet GS Deluxe 2008) ===");
        Directory.CreateDirectory(RENDERS_DIR);
        Directory.CreateDirectory(Path.Combine(Application.dataPath, "Swoop/Ramjet"));
        Directory.CreateDirectory(Path.Combine(Application.dataPath, "Scenes"));

        AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);

        // 1. Configure Normal Maps & FBX ModelImporters
        string[] normPaths = {
            "Assets/Swoop/Textures/cha_swoop_main_Normal_unity.png",
            "Assets/Swoop/Textures/cha_swoop_vh_Normal_unity.png",
            "Assets/Swoop/Ramjet/main_NM.png",
            "Assets/Swoop/Ramjet/wpns_NM.png",
            "Assets/Swoop/Ramjet/tform_misc_NM.png",
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

        // 2. Load Ramjet Donor Bundle & Procedural Animations
        foreach (var b in AssetBundle.GetAllLoadedAssetBundles()) b.Unload(false);
        AssetBundle ramjetBundle = AssetBundle.LoadFromFile(RAMJET_BUNDLE_PATH);
        if (ramjetBundle == null) {
            Debug.LogError("[Swoop] Missing Ramjet donor bundle: " + RAMJET_BUNDLE_PATH);
            if (Application.isBatchMode) EditorApplication.Exit(1);
            return;
        }
        AssetBundle procBundle = File.Exists(PROC_BUNDLE_PATH) ? AssetBundle.LoadFromFile(PROC_BUNDLE_PATH) : null;

        GameObject ramjetPrefab = ramjetBundle.LoadAsset<GameObject>("assets/bundles/characters/merged/ramjet_gs_deluxe2008/ramjet_gs_deluxe2008.prefab");
        if (ramjetPrefab == null) {
            foreach (var g in ramjetBundle.LoadAllAssets<GameObject>()) {
                if (g.name.ToLower().Contains("ramjet_gs_deluxe2008") && !g.name.ToLower().Contains("_lw")) {
                    ramjetPrefab = g; break;
                }
            }
        }
        if (ramjetPrefab == null) {
            Debug.LogError("[Swoop] Missing Ramjet prefab!");
            if (Application.isBatchMode) EditorApplication.Exit(1);
            return;
        }

        SkinnedMeshRenderer ramjetSmr00 = null, ramjetSmr01 = null;
        foreach (var smr in ramjetPrefab.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name == "cha_ramjet_gs_deluxe2008_00") ramjetSmr00 = smr;
            else if (smr.name == "cha_ramjet_gs_deluxe2008_01") ramjetSmr01 = smr;
        }
        if (ramjetSmr00 == null || ramjetSmr01 == null) {
            Debug.LogError("[Swoop] Missing _00 or _01 SMR on Ramjet prefab!");
            if (Application.isBatchMode) EditorApplication.Exit(1);
            return;
        }

        Mesh ramjetSaved00 = SaveClonedMesh(ramjetSmr00.sharedMesh, "cha_ramjet_official_00", "Assets/Swoop/Ramjet/cha_ramjet_official_00.asset");
        Mesh ramjetSaved01 = SaveClonedMesh(ramjetSmr01.sharedMesh, "cha_ramjet_official_01", "Assets/Swoop/Ramjet/cha_ramjet_official_01.asset");

        Avatar officialAvatar00 = ramjetPrefab.GetComponent<Animator>() != null ? ramjetPrefab.GetComponent<Animator>().avatar : null;
        Transform prefabTr = FindChildRecursive(ramjetPrefab.transform, "transformed");
        Avatar officialAvatar01 = (prefabTr != null && prefabTr.GetComponent<Animator>() != null) ? prefabTr.GetComponent<Animator>().avatar : null;
        Debug.Log($"[Avatars] avatar00={(officialAvatar00 != null ? officialAvatar00.name : "NULL")} | avatar01={(officialAvatar01 != null ? officialAvatar01.name : "NULL")}");

        // 3. Build Grafted Meshes
        AxisSpec spec = DetectAxisSpec(ROBOT_FBX, ramjetSmr00);
        Mesh graftedRobot = BuildGraftedMesh(ROBOT_FBX, ramjetSmr00, spec, "cha_swoop_gs_00", "Spine1", null);
        SaveOrReplaceMeshAsset(graftedRobot, ROBOT_ASSET);
        Mesh savedRobot00 = AssetDatabase.LoadAssetAtPath<Mesh>(ROBOT_ASSET);

        VerifyLeftFingerJointAlignment(ROBOT_FBX, ramjetSmr00, spec);

        Mesh graftedVh = BuildGraftedMesh(VH_FBX, ramjetSmr01, spec, "cha_swoop_gs_01", "chop1_chest_center", null);
        SaveOrReplaceMeshAsset(graftedVh, VH_ASSET);
        Mesh savedVh01 = AssetDatabase.LoadAssetAtPath<Mesh>(VH_ASSET);

        // 4. Create Preview Materials
        Material matRamjetMain = CreateOrUpdateMat("Assets/Swoop/Ramjet/M_Ramjet_Main.mat",
            "Assets/Swoop/Ramjet/cha_ramjet_gs_deluxe2008_main_a.png",
            "Assets/Swoop/Ramjet/main_NM.png", null, 0.45f, 0.25f, Vector2.one, Vector2.zero);
        Material matRamjetWpns = CreateOrUpdateMat("Assets/Swoop/Ramjet/M_Ramjet_Wpns.mat",
            "Assets/Swoop/Ramjet/cha_ramjet_gs_deluxe2008_wpns_a.png",
            "Assets/Swoop/Ramjet/wpns_NM.png", null, 0.45f, 0.30f, Vector2.one, Vector2.zero);
        Material matRamjetMisc = CreateOrUpdateMat("Assets/Swoop/Ramjet/M_Ramjet_Misc.mat",
            "Assets/Swoop/Ramjet/tform_misc_A.png",
            "Assets/Swoop/Ramjet/tform_misc_NM.png", null, 0.40f, 0.25f, Vector2.one, Vector2.zero);

        Material matSwoopMain = CreateOrUpdateMat("Assets/Swoop/M_Swoop_Main.mat",
            "Assets/Swoop/Textures/cha_swoop_main_Diffuse.png",
            "Assets/Swoop/Textures/cha_swoop_main_Normal_unity.png",
            "Assets/Swoop/Textures/cha_swoop_main_Emission.png", 0.55f, 0.25f, Vector2.one, Vector2.zero);
        Material matSwoopEmblem = CreateOrUpdateMat("Assets/Swoop/M_Swoop_Emblem.mat",
            "Assets/Swoop/Textures/cha_swoop_main_Diffuse.png",
            "Assets/Swoop/Textures/cha_swoop_main_Normal_unity.png",
            "Assets/Swoop/Textures/cha_swoop_main_Emission.png", 0.60f, 0.05f, Vector2.one, Vector2.zero);
        Material matSwoopVh = CreateOrUpdateMat("Assets/Swoop/M_Swoop_Vh.mat",
            "Assets/Swoop/Textures/cha_swoop_vh_Diffuse.png",
            "Assets/Swoop/Textures/cha_swoop_vh_Normal_unity.png",
            "Assets/Swoop/Textures/cha_swoop_vh_Emission.png", 0.55f, 0.25f, Vector2.one, Vector2.zero);

        // 5. Build Side-by-Side Scene
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

        // Left of Screen (+X): Ramjet Official Reference at X = +4.4
        GameObject ramjetInst = UnityEngine.Object.Instantiate(ramjetPrefab);
        ramjetInst.name = "Ramjet_Official_Reference";
        ramjetInst.transform.SetPositionAndRotation(new Vector3(4.4f, 0f, 0f), Quaternion.identity);
        SkinnedMeshRenderer ramjetActiveSmr00 = null, ramjetActiveSmr01 = null;
        foreach (var smr in ramjetInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name == "cha_ramjet_gs_deluxe2008_00") {
                smr.sharedMesh = ramjetSaved00;
                smr.sharedMaterials = new[] { matRamjetMain, matRamjetWpns };
                smr.updateWhenOffscreen = true;
                smr.enabled = true;
                ramjetActiveSmr00 = smr;
            } else if (smr.name == "cha_ramjet_gs_deluxe2008_01") {
                smr.sharedMesh = ramjetSaved01;
                smr.sharedMaterials = new[] { matRamjetMisc };
                smr.updateWhenOffscreen = true;
                smr.enabled = false;
                ramjetActiveSmr01 = smr;
            } else {
                smr.enabled = false;
            }
        }

        // Right of Screen (-X): Swoop Candidate at X = -4.4
        GameObject swoopInst = UnityEngine.Object.Instantiate(ramjetPrefab);
        swoopInst.name = "Swoop_Candidate";
        swoopInst.transform.SetPositionAndRotation(new Vector3(-4.4f, 0f, 0f), Quaternion.identity);
        SkinnedMeshRenderer swoopSmr00 = null, swoopSmr01 = null;
        foreach (var smr in swoopInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name == "cha_ramjet_gs_deluxe2008_00") {
                smr.gameObject.name = "cha_swoop_gs_00";
                smr.sharedMesh = savedRobot00;
                smr.sharedMaterials = (savedRobot00.subMeshCount >= 2) ? new[] { matSwoopMain, matSwoopEmblem } : new[] { matSwoopMain };
                smr.updateWhenOffscreen = true;
                smr.enabled = true;
                swoopSmr00 = smr;
            } else if (smr.name == "cha_ramjet_gs_deluxe2008_01") {
                smr.gameObject.name = "cha_swoop_gs_01";
                smr.sharedMesh = savedVh01;
                smr.sharedMaterials = new[] { matSwoopVh };
                smr.updateWhenOffscreen = true;
                smr.enabled = false;
                swoopSmr01 = smr;
            } else {
                smr.enabled = false;
                smr.sharedMesh = null;
                smr.gameObject.SetActive(false);
            }
        }

        // Disable all extraneous MeshRenderers on Swoop so donor Ramjet weapon attachments don't leak into Swoop
        foreach (var mr in swoopInst.GetComponentsInChildren<MeshRenderer>(true)) {
            mr.enabled = false;
            mr.gameObject.SetActive(false);
        }

        foreach (var t in ramjetInst.GetComponentsInChildren<Transform>(true)) GameObjectUtility.RemoveMonoBehavioursWithMissingScript(t.gameObject);
        foreach (var t in swoopInst.GetComponentsInChildren<Transform>(true)) GameObjectUtility.RemoveMonoBehavioursWithMissingScript(t.gameObject);

        Animator animRamjet = ramjetInst.GetComponent<Animator>();
        Animator animSwoop = swoopInst.GetComponent<Animator>();
        if (officialAvatar00 != null) { animRamjet.avatar = officialAvatar00; animSwoop.avatar = officialAvatar00; }
        animRamjet.cullingMode = AnimatorCullingMode.AlwaysAnimate;
        animSwoop.cullingMode = AnimatorCullingMode.AlwaysAnimate;
        animRamjet.applyRootMotion = false;
        animSwoop.applyRootMotion = false;

        Transform trRamjet = FindChildRecursive(ramjetInst.transform, "transformed");
        Transform trSwoop = FindChildRecursive(swoopInst.transform, "transformed");
        Transform refSwoop = trSwoop != null ? trSwoop.Find("Reference") : null;
        if (refSwoop != null) {
            refSwoop.localScale = new Vector3(1.53f, 1.53f, 1.53f);
            Debug.Log("[Scale] Set Swoop transformed/Reference localScale = (1.53, 1.53, 1.53) to match Robot missile pod length!");
        }
        Animator animTrRamjet = trRamjet != null ? (trRamjet.GetComponent<Animator>() ?? trRamjet.gameObject.AddComponent<Animator>()) : null;
        Animator animTrSwoop = trSwoop != null ? (trSwoop.GetComponent<Animator>() ?? trSwoop.gameObject.AddComponent<Animator>()) : null;
        if (officialAvatar01 != null) {
            if (animTrRamjet != null) { animTrRamjet.avatar = officialAvatar01; animTrRamjet.cullingMode = AnimatorCullingMode.AlwaysAnimate; animTrRamjet.applyRootMotion = false; }
            if (animTrSwoop != null) { animTrSwoop.avatar = officialAvatar01; animTrSwoop.cullingMode = AnimatorCullingMode.AlwaysAnimate; animTrSwoop.applyRootMotion = false; }
        }

        var fingerTester = swoopInst.GetComponent<SwoopFingerTester>() ?? swoopInst.AddComponent<SwoopFingerTester>();
        fingerTester.leftHandAxis = SwoopFingerTester.CurlAxis.Forward_Z;
        fingerTester.autoWiggle = false;
        fingerTester.InitializeBones();

        AnimationClip wingFlapClip = BuildSwoopWingFlapClip();

        GameObject ctrlGo = new GameObject("SwoopPreviewController");
        var ctrl = ctrlGo.AddComponent<SwoopPreviewController>();
        ctrl.animOfficialRamjet = animRamjet;
        ctrl.animSwoop = animSwoop;
        ctrl.swoopWingFlapClip = wingFlapClip;

        // Collect AnimationClips
        Dictionary<string, AnimationClip> allClips = new Dictionary<string, AnimationClip>();
        if (wingFlapClip != null) allClips[wingFlapClip.name] = wingFlapClip;
        CollectClipsFromGo(ramjetPrefab, allClips);
        foreach (var c in ramjetBundle.LoadAllAssets<AnimationClip>()) if (c != null && !allClips.ContainsKey(c.name)) allClips[c.name] = c;
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
        foreach (var t in ramjetInst.GetComponentsInChildren<Transform>(true)) { initPos[t] = t.localPosition; initRot[t] = t.localRotation; initScl[t] = t.localScale; }
        foreach (var t in swoopInst.GetComponentsInChildren<Transform>(true)) { initPos[t] = t.localPosition; initRot[t] = t.localRotation; initScl[t] = t.localScale; }

        void RestoreInitialPose() {
            foreach (var kv in initPos) {
                if (kv.Key != null) {
                    kv.Key.localPosition = kv.Value;
                    kv.Key.localRotation = initRot[kv.Key];
                    kv.Key.localScale = initScl[kv.Key];
                }
            }
            ramjetInst.transform.SetPositionAndRotation(new Vector3(4.4f, 0f, 0f), Quaternion.identity);
            swoopInst.transform.SetPositionAndRotation(new Vector3(-4.4f, 0f, 0f), Quaternion.identity);
        }

        // 6. Render Synchronized Action Screenshots (CPU BakeMesh + PlayableGraph!)
        int w = 1920, h = 1080;
        RenderTexture rt = new RenderTexture(w, h, 24, RenderTextureFormat.ARGB32) { antiAliasing = 8 };
        Texture2D ss = new Texture2D(w, h, TextureFormat.RGB24, false);
        Transform hipsRamjet = FindChildRecursive(ramjetInst.transform, "Hips");
        Transform hipsSwoop = FindChildRecursive(swoopInst.transform, "Hips");

        void RenderPoseShot(string clipName, float sampleTime, Vector3 camPos, Vector3 lookTarget, string fileName,
                            bool vehicleMode = false, string transClipName = null, float curlAngle = 0f, bool hideRamjet = false) {
            RestoreInitialPose();

            if (trRamjet != null) trRamjet.gameObject.SetActive(vehicleMode);
            if (trSwoop != null) trSwoop.gameObject.SetActive(vehicleMode);
            ramjetActiveSmr00.enabled = !vehicleMode && !hideRamjet;
            ramjetActiveSmr01.gameObject.SetActive(vehicleMode);
            ramjetActiveSmr01.enabled = vehicleMode && !hideRamjet;
            swoopSmr00.enabled = !vehicleMode;
            swoopSmr01.gameObject.SetActive(vehicleMode);
            swoopSmr01.enabled = vehicleMode;

            if (clipName != null && allClips.TryGetValue(clipName, out AnimationClip c)) {
                EvalPairGraph(animRamjet, animSwoop, c, sampleTime);
            } else if (clipName != null) {
                Debug.LogWarning($"[Shot {fileName}] Missing root clip '{clipName}'");
            }
            if (vehicleMode && transClipName != null && allClips.TryGetValue(transClipName, out AnimationClip tc)) {
                if (transClipName == "Swoop_Vehicle_WingFlap_transformed" && trSwoop != null) {
                    tc.SampleAnimation(trSwoop.gameObject, sampleTime);
                } else if (animTrRamjet != null && animTrSwoop != null) {
                    EvalPairGraph(animTrRamjet, animTrSwoop, tc, sampleTime);
                }
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

            float spacing = vehicleMode ? 5.8f : 4.4f;
            if (hideRamjet) {
                swoopInst.transform.position = Vector3.zero;
            } else if (!vehicleMode && hipsRamjet != null && hipsSwoop != null) {
                Vector3 dM = hipsRamjet.position - ramjetInst.transform.position;
                ramjetInst.transform.position = new Vector3(spacing - dM.x, 0f, -dM.z);
                Vector3 dB = hipsSwoop.position - swoopInst.transform.position;
                swoopInst.transform.position = new Vector3(-spacing - dB.x, 0f, -dB.z);
            }

            SkinnedMeshRenderer[] activeSmrs = vehicleMode
                ? (hideRamjet ? new[] { swoopSmr01 } : new[] { ramjetActiveSmr01, swoopSmr01 })
                : (hideRamjet ? new[] { swoopSmr00 } : new[] { ramjetActiveSmr00, swoopSmr00 });

            List<GameObject> tempGos = new List<GameObject>();
            List<Mesh> tempMeshes = new List<Mesh>();
            for (int idx = 0; idx < activeSmrs.Length; idx++) {
                var smr = activeSmrs[idx];
                if (smr == null) continue;
                Mesh bm = new Mesh();
                smr.BakeMesh(bm, true);
                bm.RecalculateBounds();
                GameObject bgo = new GameObject("TempBaked_" + smr.name);
                // In pure vehicle showcase (clipName == null), anchor centered on ground; when testing live Fighter+Prop clip (clipName != null), use live world transform!
                bool liveWorldPose = (vehicleMode && clipName != null);
                bgo.transform.SetPositionAndRotation(
                    (vehicleMode && !liveWorldPose) ? Vector3.zero : smr.transform.position,
                    (vehicleMode && !liveWorldPose) ? Quaternion.identity : smr.transform.rotation
                );
                bgo.transform.localScale = Vector3.one;
                bgo.AddComponent<MeshFilter>().sharedMesh = bm;
                var mr = bgo.AddComponent<MeshRenderer>();
                mr.sharedMaterials = smr.sharedMaterials;
                tempGos.Add(bgo);
                tempMeshes.Add(bm);
                smr.enabled = false;

                if (liveWorldPose) {
                    Debug.Log($"[HeavyPose '{fileName}'] {smr.name} smrPos={smr.transform.position:F2} smrEuler={smr.transform.rotation.eulerAngles:F1} worldBoundsCenter={mr.bounds.center:F2} size={mr.bounds.size:F2}");
                    if (smr == swoopSmr01) {
                        Vector3[] bvs = bm.vertices;
                        Vector3 rootOrigin = swoopInst.transform.position;
                        float maxRelZ = -999f;
                        Vector3 beakTipRel = Vector3.zero;
                        foreach (Vector3 lv in bvs) {
                            Vector3 rv = bgo.transform.TransformPoint(lv) - rootOrigin;
                            if (Mathf.Abs(rv.x) < 0.35f && rv.z > maxRelZ) {
                                maxRelZ = rv.z;
                                beakTipRel = rv;
                            }
                        }
                        Vector3 mouthSum = Vector3.zero; int mcnt = 0;
                        foreach (Vector3 lv in bvs) {
                            Vector3 rv = bgo.transform.TransformPoint(lv) - rootOrigin;
                            if (Mathf.Abs(rv.x) < 0.25f && rv.z >= maxRelZ - 1.4f && rv.z <= maxRelZ - 0.1f) {
                                mouthSum += rv; mcnt++;
                            }
                        }
                        Vector3 mouthRel = mcnt > 0 ? mouthSum / mcnt : beakTipRel;
                        Debug.Log($"[BeakMouth '{fileName}' t={sampleTime:F3}s] beakTipRel={beakTipRel:F2} mouthRel={mouthRel:F2}");
                    }
                } else if (vehicleMode) {
                    // Use rest sharedMesh bounds to anchor body X/Y/Z steadily so wing-flapping moves wings relative to stationary body
                    Bounds refB = smr.sharedMesh != null ? smr.sharedMesh.bounds : mr.bounds;
                    float targetX = (!hideRamjet && idx == 0) ? spacing : -spacing;
                    bgo.transform.position = new Vector3(targetX - refB.center.x, -refB.min.y, -refB.center.z);
                }
            }

            if (hideRamjet && lookTarget == Vector3.zero) {
                Transform lHandTrCurrent = FindChildRecursive(swoopInst.transform, "LeftHand");
                if (lHandTrCurrent != null) {
                    lookTarget = lHandTrCurrent.position + new Vector3(0f, -0.35f, 0f);
                    camPos = lookTarget + new Vector3(-0.9f, 0.1f, 1.8f);
                }
            }

            cam.transform.position = camPos;
            cam.transform.LookAt(lookTarget);
            cam.targetTexture = rt;
            cam.Render();
            cam.targetTexture = null;

            RenderTexture.active = rt;
            ss.ReadPixels(new Rect(0, 0, w, h), 0, 0);
            ss.Apply();
            RenderTexture.active = null;

            foreach (var go in tempGos) UnityEngine.Object.DestroyImmediate(go);
            foreach (var m in tempMeshes) UnityEngine.Object.DestroyImmediate(m);
            foreach (var smr in activeSmrs) if (smr != null) smr.enabled = true;

            string outPath = Path.Combine(RENDERS_DIR, fileName);
            File.WriteAllBytes(outPath, ss.EncodeToPNG());
            Debug.Log($"[✓] Saved verification render: {outPath}");
        }

        Vector3 fwdCam = new Vector3(0f, 6.2f, 20.5f);
        Vector3 fwdTarg = new Vector3(0f, 5.6f, 0f);

        // 1. Rest Pose (A-pose)
        RenderPoseShot(null, 0f, fwdCam, fwdTarg, "01_rest_sbs.png");

        // 2. Combat Idle
        RenderPoseShot("Ramjet_G1_CombatIdle", 0.5f, fwdCam, fwdTarg, "02_idle_sbs.png");

        // 3. Showroom 45°
        RenderPoseShot("Ramjet_G1_CombatIdle", 0.5f, new Vector3(-10.5f, 6.2f, 17.5f), fwdTarg, "03_showroom_sbs.png");

        // 4. Back View
        RenderPoseShot("Ramjet_G1_CombatIdle", 0.5f, new Vector3(0f, 6.2f, -20.5f), fwdTarg, "04_back_sbs.png");

        // 5. Light Punch (Jab)
        RenderPoseShot("brawler_normal_attackLight_02_jab", 0.35f, fwdCam, fwdTarg, "05_jab_sbs.png");

        // 6. Heavy Attack (Robot vs Airborne Vehicle Heavy at f=11 (0.367s) & f=12 (0.400s))
        RenderPoseShot("Ramjet_Normal_attackHeavy", 0.45f, fwdCam, fwdTarg, "06_heavy_sbs.png");
        RenderPoseShot("StarScream_Normal_attackHeavy", 0.367f, new Vector3(0f, 8.5f, 24.0f), new Vector3(0f, 8.0f, 0f), "06c_heavy_starscream_t367.png", vehicleMode: true, transClipName: "Swoop_Vehicle_WingFlap_transformed");
        RenderPoseShot("StarScream_Normal_attackHeavy", 0.400f, new Vector3(0f, 8.5f, 24.0f), new Vector3(0f, 8.0f, 0f), "06b_heavy_starscream_vh.png", vehicleMode: true, transClipName: "Swoop_Vehicle_WingFlap_transformed");

        // 7. High Kick
        RenderPoseShot("brawler_normal_attackLight_04_frontkick", 0.38f, fwdCam, fwdTarg, "07_highkick_sbs.png");

        // 8. Victory Pose
        RenderPoseShot("Brawler_Normal_Victory", 1.20f, fwdCam, fwdTarg, "08_victory_sbs.png");

        // 9. Vehicle Mode Side-by-Side (Static Neutral + Native Wing-Flapping Keyframes + 3/4 Side Profile)
        RestoreInitialPose();
        Vector3 vehCam = new Vector3(0f, 8.5f, 21.0f);
        Vector3 vehTarg = new Vector3(0f, 2.2f, 0f);
        RenderPoseShot(null, 0.000f, vehCam, vehTarg, "09_vehicle_sbs.png", vehicleMode: true, transClipName: "Swoop_Vehicle_WingFlap_transformed");
        RenderPoseShot(null, 0.300f, vehCam, vehTarg, "09b_vehicle_flap_up_sbs.png", vehicleMode: true, transClipName: "Swoop_Vehicle_WingFlap_transformed");
        RenderPoseShot(null, 0.733f, vehCam, vehTarg, "09c_vehicle_flap_down_sbs.png", vehicleMode: true, transClipName: "Swoop_Vehicle_WingFlap_transformed");
        RenderPoseShot(null, 0.000f, new Vector3(-13.5f, 6.2f, 15.5f), new Vector3(-2.5f, 2.2f, 0f), "09d_vehicle_side_sbs.png", vehicleMode: true, transClipName: "Swoop_Vehicle_WingFlap_transformed");

        // 10. Left Hand Open vs Curled Close-Up & 11. Face Eyes + 12. Right Hand Close-Up
        RestoreInitialPose();
        RenderPoseShot(null, 0f, Vector3.zero, Vector3.zero, "10_left_hand_open.png", curlAngle: 0f, hideRamjet: true);
        RenderPoseShot(null, 0f, Vector3.zero, Vector3.zero, "10_left_hand_curled.png", curlAngle: 75f, hideRamjet: true);
        RenderPoseShot("Ramjet_G1_CombatIdle", 0.5f, new Vector3(0.4f, 9.2f, 5.2f), new Vector3(0.0f, 8.6f, 0.0f), "11_face_eyes_closeup.png", hideRamjet: true);
        Transform rHandTr = FindChildRecursive(swoopInst.transform, "RightHand");
        if (rHandTr != null) {
            RestoreInitialPose();
            Vector3 rhRel = rHandTr.position - swoopInst.transform.position;
            Vector3 rhLook = rhRel + new Vector3(0f, -0.35f, 0f);
            RenderPoseShot(null, 0f, rhLook + new Vector3(1.1f, 0.1f, 1.8f), rhLook, "12_right_hand_closeup.png", hideRamjet: true);
        }

        UnityEngine.Object.DestroyImmediate(rt);
        UnityEngine.Object.DestroyImmediate(ss);

        EditorSceneManager.SaveScene(scene, SCENE_PATH);
        var ebScenes = new List<EditorBuildSettingsScene> { new EditorBuildSettingsScene(SCENE_PATH, true) };
        EditorBuildSettings.scenes = ebScenes.ToArray();
        Debug.Log("[✓] Saved inspection scene & set EditorBuildSettings.scenes[0]: " + SCENE_PATH);

        if (procBundle != null) procBundle.Unload(false);
        ramjetBundle.Unload(false);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();

        // Pack Android Mesh AssetBundle (swoop_mesh.assetbundle)
        string outAbDir = @"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles";
        Directory.CreateDirectory(outAbDir);
        AssetBundleBuild[] builds = new AssetBundleBuild[1];
        builds[0].assetBundleName = "swoop_mesh.assetbundle";
        builds[0].assetNames = new[] { ROBOT_ASSET, VH_ASSET, "Assets/Swoop/Swoop_Vehicle_WingFlap_transformed.anim" };
        var manifest = BuildPipeline.BuildAssetBundles(
            outAbDir,
            builds,
            BuildAssetBundleOptions.ForceRebuildAssetBundle | BuildAssetBundleOptions.ChunkBasedCompression,
            BuildTarget.Android
        );
        if (manifest != null) {
            Debug.Log("[✓] Successfully packed swoop_mesh.assetbundle!");
        }

        Debug.Log("=== [Swoop] Gate 3 Complete! All Verification Renders Exported! ===");
        if (Application.isBatchMode) EditorApplication.Exit(0);
    }

    static AxisSpec DetectAxisSpec(string fbxPath, SkinnedMeshRenderer refSmr) {
        GameObject fbx = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
        if (fbx == null) throw new Exception("Missing FBX: " + fbxPath);
        SkinnedMeshRenderer smr = fbx.GetComponentInChildren<SkinnedMeshRenderer>(true);
        Mesh raw = smr.sharedMesh;
        // In Blender coordinates, upright character height is always Z in [0, 11.4m]
        bool zIsHeight = raw.bounds.size.z > 5.0f || raw.bounds.size.z > raw.bounds.size.y;

        Vector3 CentroidOf(string boneName) {
            int bi = -1;
            for (int i = 0; i < smr.bones.Length; i++) if (smr.bones[i].name == boneName) { bi = i; break; }
            if (bi < 0) return Vector3.zero;
            Vector3 sum = Vector3.zero; int count = 0;
            Vector3[] v = raw.vertices; BoneWeight[] bw = raw.boneWeights;
            for (int i = 0; i < bw.Length; i++) {
                if ((bw[i].boneIndex0 == bi && bw[i].weight0 > 0.4f) || (bw[i].boneIndex1 == bi && bw[i].weight1 > 0.4f)) {
                    sum += v[i]; count++;
                }
            }
            return count > 0 ? sum / count : Vector3.zero;
        }

        Vector3 cLH = CentroidOf("LeftHand");
        if (cLH == Vector3.zero) cLH = CentroidOf("LeftForeArm");
        if (cLH == Vector3.zero) cLH = CentroidOf("LeftArm");
        Vector3 cRH = CentroidOf("RightHand");
        Vector3 cToe = CentroidOf("LeftToeBase");
        if (cToe == Vector3.zero) cToe = CentroidOf("LeftFoot");
        if (cToe == Vector3.zero) cToe = CentroidOf("LeftLeg");

        // Compare against Ramjet / official coords: LeftHand.x < 0 (-2.326), Forward = Unity +Z (Blender -Y)
        float sx = (cLH.x <= 0f) ? 1f : -1f;
        float sz = zIsHeight ? -sx : ((cToe.z >= 0f) ? 1f : -1f);
        if (cToe != Vector3.zero && !zIsHeight) sz = (cToe.z >= 0f) ? 1f : -1f;
        float det = (zIsHeight ? -1f : 1f) * sx * sz;
        Debug.Log($"[DetectAxisSpec] {fbxPath}: zIsHeight={zIsHeight} cLH={cLH} cRH={cRH} cToe={cToe} -> sx={sx} sz={sz} det={det}");
        return new AxisSpec { zIsHeight = zIsHeight, sx = sx, sz = sz, det = det };
    }

    static Mesh BuildGraftedMesh(string fbxPath, SkinnedMeshRenderer refSmr, AxisSpec spec, string meshName, string fallbackBone, string forceSingleBone) {
        GameObject fbx = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
        if (fbx == null) throw new Exception("Missing FBX: " + fbxPath);
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

        Transform[] refBones = refSmr.bones;
        Dictionary<string, int> refMap = new Dictionary<string, int>();
        for (int i = 0; i < refBones.Length; i++) if (refBones[i] != null) refMap[refBones[i].name] = i;
        int fbIdx = refMap.ContainsKey(fallbackBone) ? refMap[fallbackBone] : 0;

        int[] remap = new int[srcSmr.bones.Length];
        int matched = 0;
        for (int j = 0; j < srcSmr.bones.Length; j++) {
            string bn = srcSmr.bones[j] != null ? srcSmr.bones[j].name : "";
            if (refMap.TryGetValue(bn, out int idx)) { remap[j] = idx; matched++; }
            else remap[j] = fbIdx;
        }

        BoneWeight[] origBw = raw.boneWeights;
        BoneWeight[] newBw = new BoneWeight[rv.Length];
        if (!string.IsNullOrEmpty(forceSingleBone) && refMap.TryGetValue(forceSingleBone, out int forcedIdx)) {
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
        outMesh.bindposes = refSmr.sharedMesh.bindposes;

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

    static void VerifyLeftFingerJointAlignment(string fbxPath, SkinnedMeshRenderer refSmr00, AxisSpec spec) {
        GameObject fbx = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
        SkinnedMeshRenderer srcSmr = fbx.GetComponentInChildren<SkinnedMeshRenderer>(true);

        Transform[] refBones = refSmr00.bones;
        Matrix4x4[] refBps = refSmr00.sharedMesh.bindposes;
        Matrix4x4[] fbxBps = srcSmr.sharedMesh.bindposes;
        Dictionary<string, int> fbxIdxMap = new Dictionary<string, int>();
        for (int j = 0; j < srcSmr.bones.Length; j++) if (srcSmr.bones[j] != null) fbxIdxMap[srcSmr.bones[j].name] = j;

        float maxErrMm = 0f;
        int checkedCount = 0;
        for (int i = 0; i < refBones.Length && i < refBps.Length; i++) {
            string bn = refBones[i].name;
            string bl = bn.ToLower();
            if (!(bl.Contains("thumb") || bl.Contains("index") || bl.Contains("middle") || bl.Contains("ring") || bl.Contains("pinky"))) continue;
            if (!fbxIdxMap.TryGetValue(bn, out int fi) || fi >= fbxBps.Length) continue;
            Vector3 fp = fbxBps[fi].inverse.MultiplyPoint3x4(Vector3.zero);
            Vector3 fUnity = spec.zIsHeight ? new Vector3(spec.sx * fp.x, fp.z, spec.sz * fp.y) : new Vector3(spec.sx * fp.x, fp.y, spec.sz * fp.z);
            Vector3 refPos = refBps[i].inverse.MultiplyPoint3x4(Vector3.zero);
            float errMm = Vector3.Distance(fUnity, refPos) * 1000f;
            if (errMm > maxErrMm) maxErrMm = errMm;
            checkedCount++;
        }
        Debug.Log($"[FingerAudit] Checked {checkedCount}/15 Left finger bones against Ramjet BindPose: maxPosDelta={maxErrMm:F3} mm");
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

        Texture2D diff = AssetDatabase.LoadAssetAtPath<Texture2D>(diffPath);
        if (diff != null) {
            m.SetTexture("_MainTex", diff);
            m.SetTextureScale("_MainTex", scale);
            m.SetTextureOffset("_MainTex", offset);
        }
        if (!string.IsNullOrEmpty(normPath)) {
            Texture2D norm = AssetDatabase.LoadAssetAtPath<Texture2D>(normPath);
            if (norm != null) {
                m.SetTexture("_BumpMap", norm);
                m.SetTextureScale("_BumpMap", scale);
                m.SetTextureOffset("_BumpMap", offset);
                m.EnableKeyword("_NORMALMAP");
            }
        }
        if (!string.IsNullOrEmpty(emPath)) {
            Texture2D em = AssetDatabase.LoadAssetAtPath<Texture2D>(emPath);
            if (em != null) {
                m.SetTexture("_EmissionMap", em);
                m.SetColor("_EmissionColor", Color.white);
                m.EnableKeyword("_EMISSION");
            }
        }
        EditorUtility.SetDirty(m);
        return m;
    }

    static void CreateDirLight(string name, Vector3 angles, float intensity, Color color) {
        GameObject go = new GameObject(name);
        Light l = go.AddComponent<Light>();
        l.type = LightType.Directional;
        l.intensity = intensity;
        l.color = color;
        go.transform.rotation = Quaternion.Euler(angles);
    }

    static Transform FindChildRecursive(Transform parent, string name) {
        if (parent == null) return null;
        if (parent.name == name) return parent;
        for (int i = 0; i < parent.childCount; i++) {
            Transform found = FindChildRecursive(parent.GetChild(i), name);
            if (found != null) return found;
        }
        return null;
    }
}
