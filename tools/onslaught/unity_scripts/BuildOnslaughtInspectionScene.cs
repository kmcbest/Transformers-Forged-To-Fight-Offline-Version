using UnityEditor;
using UnityEngine;
using UnityEditor.SceneManagement;
using UnityEngine.SceneManagement;
using UnityEngine.Playables;
using UnityEngine.Animations;
using System.IO;
using System.Collections.Generic;

public class BuildOnslaughtInspectionScene {
    [MenuItem("TFTF/Build Onslaught vs Ironhide Inspection Scene")]
    public static void Build() {
        Debug.Log("=== [Onslaught] Building Authoritative Side-by-Side Inspection Scene ===");

        AssetDatabase.Refresh();

        // 1. Configure NormalMap TextureImporters so Standard Shader renders true surface relief
        string[] normalMapPaths = new string[] {
            "Assets/Onslaught/cha_onslaught_main_NM_unity.png",
            "Assets/Onslaught/cha_onslaught_vh_NM_unity.png",
            "Assets/Onslaught/Ironhide/main_NM.png",
            "Assets/Onslaught/Ironhide/tform_misc_NM.png",
            "Assets/Onslaught/Ironhide/wpns_NM.png"
        };
        foreach (string np in normalMapPaths) {
            TextureImporter ti = AssetImporter.GetAtPath(np) as TextureImporter;
            if (ti != null && ti.textureType != TextureImporterType.NormalMap) {
                ti.textureType = TextureImporterType.NormalMap;
                ti.SaveAndReimport();
            }
        }

        // Configure FBX ModelImporters (first pass with useFileScale = true)
        foreach (string fp in new string[] { "Assets/Onslaught/onslaught_prepared.fbx", "Assets/Onslaught/onslaught_vh_prepared.fbx" }) {
            ModelImporter mi = AssetImporter.GetAtPath(fp) as ModelImporter;
            if (mi != null) {
                mi.useFileScale = true;
                mi.globalScale = 1.0f;
                mi.importNormals = ModelImporterNormals.Import;
                mi.importTangents = ModelImporterTangents.CalculateMikk;
                mi.SaveAndReimport();
            }
        }

        // 2. Load Official Ironhide Registered Bundle (single CAB containing both prefab+Avatars AND registered Ironhide clips!)
        string ihAnimsPath = @"E:\Agent\TFTF-blender\toolchain\ironhide_anims_registered.assetbundle";
        string ihFallbackPath = @"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\ironhide_cin_rotf_odr\ironhide_cin_rotf.assetbundle";
        string procBundlePath = @"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle";

        foreach (var b in AssetBundle.GetAllLoadedAssetBundles()) {
            b.Unload(false);
        }

        string chosenIhPath = File.Exists(ihAnimsPath) ? ihAnimsPath : ihFallbackPath;
        AssetBundle ihBundle = AssetBundle.LoadFromFile(chosenIhPath);
        if (ihBundle == null) {
            Debug.LogError("Failed to load Ironhide bundle: " + chosenIhPath);
            return;
        }
        AssetBundle ihAnimsBundle = null;
        AssetBundle procBundle = File.Exists(procBundlePath) ? AssetBundle.LoadFromFile(procBundlePath) : null;

        GameObject ihPrefab = ihBundle.LoadAsset<GameObject>("assets/bundles/characters/merged/ironhide_cin_rotf/ironhide_cin_rotf.prefab");
        if (ihPrefab == null) ihPrefab = ihBundle.LoadAsset<GameObject>("IronHide_Cin_ROTF");
        if (ihPrefab == null) {
            foreach (var go in ihBundle.LoadAllAssets<GameObject>()) {
                if (go.name.ToLower() == "ironhide_cin_rotf") { ihPrefab = go; break; }
            }
        }
        if (ihPrefab == null) {
            Debug.LogError("Could not find IronHide_Cin_ROTF prefab in bundle!");
            return;
        }

        SkinnedMeshRenderer ihSmr00 = null;
        SkinnedMeshRenderer ihSmr01 = null;
        foreach (var smr in ihPrefab.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name == "cha_ironhide_cin_rotf_00") ihSmr00 = smr;
            else if (smr.name == "cha_ironhide_cin_rotf_01") ihSmr01 = smr;
        }

        Debug.Log($"[Ironhide] SMR00 bounds={ihSmr00.sharedMesh.bounds}, bones={ihSmr00.bones.Length}");
        Debug.Log($"[Ironhide] SMR01 bounds={ihSmr01.sharedMesh.bounds}, bones={ihSmr01.bones.Length}");

        // Save permanent Official Ironhide Meshes so Scene never loses mesh references
        Mesh ihSaved00 = Object.Instantiate(ihSmr00.sharedMesh);
        ihSaved00.name = "cha_ironhide_official_00";
        AssetDatabase.CreateAsset(ihSaved00, "Assets/Onslaught/Ironhide/cha_ironhide_official_00.asset");

        Mesh ihSaved01 = Object.Instantiate(ihSmr01.sharedMesh);
        ihSaved01.name = "cha_ironhide_official_01";
        AssetDatabase.CreateAsset(ihSaved01, "Assets/Onslaught/Ironhide/cha_ironhide_official_01.asset");

