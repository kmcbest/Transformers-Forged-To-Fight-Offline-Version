using UnityEditor;
using UnityEngine;
using UnityEditor.SceneManagement;
using UnityEngine.SceneManagement;
using UnityEngine.Playables;
using UnityEngine.Animations;
using System.IO;
using System.Collections.Generic;

public class BuildVortexInspectionScene {
    [MenuItem("TFTF/Build Vortex vs Grindor Inspection Scene")]
    public static void Build() {
        Debug.Log("=== [Vortex] Building Authoritative Side-by-Side Inspection Scene ===");

        AssetDatabase.Refresh();

        // 1. Configure NormalMap TextureImporters
        string[] normalMapPaths = new string[] {
            "Assets/Vortex/cha_vortex_main_NM_unity.png",
            "Assets/Vortex/cha_vortex_vh_NM_unity.png",
            "Assets/Vortex/Grindor/main_NM.png",
            "Assets/Vortex/Grindor/tform_misc_NM.png",
            "Assets/Vortex/Grindor/wpns_NM.png"
        };
        foreach (string np in normalMapPaths) {
            TextureImporter ti = AssetImporter.GetAtPath(np) as TextureImporter;
            if (ti != null && ti.textureType != TextureImporterType.NormalMap) {
                ti.textureType = TextureImporterType.NormalMap;
                ti.SaveAndReimport();
            }
        }

        // Configure FBX ModelImporters
        foreach (string fp in new string[] { "Assets/Vortex/vortex_prepared.fbx", "Assets/Vortex/vortex_vh_prepared.fbx" }) {
            ModelImporter mi = AssetImporter.GetAtPath(fp) as ModelImporter;
            if (mi != null) {
                mi.useFileScale = true;
                mi.globalScale = 1.0f;
                mi.importNormals = ModelImporterNormals.Import;
                mi.importTangents = ModelImporterTangents.CalculateMikk;
                mi.SaveAndReimport();
            }
        }

        // 2. Load Official Grindor Bundle (using registered anim bundle with all 33 clips!)
        string gBundlePath = @"E:\Agent\TFTF-blender\toolchain\grindor_anims_registered.assetbundle";
        if (!File.Exists(gBundlePath)) {
            gBundlePath = @"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle";
        }
        foreach (var b in AssetBundle.GetAllLoadedAssetBundles()) {
            b.Unload(false);
        }

        AssetBundle gBundle = AssetBundle.LoadFromFile(gBundlePath);
        if (gBundle == null) {
            Debug.LogError("Failed to load Grindor bundle at " + gBundlePath);
            return;
        }

        GameObject gPrefab = gBundle.LoadAsset<GameObject>("Grindor_Cin_ROTF");
        if (gPrefab == null) {
            foreach (var go in gBundle.LoadAllAssets<GameObject>()) {
                if (go.name.ToLower().Contains("grindor_cin_rotf")) { gPrefab = go; break; }
            }
        }
        if (gPrefab == null) {
            Debug.LogError("Could not find Grindor_Cin_ROTF prefab in bundle!");
            return;
        }

        SkinnedMeshRenderer gSmr00 = null;
        SkinnedMeshRenderer gSmr01 = null;
        foreach (var smr in gPrefab.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name.Contains("_00") && !smr.name.Contains("wpns")) gSmr00 = smr;
            else if (smr.name.Contains("_01")) gSmr01 = smr;
        }

        // Save permanent Grindor official meshes
        Directory.CreateDirectory(Path.Combine(Application.dataPath, "Vortex/Grindor"));
        Mesh gSaved00 = Object.Instantiate(gSmr00.sharedMesh);
        gSaved00.name = "cha_grindor_official_00";
        AssetDatabase.CreateAsset(gSaved00, "Assets/Vortex/Grindor/cha_grindor_official_00.asset");

        Mesh gSaved01 = Object.Instantiate(gSmr01.sharedMesh);
        gSaved01.name = "cha_grindor_official_01";
        AssetDatabase.CreateAsset(gSaved01, "Assets/Vortex/Grindor/cha_grindor_official_01.asset");