        // Extract live Avatars directly from Prefab's Animator & transformed Animator (Avatars are sub-objects, NOT in m_Container!)
        Avatar officialAvatar00 = ihPrefab.GetComponent<Animator>() != null ? ihPrefab.GetComponent<Animator>().avatar : null;
        Transform prefabTr = FindChildRecursive(ihPrefab.transform, "transformed");
        Avatar officialAvatar01 = (prefabTr != null && prefabTr.GetComponent<Animator>() != null) ? prefabTr.GetComponent<Animator>().avatar : null;
        Debug.Log($"[Avatars] officialAvatar00={(officialAvatar00 != null ? officialAvatar00.name + " (isHuman=" + officialAvatar00.isHuman + ")" : "NULL")} | officialAvatar01={(officialAvatar01 != null ? officialAvatar01.name : "NULL")}");
        // Delete any previously serialized broken .asset Avatars (Unity 2020 CreateAsset strips 5.6 Mecanim muscle tables!)
        AssetDatabase.DeleteAsset("Assets/Onslaught/Ironhide/cha_ironhide_00Avatar.asset");
        AssetDatabase.DeleteAsset("Assets/Onslaught/Ironhide/cha_ironhide_01Avatar.asset");

        // 3. Graft Onslaught Robot Mesh onto Ironhide's Authoritative 80-Bone Bindposes!
        GameObject onsFbx = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Onslaught/onslaught_prepared.fbx");
        SkinnedMeshRenderer onsFbxSmr = onsFbx.GetComponentInChildren<SkinnedMeshRenderer>();
        Mesh rawOnsMesh = onsFbxSmr.sharedMesh;
        Debug.Log($"[Onslaught Robot FBX] Raw bounds: center={rawOnsMesh.bounds.center}, size={rawOnsMesh.bounds.size}, bones={onsFbxSmr.bones.Length}");

        // Auto-detect scale if FBX_SCALE_ALL produced 0.01x or 100x
        float maxSpan = Mathf.Max(rawOnsMesh.bounds.size.x, Mathf.Max(rawOnsMesh.bounds.size.y, rawOnsMesh.bounds.size.z));
        float scaleFix = 1.0f;
        if (maxSpan < 0.5f) scaleFix = 100.0f;
        else if (maxSpan > 100.0f) scaleFix = 0.01f;
        bool zIsHeight = (rawOnsMesh.bounds.size.z > rawOnsMesh.bounds.size.y * 1.2f);
        Debug.Log($"[Onslaught Robot FBX] scaleFix={scaleFix}, zIsHeight={zIsHeight}");

        Dictionary<string, int> ihBoneMap = new Dictionary<string, int>();
        for (int i = 0; i < ihSmr00.bones.Length; i++) {
            ihBoneMap[ihSmr00.bones[i].name] = i;
        }
        int[] remapRobot = new int[onsFbxSmr.bones.Length];
        int matchedBones = 0;
        for (int j = 0; j < onsFbxSmr.bones.Length; j++) {
            if (ihBoneMap.TryGetValue(onsFbxSmr.bones[j].name, out int idx)) {
                remapRobot[j] = idx;
                matchedBones++;
            } else {
                remapRobot[j] = ihBoneMap.ContainsKey("Spine1") ? ihBoneMap["Spine1"] : 0;
            }
        }
        Debug.Log($"[✓] Remapped {matchedBones}/{onsFbxSmr.bones.Length} Onslaught robot bones to Ironhide!");

        Vector3[] rVerts = rawOnsMesh.vertices;
        Vector3[] gVerts = new Vector3[rVerts.Length];
        Vector3[] rNorms = rawOnsMesh.normals;
        Vector3[] gNorms = new Vector3[rNorms.Length];
        Vector4[] rTans = rawOnsMesh.tangents;
        Vector4[] gTans = new Vector4[rTans.Length];

        for (int i = 0; i < rVerts.Length; i++) {
            Vector3 v = rVerts[i] * scaleFix;
            gVerts[i] = zIsHeight ? new Vector3(-v.x, v.z, v.y) : v;
        }
        for (int i = 0; i < rNorms.Length; i++) {
            Vector3 n = rNorms[i];
            gNorms[i] = zIsHeight ? new Vector3(-n.x, n.z, n.y) : n;
        }
        for (int i = 0; i < rTans.Length; i++) {
            Vector4 t = rTans[i];
            gTans[i] = zIsHeight ? new Vector4(-t.x, t.z, t.y, t.w) : t;
        }

        BoneWeight[] origBw = rawOnsMesh.boneWeights;
        BoneWeight[] newBw = new BoneWeight[origBw.Length];
        for (int i = 0; i < origBw.Length; i++) {
            BoneWeight bw = origBw[i];
            bw.boneIndex0 = remapRobot[bw.boneIndex0];
            bw.boneIndex1 = remapRobot[bw.boneIndex1];
            bw.boneIndex2 = remapRobot[bw.boneIndex2];
            bw.boneIndex3 = remapRobot[bw.boneIndex3];
            newBw[i] = bw;
        }

        Mesh onsGraftedRobot = new Mesh();
        onsGraftedRobot.name = "cha_onslaught_gs_00";
        onsGraftedRobot.vertices = gVerts;
        onsGraftedRobot.normals = gNorms;
        onsGraftedRobot.tangents = gTans;
        onsGraftedRobot.uv = rawOnsMesh.uv;
        onsGraftedRobot.subMeshCount = rawOnsMesh.subMeshCount;
        for (int sm = 0; sm < rawOnsMesh.subMeshCount; sm++) {
            onsGraftedRobot.SetTriangles(rawOnsMesh.GetTriangles(sm), sm);
        }
        onsGraftedRobot.boneWeights = newBw;
        onsGraftedRobot.bindposes = ihSmr00.sharedMesh.bindposes;
        onsGraftedRobot.RecalculateBounds();
        AssetDatabase.CreateAsset(onsGraftedRobot, "Assets/Onslaught/cha_onslaught_grafted.asset");
        Debug.Log($"[✓] Created cha_onslaught_grafted.asset | Bounds center={onsGraftedRobot.bounds.center}, size={onsGraftedRobot.bounds.size}");

        // 4. Graft Onslaught Vehicle Mesh onto Ironhide's 47-Bone Vehicle Bindposes!
        GameObject onsVhFbx = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Onslaught/onslaught_vh_prepared.fbx");
        SkinnedMeshRenderer onsVhFbxSmr = onsVhFbx.GetComponentInChildren<SkinnedMeshRenderer>();
        Mesh rawVhMesh = onsVhFbxSmr.sharedMesh;
        float vhMaxSpan = Mathf.Max(rawVhMesh.bounds.size.x, Mathf.Max(rawVhMesh.bounds.size.y, rawVhMesh.bounds.size.z));
        float vhScaleFix = (vhMaxSpan < 0.5f) ? 100.0f : ((vhMaxSpan > 100.0f) ? 0.01f : 1.0f);
        // Check which axis in rawVhMesh is length (~8.0m) vs height (~3.9m):
        // In Blender: X[-2.58, 2.58] (5.16m width), Y[-4.00, 4.00] (8.00m length), Z[0.00, 3.92] (3.92m height).
        // Compare against ihSmr01.sharedMesh.bounds!
        Debug.Log($"[Onslaught Vh FBX] Raw bounds: center={rawVhMesh.bounds.center}, size={rawVhMesh.bounds.size} | Ironhide Vh mesh bounds: center={ihSmr01.sharedMesh.bounds.center}, size={ihSmr01.sharedMesh.bounds.size}");

        int bodyBaseIdx = 0;
        for (int i = 0; i < ihSmr01.bones.Length; i++) {
            if (ihSmr01.bones[i].name == "BodyBase") {
                bodyBaseIdx = i;
                break;
            }
        }
        // cha_ironhide_cin_rotf_01 mesh space is already standard upright (X=width, Y=height [0..4.3], Z=length [-4.8..+5.0])!
        bool vhZIsHeight = (Mathf.Abs(rawVhMesh.bounds.center.z) > Mathf.Abs(rawVhMesh.bounds.center.y));
        Vector3[] rvVerts = rawVhMesh.vertices;
        Vector3[] gvVerts = new Vector3[rvVerts.Length];
        Vector3[] rvNorms = rawVhMesh.normals;
        Vector3[] gvNorms = new Vector3[rvNorms.Length];
        Vector4[] rvTans = rawVhMesh.tangents;
        Vector4[] gvTans = new Vector4[rvTans.Length];

        float vhProportionScale = 1.14f; // Match Ironhide's (6.6, 4.3, 9.8) truck scale cleanly (~5.9 x 4.45 x 9.12)
        for (int i = 0; i < rvVerts.Length; i++) {
            Vector3 v = rvVerts[i] * (vhScaleFix * vhProportionScale);
            gvVerts[i] = vhZIsHeight ? new Vector3(-v.x, v.z, v.y) : v;
        }
        for (int i = 0; i < rvNorms.Length; i++) {
            Vector3 n = rvNorms[i];
            gvNorms[i] = vhZIsHeight ? new Vector3(-n.x, n.z, n.y) : n;
        }
        for (int i = 0; i < rvTans.Length; i++) {
            Vector4 t = rvTans[i];
            gvTans[i] = vhZIsHeight ? new Vector4(-t.x, t.z, t.y, t.w) : t;
        }

        BoneWeight[] vhBw = new BoneWeight[rvVerts.Length];
        for (int i = 0; i < vhBw.Length; i++) {
            vhBw[i] = new BoneWeight { boneIndex0 = bodyBaseIdx, weight0 = 1.0f };
        }

        Mesh onsGraftedVh = new Mesh();
        onsGraftedVh.name = "cha_onslaught_gs_01";
        onsGraftedVh.vertices = gvVerts;
        onsGraftedVh.normals = gvNorms;
        onsGraftedVh.tangents = gvTans;
        onsGraftedVh.uv = rawVhMesh.uv;
        onsGraftedVh.subMeshCount = rawVhMesh.subMeshCount;
        for (int sm = 0; sm < rawVhMesh.subMeshCount; sm++) {
            onsGraftedVh.SetTriangles(rawVhMesh.GetTriangles(sm), sm);
        }
        onsGraftedVh.boneWeights = vhBw;
        onsGraftedVh.bindposes = ihSmr01.sharedMesh.bindposes;
        onsGraftedVh.RecalculateBounds();
        AssetDatabase.CreateAsset(onsGraftedVh, "Assets/Onslaught/cha_onslaught_vehicle_grafted.asset");
        Debug.Log($"[✓] Created cha_onslaught_vehicle_grafted.asset | Bounds center={onsGraftedVh.bounds.center}, size={onsGraftedVh.bounds.size}");