        Avatar officialAvatar00 = gPrefab.GetComponent<Animator>() != null ? gPrefab.GetComponent<Animator>().avatar : null;
        Transform prefabTr = FindChildRecursive(gPrefab.transform, "transformed");
        Avatar officialAvatar01 = (prefabTr != null && prefabTr.GetComponent<Animator>() != null) ? prefabTr.GetComponent<Animator>().avatar : null;

        // 3. Create Standard Shader Materials for Official Grindor Reference
        Material matGMain = AssetDatabase.LoadAssetAtPath<Material>("Assets/Vortex/Grindor/M_Grindor_Main.mat");
        if (matGMain == null) {
            matGMain = new Material(Shader.Find("Standard"));
            matGMain.name = "M_Grindor_Main";
            Texture2D a = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Vortex/Grindor/cha_grindor_cin_rotf_main_a.png");
            Texture2D n = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Vortex/Grindor/main_NM.png");
            if (a != null) matGMain.mainTexture = a;
            if (n != null) { matGMain.SetTexture("_BumpMap", n); matGMain.EnableKeyword("_NORMALMAP"); }
            matGMain.SetFloat("_Glossiness", 0.40f);
            matGMain.SetFloat("_Metallic", 0.25f);
            AssetDatabase.CreateAsset(matGMain, "Assets/Vortex/Grindor/M_Grindor_Main.mat");
        }

        Material matGMisc = AssetDatabase.LoadAssetAtPath<Material>("Assets/Vortex/Grindor/M_Grindor_Misc.mat");
        if (matGMisc == null) {
            matGMisc = new Material(Shader.Find("Standard"));
            matGMisc.name = "M_Grindor_Misc";
            Texture2D a = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Vortex/Grindor/tform_misc_A.png");
            Texture2D n = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Vortex/Grindor/tform_misc_NM.png");
            if (a != null) matGMisc.mainTexture = a;
            if (n != null) { matGMisc.SetTexture("_BumpMap", n); matGMisc.EnableKeyword("_NORMALMAP"); }
            matGMisc.SetFloat("_Glossiness", 0.35f);
            matGMisc.SetFloat("_Metallic", 0.30f);
            AssetDatabase.CreateAsset(matGMisc, "Assets/Vortex/Grindor/M_Grindor_Misc.mat");
        }

        Material matGWpns = AssetDatabase.LoadAssetAtPath<Material>("Assets/Vortex/Grindor/M_Grindor_Wpns.mat");
        if (matGWpns == null) {
            matGWpns = new Material(Shader.Find("Standard"));
            matGWpns.name = "M_Grindor_Wpns";
            Texture2D a = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Vortex/Grindor/cha_grindor_cin_rotf_wpns_a.png");
            Texture2D n = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Vortex/Grindor/wpns_NM.png");
            if (a != null) matGWpns.mainTexture = a;
            if (n != null) { matGWpns.SetTexture("_BumpMap", n); matGWpns.EnableKeyword("_NORMALMAP"); }
            matGWpns.SetFloat("_Glossiness", 0.45f);
            matGWpns.SetFloat("_Metallic", 0.35f);
            AssetDatabase.CreateAsset(matGWpns, "Assets/Vortex/Grindor/M_Grindor_Wpns.mat");
        }

        // 4. Create Standard Shader Materials for Vortex Candidate
        Material vtxMat = AssetDatabase.LoadAssetAtPath<Material>("Assets/Vortex/M_Vortex_Main.mat");
        if (vtxMat == null) {
            vtxMat = new Material(Shader.Find("Standard"));
            vtxMat.name = "M_Vortex_Main";
            Texture2D albedo = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Vortex/cha_vortex_main_a.png");
            Texture2D normal = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Vortex/cha_vortex_main_NM_unity.png");
            Texture2D emis = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Vortex/cha_vortex_main_Emission.png");
            if (albedo != null) vtxMat.mainTexture = albedo;
            if (normal != null) { vtxMat.SetTexture("_BumpMap", normal); vtxMat.EnableKeyword("_NORMALMAP"); }
            if (emis != null) {
                vtxMat.SetTexture("_EmissionMap", emis);
                vtxMat.SetColor("_EmissionColor", Color.white);
                vtxMat.EnableKeyword("_EMISSION");
            }
            vtxMat.SetFloat("_Glossiness", 0.45f);
            AssetDatabase.CreateAsset(vtxMat, "Assets/Vortex/M_Vortex_Main.mat");
        }

        Material vtxVhMat = AssetDatabase.LoadAssetAtPath<Material>("Assets/Vortex/M_Vortex_Vh.mat");
        if (vtxVhMat == null) {
            vtxVhMat = new Material(Shader.Find("Standard"));
            vtxVhMat.name = "M_Vortex_Vh";
            Texture2D albedoVh = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Vortex/cha_vortex_vh_a.png");
            Texture2D normalVh = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Vortex/cha_vortex_vh_NM_unity.png");
            if (albedoVh != null) vtxVhMat.mainTexture = albedoVh;
            if (normalVh != null) { vtxVhMat.SetTexture("_BumpMap", normalVh); vtxVhMat.EnableKeyword("_NORMALMAP"); }
            vtxVhMat.SetFloat("_Glossiness", 0.45f);
            AssetDatabase.CreateAsset(vtxVhMat, "Assets/Vortex/M_Vortex_Vh.mat");
        }

        // 5. Create Scene & Studio Lighting
        string scenePath = "Assets/Scenes/Vortex_Inspection.unity";
        Directory.CreateDirectory(Path.Combine(Application.dataPath, "Scenes"));
        Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        GameObject keyLight = new GameObject("Key Light");
        var kl = keyLight.AddComponent<Light>();
        kl.type = LightType.Directional;
        kl.intensity = 1.35f;
        kl.color = new Color(1.0f, 0.98f, 0.95f);
        keyLight.transform.rotation = Quaternion.Euler(28f, -25f, 0f);

        GameObject fillLight = new GameObject("Fill Light");
        var fl = fillLight.AddComponent<Light>();
        fl.type = LightType.Directional;
        fl.intensity = 0.65f;
        fl.color = new Color(0.85f, 0.92f, 1.0f);
        fillLight.transform.rotation = Quaternion.Euler(35f, 155f, 0f);

        GameObject rimLight = new GameObject("Rim Light");
        var rl = rimLight.AddComponent<Light>();
        rl.type = LightType.Directional;
        rl.intensity = 0.95f;
        rl.color = new Color(1.0f, 0.95f, 0.90f);
        rimLight.transform.rotation = Quaternion.Euler(-18f, 180f, 0f);

        GameObject camGo = new GameObject("Main Camera");
        camGo.tag = "MainCamera";
        Camera cam = camGo.AddComponent<Camera>();
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color(0.14f, 0.15f, 0.18f, 1.0f);
        cam.fieldOfView = 36f;
        cam.nearClipPlane = 0.1f;
        cam.farClipPlane = 150f;
        camGo.transform.position = new Vector3(0f, 6.2f, 23.5f);
        camGo.transform.LookAt(new Vector3(0f, 5.8f, 0f));

        // 6. Instantiate Official Grindor (Left of camera view: X = +3.3f)
        GameObject gInst = Object.Instantiate(gPrefab);
        gInst.name = "Grindor_Official_Reference";
        gInst.transform.position = new Vector3(3.3f, 0f, 0f);
        gInst.transform.rotation = Quaternion.Euler(0f, 0f, 0f); // Faces camera (+Z) cleanly!