        // 5. Create Standard Materials for Official Ironhide & Onslaught
        Material matIhMain = CreateOrUpdateMat("Assets/Onslaught/Ironhide/M_Ironhide_Main.mat",
            "Assets/Onslaught/Ironhide/cha_ironhide_cin_rotf_main_a.png",
            "Assets/Onslaught/Ironhide/main_NM.png", null, 0.42f, 0.25f);
        Material matIhMisc = CreateOrUpdateMat("Assets/Onslaught/Ironhide/M_Ironhide_Misc.mat",
            "Assets/Onslaught/Ironhide/tform_misc_A.png",
            "Assets/Onslaught/Ironhide/tform_misc_NM.png", null, 0.40f, 0.25f);
        Material matIhWpns = CreateOrUpdateMat("Assets/Onslaught/Ironhide/M_Ironhide_Wpns.mat",
            "Assets/Onslaught/Ironhide/cha_ironhide_cin_rotf_wpns_a.png",
            "Assets/Onslaught/Ironhide/wpns_NM.png", null, 0.45f, 0.30f);

        Material matOnsMain = CreateOrUpdateMat("Assets/Onslaught/M_Onslaught_Main.mat",
            "Assets/Onslaught/cha_onslaught_main_a.png",
            "Assets/Onslaught/cha_onslaught_main_NM_unity.png",
            "Assets/Onslaught/cha_onslaught_main_Emission.png", 0.42f, 0.22f);
        Material matOnsVh = CreateOrUpdateMat("Assets/Onslaught/M_Onslaught_Vh.mat",
            "Assets/Onslaught/cha_onslaught_vh_a.png",
            "Assets/Onslaught/cha_onslaught_vh_NM_unity.png",
            "Assets/Onslaught/cha_onslaught_vh_Emission.png", 0.42f, 0.22f);

        // 6. Build Clean Side-by-Side Scene
        if (!Directory.Exists("Assets/Scenes")) Directory.CreateDirectory("Assets/Scenes");
        Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        // 3-Point Studio Lighting (Characters face +Z, Camera looks from +Z toward -Z!)
        CreateDirLight("Key Light", new Vector3(22f, -155f, 0f), 1.25f, new Color(1.0f, 0.98f, 0.95f));
        CreateDirLight("Fill Light", new Vector3(15f, 145f, 0f), 0.65f, new Color(0.88f, 0.93f, 1.0f));
        CreateDirLight("Back Rim Light", new Vector3(25f, 10f, 0f), 0.75f, new Color(0.95f, 0.95f, 1.0f));

        GameObject camGo = new GameObject("Main Camera");
        camGo.tag = "MainCamera";
        Camera cam = camGo.AddComponent<Camera>();
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color(0.14f, 0.15f, 0.19f);
        cam.fieldOfView = 45.0f;
        camGo.transform.position = new Vector3(0.0f, 5.4f, 17.5f);
        camGo.transform.LookAt(new Vector3(0.0f, 5.0f, 0.0f));

        // Left on screen (from +Z camera looking toward 0, +X is Screen Left!):
        // Let's place Official Ironhide at X = +3.8f (Screen Left) and Onslaught at X = -3.8f (Screen Right)
        GameObject ihInst = Object.Instantiate(ihPrefab);
        ihInst.name = "Ironhide_Official_Reference";
        ihInst.transform.position = new Vector3(3.8f, 0.0f, 0.0f);
        ihInst.transform.rotation = Quaternion.identity;