        // Assign PBR Standard materials to Grindor
        foreach (var smr in gInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name.Contains("_00") && !smr.name.Contains("wpns")) {
                smr.sharedMaterials = new Material[] { matGMain, matGMisc };
                smr.updateWhenOffscreen = true;
            } else if (smr.name.Contains("_01")) {
                smr.sharedMaterials = new Material[] { matGMisc, matGMain };
                smr.updateWhenOffscreen = true;
            } else if (smr.name.Contains("wpns")) {
                smr.sharedMaterials = new Material[] { matGWpns };
                smr.updateWhenOffscreen = true;
            }
        }

        // 7. Instantiate Vortex Candidate (Right of camera view: X = -3.3f)
        GameObject vtxInst = Object.Instantiate(gPrefab);
        vtxInst.name = "Vortex_Candidate";
        vtxInst.transform.position = new Vector3(-3.3f, 0f, 0f);
        vtxInst.transform.rotation = Quaternion.Euler(0f, 0f, 0f); // Faces camera (+Z) cleanly!

        // Remove Grindor's weapons and fx on Vortex candidate (Vortex has his own Ion Blades!)
        List<GameObject> toDestroy = new List<GameObject>();
        foreach (var r in vtxInst.GetComponentsInChildren<Renderer>(true)) {
            string ln = r.gameObject.name.ToLower();
            if (ln.Contains("wpns") || ln.Contains("tailrotor") || ln.Contains("missile") || ln.Contains("fx_")) {
                toDestroy.Add(r.gameObject);
            }
        }
        foreach (var go in toDestroy) {
            Object.DestroyImmediate(go);
        }

        // Graft Vehicle Mesh on Vortex candidate using authoritative Grindor bindposes (solid bodyBase grafting!)
        GameObject vhFbx = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Vortex/vortex_vh_prepared.fbx");
        if (vhFbx != null && gSmr01 != null) {
            SkinnedMeshRenderer vhSmr = vhFbx.GetComponentInChildren<SkinnedMeshRenderer>(true);
            if (vhSmr != null && vhSmr.sharedMesh != null) {
                int bodyBoneIdx = 0;
                int rotorBoneIdx = 3; // RotorMain default
                for (int i = 0; i < gSmr01.bones.Length; i++) {
                    string bn = gSmr01.bones[i].name;
                    if (bn == "RotorMain") {
                        rotorBoneIdx = i;
                    }
                    if (bn == "BodyTopCenterRight" || bn == "BodyMainCenterTopLeft" || bn == "BodyMainCenterTopRight") {
                        bodyBoneIdx = i;
                    }
                }

                // Find RotorMain bone index on imported FBX SMR
                int fbxRotorBoneIdx = -1;
                for (int i = 0; i < vhSmr.bones.Length; i++) {
                    if (vhSmr.bones[i].name == "RotorMain") {
                        fbxRotorBoneIdx = i;
                        break;
                    }
                }

                Mesh rawMesh = vhSmr.sharedMesh;
                Mesh vhMesh = new Mesh();
                vhMesh.name = "cha_vortex_gs_01";

                Vector3[] origVerts = rawMesh.vertices;
                Vector3[] origNorms = rawMesh.normals;
                Vector4[] origTangs = rawMesh.tangents;
                BoneWeight[] rawBws = rawMesh.boneWeights;
                Vector3[] newVerts = new Vector3[origVerts.Length];
                Vector3[] newNorms = new Vector3[origNorms.Length];
                Vector4[] newTangs = new Vector4[origTangs.Length];

                // Compute pure rotor center from rawBws (where boneIndex0 == fbxRotorBoneIdx)
                Vector3 rawRotorCenter = Vector3.zero;
                int rotorCount = 0;
                for (int i = 0; i < rawBws.Length; i++) {
                    if (rawBws[i].boneIndex0 == fbxRotorBoneIdx && rawBws[i].weight0 > 0.5f) {
                        rawRotorCenter += origVerts[i];
                        rotorCount++;
                    }
                }
                if (rotorCount > 0) rawRotorCenter /= rotorCount;
                Debug.Log($"[Vortex Vehicle] Identified {rotorCount} pure rotor vertices from FBX bone weights! Raw Rotor Center: {rawRotorCenter}");

                // Grindor authoritative RotorMain rest world position: (0, 4.0218, 0.1604)
                Vector3 targetRotorPos = new Vector3(0f, 4.0218f, 0.1604f);

                // Rotation: Pitch down 90 deg + Roll 180 deg (x' = -x, y' = z, z' = y)
                // Offset calculation to align rotor hub center with targetRotorPos with 0.000mm error
                float dx = targetRotorPos.x - (-rawRotorCenter.x);
                float dy = targetRotorPos.y - rawRotorCenter.z;
                float dz = targetRotorPos.z - rawRotorCenter.y;
                Debug.Log($"[Vortex Vehicle] Target Pos: {targetRotorPos}, Offsets: dx={dx:F4}, dy={dy:F4}, dz={dz:F4}");

                for (int vi = 0; vi < origVerts.Length; vi++) {
                    Vector3 v = origVerts[vi];
                    newVerts[vi] = new Vector3(-v.x + dx, v.z + dy, v.y + dz);
                }
                for (int vi = 0; vi < origNorms.Length; vi++) {
                    Vector3 n = origNorms[vi];
                    newNorms[vi] = new Vector3(-n.x, n.z, n.y);
                }
                for (int vi = 0; vi < origTangs.Length; vi++) {
                    Vector4 t = origTangs[vi];
                    newTangs[vi] = new Vector4(-t.x, t.z, t.y, t.w);
                }

                vhMesh.vertices = newVerts;
                vhMesh.normals = newNorms;
                vhMesh.tangents = newTangs;
                vhMesh.uv = rawMesh.uv;
                vhMesh.subMeshCount = rawMesh.subMeshCount;
                for (int sm = 0; sm < rawMesh.subMeshCount; sm++) {
                    vhMesh.SetTriangles(rawMesh.GetTriangles(sm), sm);
                }
                vhMesh.bindposes = gSmr01.sharedMesh.bindposes;

                BoneWeight[] bws = new BoneWeight[rawMesh.vertexCount];
                for (int vi = 0; vi < rawMesh.vertexCount; vi++) {
                    if (rawBws[vi].boneIndex0 == fbxRotorBoneIdx && rawBws[vi].weight0 > 0.5f) {
                        bws[vi] = new BoneWeight { boneIndex0 = rotorBoneIdx, weight0 = 1.0f };
                    } else {
                        bws[vi] = new BoneWeight { boneIndex0 = bodyBoneIdx, weight0 = 1.0f };
                    }
                }
                vhMesh.boneWeights = bws;
                vhMesh.RecalculateBounds();

                AssetDatabase.CreateAsset(vhMesh, "Assets/Vortex/cha_vortex_vh_grafted.asset");
                foreach (var s in vtxInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
                    if (s.name.Contains("_01") || s.name.ToLower().Contains("vehicle")) {
                        s.sharedMesh = vhMesh;
                        s.sharedMaterials = new Material[] { vtxVhMat };
                        s.updateWhenOffscreen = true;
                    }
                }
            }
        }

        // Clean missing MonoBehaviour scripts on both instances
        foreach (var t in gInst.GetComponentsInChildren<Transform>(true)) {
            GameObjectUtility.RemoveMonoBehavioursWithMissingScript(t.gameObject);
        }
        foreach (var t in vtxInst.GetComponentsInChildren<Transform>(true)) {
            GameObjectUtility.RemoveMonoBehavioursWithMissingScript(t.gameObject);
        }

        // Rebuild Robot flexible fingers & graft mesh
        VortexHandFixer.RebuildFlexibleFingers();

        // Attach controller & tester
        var mgrGo = new GameObject("AnimationPreviewManager");
        var ctrl = mgrGo.AddComponent<VortexPreviewController>();
        ctrl.animGrindor = gInst.GetComponent<Animator>();
        ctrl.animVortex = vtxInst.GetComponent<Animator>();

        if (officialAvatar00 != null) {
            ctrl.animGrindor.avatar = officialAvatar00;
            ctrl.animVortex.avatar = officialAvatar00;
        }

        EditorSceneManager.SaveScene(scene, scenePath);
        Debug.Log("[✓] Saved Vortex_Inspection.unity scene successfully!");

        // 8. Capture 9 SBS Verification Screenshots + 3 Finger Close-ups
        string outDir = @"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d";
        Directory.CreateDirectory(outDir);

        Dictionary<string, AnimationClip> allClips = new Dictionary<string, AnimationClip>();
        foreach (var c in gBundle.LoadAllAssets<AnimationClip>()) {
            allClips[c.name] = c;
        }

        int w = 1920, h = 1080;
        RenderTexture rt = new RenderTexture(w, h, 24, RenderTextureFormat.ARGB32);
        Texture2D ss = new Texture2D(w, h, TextureFormat.RGB24, false);

        Transform trG = FindChildRecursive(gInst.transform, "transformed");
        Transform trV = FindChildRecursive(vtxInst.transform, "transformed");

        SkinnedMeshRenderer vtxSmr00 = null;
        SkinnedMeshRenderer vtxSmr01 = null;
        foreach (var smr in vtxInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (smr.name.Contains("_01") || smr.name.ToLower().Contains("vehicle")) vtxSmr01 = smr;
            else if (vtxSmr00 == null && !smr.name.Contains("wpns")) vtxSmr00 = smr;
        }

        Animator animG = gInst.GetComponent<Animator>();
        Animator animV = vtxInst.GetComponent<Animator>();

        // Save initial rest transforms
        Dictionary<Transform, Vector3> initPos = new Dictionary<Transform, Vector3>();
        Dictionary<Transform, Quaternion> initRot = new Dictionary<Transform, Quaternion>();
        foreach (var t in gInst.GetComponentsInChildren<Transform>(true)) { initPos[t] = t.localPosition; initRot[t] = t.localRotation; }
        foreach (var t in vtxInst.GetComponentsInChildren<Transform>(true)) { initPos[t] = t.localPosition; initRot[t] = t.localRotation; }

        void RestoreInitialPose() {
            foreach (var kvp in initPos) if (kvp.Key != null) kvp.Key.localPosition = kvp.Value;
            foreach (var kvp in initRot) if (kvp.Key != null) kvp.Key.localRotation = kvp.Value;
        }

        void RenderPoseShot(string clipName, float sampleTime, Vector3 camPos, Vector3 lookTarget, string fileName, bool vehicleMode = false, string transClipName = null) {
            RestoreInitialPose();

            SkinnedMeshRenderer gActiveSmr = null;
            foreach (var smr in gInst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
                if (smr.name.Contains("_00") && !smr.name.Contains("wpns")) { smr.enabled = !vehicleMode; if (!vehicleMode) gActiveSmr = smr; }
                else if (smr.name.Contains("_01")) { smr.gameObject.SetActive(true); smr.enabled = vehicleMode; if (vehicleMode) gActiveSmr = smr; }
            }
            if (vtxSmr00 != null) vtxSmr00.enabled = !vehicleMode;
            if (vtxSmr01 != null) { vtxSmr01.gameObject.SetActive(true); vtxSmr01.enabled = vehicleMode; }
            SkinnedMeshRenderer vtxActiveSmr = vehicleMode ? vtxSmr01 : vtxSmr00;

            // Evaluate animation using PlayableGraph with official Mecanim Avatars
            if (clipName != null && allClips.TryGetValue(clipName, out AnimationClip c)) {
                var graph = PlayableGraph.Create("PoseGraph");
                graph.SetTimeUpdateMode(DirectorUpdateMode.Manual);
                var outG = AnimationPlayableOutput.Create(graph, "AnimG", animG);
                var outV = AnimationPlayableOutput.Create(graph, "AnimV", animV);
                var playG = AnimationClipPlayable.Create(graph, c);
                var playV = AnimationClipPlayable.Create(graph, c);
                playG.SetApplyFootIK(false);
                playV.SetApplyFootIK(false);
                playG.SetTime(sampleTime);
                playV.SetTime(sampleTime);
                outG.SetSourcePlayable(playG);
                outV.SetSourcePlayable(playV);
                graph.Play();
                graph.Evaluate(0.0f);
                graph.Destroy();
            }

            if (transClipName != null && allClips.TryGetValue(transClipName, out AnimationClip tc) && trG != null && trV != null) {
                tc.SampleAnimation(trG.gameObject, sampleTime);
                tc.SampleAnimation(trV.gameObject, sampleTime);
            }

            float spacing = vehicleMode ? 5.0f : 4.0f;
            gInst.transform.position = new Vector3(spacing, 0f, 0f);
            gInst.transform.rotation = Quaternion.Euler(0f, 0f, 0f);
            vtxInst.transform.position = new Vector3(-spacing, 0f, 0f);
            vtxInst.transform.rotation = Quaternion.Euler(0f, 0f, 0f);

            // BakeMesh CPU skinning for headless render
            List<GameObject> tempBakedGos = new List<GameObject>();
            List<Mesh> tempBakedMeshes = new List<Mesh>();
            foreach (var smr in new SkinnedMeshRenderer[] { gActiveSmr, vtxActiveSmr }) {
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
                }
            }

            // If vehicle mode, place baked meshes cleanly at +/- spacing
            if (vehicleMode && tempBakedGos.Count == 2) {
                for (int k = 0; k < 2; k++) {
                    var mr = tempBakedGos[k].GetComponent<MeshRenderer>();
                    Bounds wb = mr.bounds;
                    float targetX = (k == 0) ? spacing : -spacing;
                    tempBakedGos[k].transform.position += new Vector3(targetX - wb.center.x, 3.5f - wb.center.y, 0f - wb.center.z);
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
            File.WriteAllBytes(Path.Combine(outDir, fileName), ss.EncodeToPNG());
            Debug.Log("[✓] Rendered verification screenshot: " + fileName);

            foreach (var bgo in tempBakedGos) Object.DestroyImmediate(bgo);
            foreach (var bm in tempBakedMeshes) Object.DestroyImmediate(bm);
            if (gActiveSmr != null) gActiveSmr.enabled = true;
            if (vtxActiveSmr != null) vtxActiveSmr.enabled = true;
        }

        // Shot 0: Pure BindPose Rest Stance (Full body, generous margins)
        RenderPoseShot(null, 0f, new Vector3(0f, 6.2f, 23.5f), new Vector3(0f, 5.8f, 0f), "vortex_sbs_00_rest_pose.png");

        // Shot 1: Combat Idle (Front)
        RenderPoseShot("Brute_Normal_CombatIdle", 0.40f, new Vector3(0f, 6.2f, 23.5f), new Vector3(0f, 5.8f, 0f), "vortex_sbs_01_combat_idle_front.png");

        // Shot 2: Prefight Idle 3/4 Perspective
        RenderPoseShot("Prefight_Brute_idle", 0.50f, new Vector3(7.5f, 6.5f, 22.5f), new Vector3(0f, 5.8f, 0f), "vortex_sbs_02_prefight_idle_34.png");

        // Shot 3: Rear View (showing Vortex's Backpack and Rotor Engine)
        RenderPoseShot("Brute_Normal_CombatIdle", 0.40f, new Vector3(-7.5f, 6.8f, -22.5f), new Vector3(0f, 5.8f, 0f), "vortex_sbs_03_backpack_rotors_view.png");

        // Shot 4: Light Attack 1 Punch (Right hand punch with Ion Blade!)
        RenderPoseShot("brute_normal_attackLight_01_rightHandPunch", 0.35f, new Vector3(-7.5f, 6.2f, 22.5f), new Vector3(0f, 5.8f, 0f), "vortex_sbs_04_light_punch_action.png");

        // Shot 5: Heavy Attack Strike (Transform attack)
        RenderPoseShot("Grindor_Normal_attackHeavy", 0.45f, new Vector3(-7.5f, 6.2f, 22.5f), new Vector3(0f, 5.8f, 0f), "vortex_sbs_05_heavy_attack_strike.png", false, "Grindor_Normal_attackHeavy_transformed");

        // Shot 6: SP2 Rotor Slash
        RenderPoseShot("Grindor_Normal_attackSpecial_02", 0.85f, new Vector3(-7.5f, 6.2f, 22.5f), new Vector3(0f, 5.8f, 0f), "vortex_sbs_06_special_02_rotor_slash.png");

        // Shot 7: SP3 Helicopter Ultimate Strike
        RenderPoseShot("Grindor_Normal_attackSpecial_03", 1.20f, new Vector3(-7.5f, 6.2f, 22.5f), new Vector3(0f, 5.8f, 0f), "vortex_sbs_07_special_03_ultimate.png", false, "Grindor_Normal_attackSpecial_03_transformed");

        // Shot 8: Vehicle Mode Side-by-Side (Helicopter Hover)
        RenderPoseShot("frontend_Grindor_levelup_vehicle_idle", 0.50f, new Vector3(0f, 6.0f, 22.0f), new Vector3(0f, 3.5f, 0f), "vortex_sbs_08_vehicle_mode_hover.png", true, "frontend_Grindor_levelup_vehicle_idle_transformed");

        // 3 Finger Close-Up Shots (Focused on Vortex Candidate on the right: X = -4.0f)
        // Close-up 1: Rest open hand
        RestoreInitialPose();
        RenderPoseShot(null, 0f, new Vector3(-4.0f, 5.5f, 6.8f), new Vector3(-1.4f, 5.0f, 0f), "vortex_fingers_01_rest_closeup.png");

        // Close-up 2: Finger curl 45 degrees
        var tester = vtxInst.GetComponent<VortexFingerTester>();
        if (tester != null) {
            tester.curlAll = 45f;
            foreach (var b in vtxInst.GetComponentsInChildren<Transform>(true)) {
                if (b.name.Contains("HandIndex") || b.name.Contains("HandMiddle") || b.name.Contains("HandRing") || b.name.Contains("HandPinky")) {
                    b.localRotation *= Quaternion.AngleAxis(b.name.Contains("Left") ? 45f : -45f, Vector3.forward);
                }
            }
        }
        RenderPoseShot(null, 0f, new Vector3(-4.0f, 5.5f, 6.8f), new Vector3(-1.4f, 5.0f, 0f), "vortex_fingers_02_curl45_fist_closeup.png");

        // Close-up 3: Combat idle hands
        RestoreInitialPose();
        RenderPoseShot("Brute_Normal_CombatIdle", 0.40f, new Vector3(-4.0f, 5.5f, 6.8f), new Vector3(-1.4f, 5.0f, 0f), "vortex_fingers_03_combat_idle_sbs.png");

        RestoreInitialPose();
        gInst.transform.position = new Vector3(3.3f, 0f, 0f);
        gInst.transform.rotation = Quaternion.Euler(0f, 0f, 0f);
        vtxInst.transform.position = new Vector3(-3.3f, 0f, 0f);
        vtxInst.transform.rotation = Quaternion.Euler(0f, 0f, 0f);

        EditorSceneManager.SaveScene(scene, scenePath);
        EditorBuildSettings.scenes = new EditorBuildSettingsScene[] { new EditorBuildSettingsScene(scenePath, true) };
        try {
            string lastSceneSetup = "sceneSetups:\n- path: " + scenePath + "\n  isLoaded: 1\n  isActive: 1\n  isSubScene: 0\n";
            File.WriteAllText(Path.Combine(Application.dataPath, "../Library/LastSceneManagerSetup.txt"), lastSceneSetup);
            Debug.Log("[✓] Set Vortex_Inspection.unity as default active scene!");
        } catch (System.Exception ex) {
            Debug.LogWarning("Could not write LastSceneManagerSetup: " + ex.Message);
        }

        // Clean up
        cam.targetTexture = null;
        RenderTexture.active = null;
        Object.DestroyImmediate(rt);
        Object.DestroyImmediate(ss);
        gBundle.Unload(false);

        Debug.Log("[SUCCESS] All 9 SBS actions and 3 finger close-up screenshots rendered successfully!");
    }

    private static Transform FindChildRecursive(Transform parent, string childName) {
        foreach (Transform c in parent) {
            if (c.name.Equals(childName, System.StringComparison.OrdinalIgnoreCase)) return c;
            Transform found = FindChildRecursive(c, childName);
            if (found != null) return found;
        }
        return null;
    }
}