        foreach (var smr in ihInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name == "cha_ironhide_cin_rotf_00") {
                smr.sharedMesh = ihSaved00;
                smr.sharedMaterials = new Material[] { matIhMain, matIhMisc, matIhWpns };
                smr.updateWhenOffscreen = true;
                smr.enabled = true;
            } else if (smr.name == "cha_ironhide_cin_rotf_01") {
                smr.sharedMesh = ihSaved01;
                smr.sharedMaterials = new Material[] { matIhMisc, matIhWpns, matIhMain, matIhMisc };
                smr.updateWhenOffscreen = true;
                smr.enabled = false;
            } else {
                smr.enabled = false;
                smr.gameObject.SetActive(false);
            }
        }

        GameObject onsInst = Object.Instantiate(ihPrefab);
        onsInst.name = "Onslaught_Candidate";
        onsInst.transform.position = new Vector3(-3.8f, 0.0f, 0.0f);
        onsInst.transform.rotation = Quaternion.identity;

        SkinnedMeshRenderer onsSmr00 = null, onsSmr01 = null;
        foreach (var smr in onsInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name == "cha_ironhide_cin_rotf_00") {
                smr.gameObject.name = "cha_onslaught_gs_00";
                smr.sharedMesh = onsGraftedRobot;
                smr.sharedMaterials = new Material[] { matOnsMain };
                smr.updateWhenOffscreen = true;
                smr.enabled = true;
                onsSmr00 = smr;
            } else if (smr.name == "cha_ironhide_cin_rotf_01") {
                smr.gameObject.name = "cha_onslaught_gs_01";
                smr.sharedMesh = onsGraftedVh;
                smr.sharedMaterials = new Material[] { matOnsVh };
                smr.updateWhenOffscreen = true;
                smr.enabled = false;
                onsSmr01 = smr;
            } else {
                smr.enabled = false;
                smr.gameObject.SetActive(false);
            }
        }

        Animator animIh = ihInst.GetComponent<Animator>();
        Animator animOns = onsInst.GetComponent<Animator>();
        if (officialAvatar00 != null) {
            animIh.avatar = officialAvatar00;
            animOns.avatar = officialAvatar00;
        }
        animIh.cullingMode = AnimatorCullingMode.AlwaysAnimate;
        animOns.cullingMode = AnimatorCullingMode.AlwaysAnimate;
        animIh.applyRootMotion = false;
        animOns.applyRootMotion = false;

        Transform trIh = FindChildRecursive(ihInst.transform, "transformed");
        Transform trOns = FindChildRecursive(onsInst.transform, "transformed");
        Animator animTrIh = trIh != null ? (trIh.GetComponent<Animator>() ?? trIh.gameObject.AddComponent<Animator>()) : null;
        Animator animTrOns = trOns != null ? (trOns.GetComponent<Animator>() ?? trOns.gameObject.AddComponent<Animator>()) : null;
        if (officialAvatar01 != null) {
            if (animTrIh != null) { animTrIh.avatar = officialAvatar01; animTrIh.cullingMode = AnimatorCullingMode.AlwaysAnimate; animTrIh.applyRootMotion = false; }
            if (animTrOns != null) { animTrOns.avatar = officialAvatar01; animTrOns.cullingMode = AnimatorCullingMode.AlwaysAnimate; animTrOns.applyRootMotion = false; }
        }

        // Attach Interactive Runtime Controller & 30-Finger Tester
        var fingerTester = onsInst.GetComponent<OnslaughtFingerTester>();
        if (fingerTester == null) fingerTester = onsInst.AddComponent<OnslaughtFingerTester>();
        fingerTester.leftHandAxis = OnslaughtFingerTester.CurlAxis.Forward_Z;
        fingerTester.rightHandAxis = OnslaughtFingerTester.CurlAxis.Back_NegZ;
        fingerTester.autoWiggle = false;
        fingerTester.InitializeBones();

        GameObject ctrlGo = new GameObject("OnslaughtPreviewController");
        var ctrlComp = ctrlGo.AddComponent<OnslaughtPreviewController>();
        ctrlComp.animIronhide = animIh;
        ctrlComp.animOnslaught = animOns;

        // Inspect SP3 curves to find exact vehicle visibility window if any!
        Dictionary<string, AnimationClip> allClips = new Dictionary<string, AnimationClip>();
        if (ihPrefab.GetComponent<Animator>()?.runtimeAnimatorController != null) {
            foreach (var c in ihPrefab.GetComponent<Animator>().runtimeAnimatorController.animationClips) if (c != null) allClips[c.name] = c;
        }
        if (prefabTr != null && prefabTr.GetComponent<Animator>()?.runtimeAnimatorController != null) {
            foreach (var c in prefabTr.GetComponent<Animator>().runtimeAnimatorController.animationClips) if (c != null) allClips[c.name] = c;
        }
        foreach (var c in ihBundle.LoadAllAssets<AnimationClip>()) if (c != null) allClips[c.name] = c;
        if (ihAnimsBundle != null) foreach (var c in ihAnimsBundle.LoadAllAssets<AnimationClip>()) if (c != null) allClips[c.name] = c;
        if (procBundle != null) {
            foreach (string ap in procBundle.GetAllAssetNames()) {
                foreach (var sub in procBundle.LoadAssetWithSubAssets(ap)) {
                    if (sub is AnimationClip ac && !allClips.ContainsKey(ac.name)) allClips[ac.name] = ac;
                }
            }
        }

        if (allClips.TryGetValue("Ironhide_Normal_attackSpecial_03", out AnimationClip sp3Clip)) {
            foreach (var binding in AnimationUtility.GetCurveBindings(sp3Clip)) {
                if (binding.propertyName.Contains("Enabled") || binding.path.Contains("01") || binding.path.Contains("00")) {
                    AnimationCurve curve = AnimationUtility.GetEditorCurve(sp3Clip, binding);
                    string keysStr = "";
                    foreach (var k in curve.keys) keysStr += $"({k.time:F2}s:{k.value:F1}) ";
                    Debug.Log($"[SP3 Curve] path='{binding.path}' prop='{binding.propertyName}' keys={keysStr}");
                }
            }
        }

        foreach (var kv in allClips) {
            if (kv.Key.ToLower().Contains("ironhide") || kv.Key.ToLower().Contains("vehicle") || kv.Key.ToLower().Contains("transform")) {
                Debug.Log($"[Clip Registry] {kv.Key} ({kv.Value.length:F2}s, humanMotion={kv.Value.humanMotion})");
            }
        }

        // Snapshot pristine prefab bone transforms so every RenderPoseShot starts cleanly AND saved scene stays unmutated!
        var initPos = new Dictionary<Transform, Vector3>();
        var initRot = new Dictionary<Transform, Quaternion>();
        var initScl = new Dictionary<Transform, Vector3>();
        foreach (var t in ihInst.GetComponentsInChildren<Transform>(true)) { initPos[t] = t.localPosition; initRot[t] = t.localRotation; initScl[t] = t.localScale; }
        foreach (var t in onsInst.GetComponentsInChildren<Transform>(true)) { initPos[t] = t.localPosition; initRot[t] = t.localRotation; initScl[t] = t.localScale; }

        void RestoreInitialPose() {
            foreach (var kv in initPos) {
                if (kv.Key != null) {
                    kv.Key.localPosition = kv.Value;
                    kv.Key.localRotation = initRot[kv.Key];
                    kv.Key.localScale = initScl[kv.Key];
                }
            }
            ihInst.transform.position = new Vector3(3.8f, 0.0f, 0.0f);
            ihInst.transform.rotation = Quaternion.identity;
            onsInst.transform.position = new Vector3(-3.8f, 0.0f, 0.0f);
            onsInst.transform.rotation = Quaternion.identity;
        }

        string scenePath = "Assets/Scenes/Onslaught_Inspection.unity";

        // 7. Render Multi-Pose & Multi-Angle Side-by-Side Verification Screenshots (WITH live officialAvatar00/01 bound!)
        string outDir = @"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d";
        int w = 1920, h = 1080;
        RenderTexture rt = new RenderTexture(w, h, 24, RenderTextureFormat.ARGB32);
        rt.antiAliasing = 4;
        cam.targetTexture = rt;
        Texture2D ss = new Texture2D(w, h, TextureFormat.RGB24, false);

        Transform refIh = FindChildRecursive(ihInst.transform, "Reference");
        Transform hipsIh = FindChildRecursive(ihInst.transform, "Hips");
        Transform hipsOns = FindChildRecursive(onsInst.transform, "Hips");

        Debug.Log($"[Skinning Audit] ihSaved00: verts={ihSaved00.vertexCount}, bw={ihSaved00.boneWeights.Length}, bp={ihSaved00.bindposes.Length} | onsGraftedRobot: verts={onsGraftedRobot.vertexCount}, bw={onsGraftedRobot.boneWeights.Length}, bp={onsGraftedRobot.bindposes.Length}");

        // Find best vehicle upright pose using TRUE WORLD MeshRenderer.bounds (including smr.transform.rotation!)
        string chosenVehRoot = "Ironhide_Normal_attackSpecial_03";
        string chosenVehTrans = "Ironhide_Normal_attackSpecial_03_transformed";
        float chosenVehT = 2.20f;
        {
            SkinnedMeshRenderer ihVhTest = null;
            foreach (var s in ihInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) if (s.name.Contains("_01")) ihVhTest = s;
            var candidates = new (string r, string tr, float t)[] {
                ("Ironhide_Normal_attackSpecial_03", "Ironhide_Normal_attackSpecial_03_transformed", 2.20f),
                ("Ironhide_Normal_attackHeavy", "Ironhide_Normal_attackHeavy_transformed", 0.45f),
                (null, "frontend_Ironhide_levelup_vehicle_idle_transformed", 0.25f),
                (null, null, 0.0f)
            };
            foreach (var cand in candidates) {
                RestoreInitialPose();
                if (cand.r != null && allClips.TryGetValue(cand.r, out var cr)) cr.SampleAnimation(ihInst, cand.t);
                if (cand.tr != null && allClips.TryGetValue(cand.tr, out var ctr) && trIh != null) ctr.SampleAnimation(trIh.gameObject, cand.t);
                if (ihVhTest != null) {
                    Mesh bm = new Mesh();
                    ihVhTest.BakeMesh(bm, true);
                    GameObject tgo = new GameObject("VehTest");
                    tgo.transform.SetPositionAndRotation(ihVhTest.transform.position, ihVhTest.transform.rotation);
                    tgo.AddComponent<MeshFilter>().sharedMesh = bm;
                    var tmr = tgo.AddComponent<MeshRenderer>();
                    Bounds wb = tmr.bounds;
                    Debug.Log($"[VehWorldAudit] root='{cand.r ?? "REST"}' trans='{cand.tr ?? "REST"}' @ {cand.t:F2}s -> rot={ihVhTest.transform.eulerAngles} WORLD center={wb.center}, size={wb.size}");
                    if (wb.size.y < 5.5f && wb.size.z > 7.5f) {
                        chosenVehRoot = cand.r;
                        chosenVehTrans = cand.tr;
                        chosenVehT = cand.t;
                    }
                    Object.DestroyImmediate(tgo);
                    Object.DestroyImmediate(bm);
                }
            }
            RestoreInitialPose();
            Debug.Log($"[VehChosen] Using root='{chosenVehRoot ?? "REST"}' + trans='{chosenVehTrans ?? "REST"}' @ {chosenVehT:F2}s");
        }

        // Audit SP1 cannon aim frames
        float bestCannonT = 0.65f;
        if (allClips.TryGetValue("Ironhide_Normal_attackSpecial_01", out AnimationClip sp1Audit)) {
            Transform lh = FindChildRecursive(ihInst.transform, "LeftHand");
            Transform rh = FindChildRecursive(ihInst.transform, "RightHand");
            float bestZ = -999f;
            for (float t = 0.20f; t <= 2.20f; t += 0.10f) {
                RestoreInitialPose();
                sp1Audit.SampleAnimation(ihInst, t);
                if (hipsIh != null && lh != null && rh != null) {
                    float dz = Mathf.Max(lh.position.z - hipsIh.position.z, rh.position.z - hipsIh.position.z);
                    float avgY = 0.5f * (lh.position.y + rh.position.y);
                    if (avgY > 4.2f && avgY < 7.8f && dz > bestZ) {
                        bestZ = dz;
                        bestCannonT = t;
                    }
                }
            }
            RestoreInitialPose();
            Debug.Log($"[PeakCannon] Ironhide_Normal_attackSpecial_01 -> bestCannonT={bestCannonT:F2}s (dz={bestZ:F2})");
        }

        void RenderPoseShot(string clipName, float sampleTime, Vector3 camPos, Vector3 lookTarget, string fileName, bool vehicleMode = false, string transClipName = null) {
            RestoreInitialPose();

            SkinnedMeshRenderer ihActiveSmr = null;
            foreach (var smr in ihInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
                if (smr.name.Contains("_00")) { smr.enabled = !vehicleMode; if (!vehicleMode) ihActiveSmr = smr; }
                else if (smr.name.Contains("_01")) { smr.gameObject.SetActive(true); smr.enabled = vehicleMode; if (vehicleMode) ihActiveSmr = smr; }
            }
            if (onsSmr00 != null) onsSmr00.enabled = !vehicleMode;
            if (onsSmr01 != null) { onsSmr01.gameObject.SetActive(true); onsSmr01.enabled = vehicleMode; }
            SkinnedMeshRenderer onsActiveSmr = vehicleMode ? onsSmr01 : onsSmr00;

            if (clipName != null && allClips.TryGetValue(clipName, out AnimationClip c)) {
                c.SampleAnimation(ihInst, sampleTime);
                c.SampleAnimation(onsInst, sampleTime);
            } else if (!allClips.ContainsKey(clipName ?? "") && clipName != null) {
                Debug.LogWarning($"[Shot {fileName}] Clip NOT FOUND in allClips: '{clipName}'");
            }
            if (transClipName != null && allClips.TryGetValue(transClipName, out AnimationClip tc) && trIh != null && trOns != null) {
                tc.SampleAnimation(trIh.gameObject, sampleTime);
                tc.SampleAnimation(trOns.gameObject, sampleTime);
            }

            float spacing = vehicleMode ? 4.4f : 3.9f;
            if (hipsIh != null && hipsOns != null) {
                Vector3 dIh = hipsIh.position - ihInst.transform.position;
                ihInst.transform.position = new Vector3(spacing - dIh.x, 0.0f, 0.0f - dIh.z);
                Vector3 dOns = hipsOns.position - onsInst.transform.position;
                onsInst.transform.position = new Vector3(-spacing - dOns.x, 0.0f, 0.0f - dOns.z);
            }

            // Force synchronous CPU skinning via BakeMesh so headless Edit-Mode Camera.Render() renders all 80 deformed bones!
            List<GameObject> tempBakedGos = new List<GameObject>();
            List<Mesh> tempBakedMeshes = new List<Mesh>();
            foreach (var smr in new SkinnedMeshRenderer[] { ihActiveSmr, onsActiveSmr }) {
                if (smr != null && smr.enabled) {
                    Mesh bm = new Mesh();
                    smr.BakeMesh(bm, true);
                    bm.RecalculateBounds();
                    GameObject bgo = new GameObject("TempBaked_" + smr.name);
                    bgo.transform.SetPositionAndRotation(smr.transform.position, smr.transform.rotation);
                    bgo.transform.localScale = Vector3.one;
                    var mf = bgo.AddComponent<MeshFilter>();
                    mf.sharedMesh = bm;
                    var mr = bgo.AddComponent<MeshRenderer>();
                    mr.sharedMaterials = smr.sharedMaterials;
                    smr.enabled = false;
                    tempBakedGos.Add(bgo);
                    tempBakedMeshes.Add(bm);
                    Debug.Log($"[Baked {fileName}] {smr.name} -> bgoPos={bgo.transform.position}, bakedBounds={bm.bounds}");
                }
            }

            // If in vehicle mode and baked center Y or Z drifted from 0, center the two baked vehicles neatly on Y>=0, Z=0!
            if (vehicleMode && tempBakedGos.Count == 2) {
                for (int k = 0; k < 2; k++) {
                    var mr = tempBakedGos[k].GetComponent<MeshRenderer>();
                    Bounds wb = mr.bounds;
                    float targetX = (k == 0) ? 4.4f : -4.4f;
                    tempBakedGos[k].transform.position += new Vector3(targetX - wb.center.x, -wb.min.y, 0.0f - wb.center.z);
                }
            }

            cam.transform.position = camPos;
            cam.transform.LookAt(lookTarget);
            cam.Render();
            RenderTexture.active = rt;
            ss.ReadPixels(new Rect(0, 0, w, h), 0, 0);
            ss.Apply();
            File.WriteAllBytes(Path.Combine(outDir, fileName), ss.EncodeToPNG());
            Debug.Log("[✓] Rendered verification screenshot: " + fileName);

            foreach (var bgo in tempBakedGos) Object.DestroyImmediate(bgo);
            foreach (var bm in tempBakedMeshes) Object.DestroyImmediate(bm);
            if (ihActiveSmr != null) ihActiveSmr.enabled = true;
            if (onsActiveSmr != null) onsActiveSmr.enabled = true;
        }

        // Shot 0: Pure BindPose / Rest Stance (before any animation)
        RenderPoseShot(null, 0f, new Vector3(0f, 5.4f, 17.5f), new Vector3(0f, 5.1f, 0f), "unity_sbs_00_rest_pose.png");

        // Shot 1: Combat Stance Idle (Front)
        RenderPoseShot("brawler_normal_idle", 0.35f, new Vector3(0f, 5.4f, 17.5f), new Vector3(0f, 5.0f, 0f), "unity_sbs_01_combat_idle_front.png");

        // Shot 2: TeamSelect Idle (Front-Left 3/4 Perspective)
        RenderPoseShot("TeamSelect_Brawler_idle", 0.50f, new Vector3(5.5f, 5.8f, 17.0f), new Vector3(0f, 5.0f, 0f), "unity_sbs_02_teamselect_idle_34.png");

        // Shot 3: Rear 3/4 View (showing Onslaught's Twin Back Cannons & Wheel Armor!)
        RenderPoseShot("brawler_normal_idle", 0.35f, new Vector3(-6.5f, 6.4f, -16.5f), new Vector3(0f, 5.2f, 0f), "unity_sbs_03_back_cannons_view.png");

        // Shot 4: Light Attack Punch (Synchronized Cross/Jab @ t=0.40s from 3/4 angle so arm extension is crystal clear!)
        RenderPoseShot("brawler_normal_attackLight_01_jab", 0.40f, new Vector3(-7.2f, 5.6f, 16.2f), new Vector3(0f, 5.1f, 0f), "unity_sbs_04_light_punch_action.png");

        // Shot 5: Forearm Cannon Blast Action (Synchronized Special 1 Cannon Aim & Fire from 3/4 angle!)
        RenderPoseShot("Ironhide_Normal_attackSpecial_01", bestCannonT, new Vector3(-7.2f, 5.6f, 16.2f), new Vector3(0f, 5.1f, 0f), "unity_sbs_05_heavy_cannon_blast.png");

        // Shot 6: Vehicle Mode Side-by-Side (Guaranteed level world-space vehicle pose!)
        RenderPoseShot(chosenVehRoot, chosenVehT, new Vector3(-5.8f, 4.8f, 16.2f), new Vector3(0f, 2.1f, 0f), "unity_sbs_06_vehicle_mode_sbs.png", true, chosenVehTrans);

        // Shot 7: Light Attack 4 High Front Kick (Tests hip/knee/shin-wheel rigid articulation under extreme leg lift!)
        RenderPoseShot("brawler_normal_attackLight_04_frontkick", 0.36f, new Vector3(-6.8f, 5.4f, 16.8f), new Vector3(0f, 4.9f, 0f), "unity_sbs_07_high_kick_action.png");

        // Shot 8: Victory Pose (Synchronized Brawler_Normal_Victory!)
        RenderPoseShot("Brawler_Normal_Victory", 1.85f, new Vector3(0f, 5.5f, 17.5f), new Vector3(0f, 5.1f, 0f), "unity_sbs_08_victory_pose.png");

        // Restore pristine unmutated pose and save scene cleanly
        RestoreInitialPose();
        foreach (var smr in ihInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name.Contains("_00")) smr.enabled = true;
            else if (smr.name.Contains("_01")) smr.enabled = false;
        }
        if (onsSmr00 != null) onsSmr00.enabled = true;
        if (onsSmr01 != null) onsSmr01.enabled = false;

        cam.targetTexture = null;
        RenderTexture.active = null;
        Object.DestroyImmediate(rt);
        Object.DestroyImmediate(ss);
        cam.transform.position = new Vector3(0.0f, 5.4f, 17.5f);
        cam.transform.LookAt(new Vector3(0.0f, 5.0f, 0.0f));

        // Clear temporary bundle Avatar refs before saving scene so Unity doesn't complain about unloaded bundle objects;
        // OnslaughtPreviewController.Start() automatically binds officialAvatar00/01 from bundle at Play!
        animIh.avatar = null;
        animOns.avatar = null;
        if (animTrIh != null) animTrIh.avatar = null;
        if (animTrOns != null) animTrOns.avatar = null;

        EditorSceneManager.SaveScene(scene, scenePath);
        Debug.Log("[✓] Saved clean scene: " + scenePath);

        if (procBundle != null) procBundle.Unload(false);
        if (ihAnimsBundle != null) ihAnimsBundle.Unload(false);
        ihBundle.Unload(false);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("=== [Onslaught] ALL DONE! Scene & 7 Verification Renders Exported! ===");
    }

    static PlayableGraph EvalClip(Animator anim, AnimationClip clip, float timeSec) {
        PlayableGraph g = PlayableGraph.Create("Eval_" + anim.name);
        g.SetTimeUpdateMode(DirectorUpdateMode.Manual);
        var p = AnimationClipPlayable.Create(g, clip);
        p.SetApplyFootIK(false);
        p.SetTime(timeSec);
        var o = AnimationPlayableOutput.Create(g, "Out", anim);
        o.SetSourcePlayable(p);
        g.Evaluate(0.0f);
        return g;
    }

    static Material CreateOrUpdateMat(string matPath, string diffPath, string normPath, string emPath, float gloss, float metallic) {
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
        if (td != null) m.mainTexture = td;

        if (!string.IsNullOrEmpty(normPath)) {
            Texture2D tn = AssetDatabase.LoadAssetAtPath<Texture2D>(normPath);
            if (tn != null) {
                m.EnableKeyword("_NORMALMAP");
                m.SetTexture("_BumpMap", tn);
            }
        }

        if (!string.IsNullOrEmpty(emPath)) {
            Texture2D te = AssetDatabase.LoadAssetAtPath<Texture2D>(emPath);
            if (te != null) {
                m.EnableKeyword("_EMISSION");
                m.SetTexture("_EmissionMap", te);
                m.SetColor("_EmissionColor", Color.white * 0.85f);
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
