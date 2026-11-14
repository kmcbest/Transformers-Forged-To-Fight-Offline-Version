using System;
using System.IO;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine.SceneManagement;
using UnityEditor.Animations;

public class BuildKarnakPreviewScene {
    [MenuItem("TFTF/Add Main Camera to Current Scene")]
    public static void AddCameraToCurrentScene() {
        GameObject existing = GameObject.Find("Main Camera (TFTF Combat View)");
        if (existing == null) {
            existing = new GameObject("Main Camera (TFTF Combat View)");
            existing.tag = "MainCamera";
            Camera cam = existing.AddComponent<Camera>();
            cam.clearFlags = CameraClearFlags.Skybox;
            cam.fieldOfView = 56.0f;
            existing.transform.position = new Vector3(0.0f, 3.2f, -13.0f);
            existing.transform.LookAt(new Vector3(0.0f, 2.5f, 3.0f));
            Debug.Log("[✓] Added permanent Main Camera (TFTF Combat View) to current scene!");
        } else {
            Debug.Log("[i] Camera already exists in current scene.");
        }
        EditorSceneManager.MarkSceneDirty(EditorSceneManager.GetActiveScene());
    }

    [MenuItem("TFTF/Build Karnak Combiners Preview Scene")]
    public static void BuildAndCapture() {
        Debug.Log("=== [1/6] Building Karnak Combiners Preview Scene ===");

        // 1. Ensure Directories
        string sceneDir = "Assets/Scenes";
        string matDir = "Assets/Stages/Karnak/Materials";
        string volcMatDir = "Assets/Combiners/Volcanicus/Materials";
        string vicMatDir = "Assets/Combiners/Victorion/Materials";

        if (!Directory.Exists(sceneDir)) Directory.CreateDirectory(sceneDir);
        if (!Directory.Exists(matDir)) Directory.CreateDirectory(matDir);
        if (!Directory.Exists(volcMatDir)) Directory.CreateDirectory(volcMatDir);
        if (!Directory.Exists(vicMatDir)) Directory.CreateDirectory(vicMatDir);

        // 2. Configure Texture Importers for Victorion Palette
        string vicColorTex = "Assets/Combiners/Victorion/Character_Atlas_Color.png";
        TextureImporter cImporter = AssetImporter.GetAtPath(vicColorTex) as TextureImporter;
        if (cImporter != null) {
            cImporter.filterMode = FilterMode.Point; // Crisp palette lookup
            cImporter.textureCompression = TextureImporterCompression.Uncompressed;
            cImporter.wrapMode = TextureWrapMode.Clamp;
            cImporter.SaveAndReimport();
        }

        // 3. Configure Volcanicus FBX Import & Animation
        string volcFBXPath = "Assets/Combiners/Volcanicus/Volcanicus_PingPong.fbx";
        ModelImporter volcImporter = AssetImporter.GetAtPath(volcFBXPath) as ModelImporter;
        if (volcImporter != null) {
            volcImporter.animationType = ModelImporterAnimationType.Generic;
            volcImporter.importAnimation = true;
            ModelImporterClipAnimation[] clips = volcImporter.defaultClipAnimations;
            List<ModelImporterClipAnimation> newClips = new List<ModelImporterClipAnimation>();
            foreach (var clip in clips) {
                clip.name = "Volcanicus_PingPong_Loop";
                clip.loopTime = true;
                clip.loopPose = false;
                newClips.Add(clip);
            }
            if (newClips.Count > 0) volcImporter.clipAnimations = newClips.ToArray();
            volcImporter.SaveAndReimport();
        }

        // 4. Configure Victorion FBX Import & Animation
        string vicFBXPath = "Assets/Combiners/Victorion/Victorion_PingPong.fbx";
        ModelImporter vicImporter = AssetImporter.GetAtPath(vicFBXPath) as ModelImporter;
        if (vicImporter != null) {
            vicImporter.animationType = ModelImporterAnimationType.Generic;
            vicImporter.importAnimation = true;
            ModelImporterClipAnimation[] clips = vicImporter.defaultClipAnimations;
            List<ModelImporterClipAnimation> newClips = new List<ModelImporterClipAnimation>();
            foreach (var clip in clips) {
                clip.name = "Victorion_Attack_1_Loop";
                clip.loopTime = true;
                clip.loopPose = false;
                newClips.Add(clip);
            }
            if (newClips.Count > 0) vicImporter.clipAnimations = newClips.ToArray();
            vicImporter.SaveAndReimport();
        }

        // 5. Create Combiner Materials
        Material volcBodyMat = CreateStandardMaterial(
            "Assets/Combiners/Volcanicus/Materials/M_Volcanicus.mat",
            "Assets/Combiners/Volcanicus/Tx_Volcanicus_D.png",
            "Assets/Combiners/Volcanicus/Tx_Volcanicus_N.png",
            0.35f, 0.65f);

        Material volcWeaponMat = CreateStandardMaterial(
            "Assets/Combiners/Volcanicus/Materials/M_Volcanicus_Weapon.mat",
            "Assets/Combiners/Volcanicus/Tx_Volcanicus_Weapon_D.png",
            "Assets/Combiners/Volcanicus/Tx_Volcanicus_Weapon_N.png",
            0.35f, 0.65f);

        // Victorion Body Material (Slot 1)
        Material vicBodyMat = CreateStandardMaterial(
            "Assets/Combiners/Victorion/Materials/M_Victorion_Body.mat",
            "Assets/Combiners/Victorion/Character_Atlas_Color.png",
            null, 0.35f, 0.65f, null,
            "Assets/Combiners/Victorion/Victorion_AO.png");

        // Victorion Glass Material (Slot 0)
        Material vicGlassMat = CreateStandardMaterial(
            "Assets/Combiners/Victorion/Materials/M_Victorion_Glass.mat",
            "Assets/Combiners/Victorion/Victorion_Glass_CA.png",
            null, 0.15f, 0.85f);

        // Victorion Sword Material
        Material vicSwordMat = CreateStandardMaterial(
            "Assets/Combiners/Victorion/Materials/M_Victorion_Sword.mat",
            "Assets/Combiners/Victorion/Character_Atlas_Color.png",
            null, 0.45f, 0.70f);

        // 6. Create Karnak Stage Materials
        Debug.Log("=== [2/6] Generating Karnak Stage Materials ===");
        Dictionary<string, Material> karnakMats = new Dictionary<string, Material>();
        string[] texFiles = Directory.GetFiles("Assets/Stages/Karnak/Textures", "*.png");
        foreach (string tf in texFiles) {
            string texName = Path.GetFileNameWithoutExtension(tf);
            if (texName.EndsWith("_d")) {
                string basePrefix = texName.Substring(0, texName.Length - 2);
                string normPath = $"Assets/Stages/Karnak/Textures/{basePrefix}_n.png";
                string matPath = $"Assets/Stages/Karnak/Materials/M_{basePrefix}.mat";
                Material m = CreateStandardMaterial(matPath, tf, File.Exists(normPath) ? normPath : null, 0.15f, 0.40f);
                karnakMats[basePrefix] = m;
            }
        }

        string tentTex = "Assets/Stages/Karnak/Textures/krnk_bldg_tentset.png";
        if (File.Exists(tentTex)) {
            Material tentMat = CreateStandardMaterial("Assets/Stages/Karnak/Materials/M_krnk_bldg_tentset.mat", tentTex, null, 0.1f, 0.3f);
            karnakMats["krnk_bldg_tentset"] = tentMat;
        }

        Material defaultSandMat = CreateStandardMaterial(
            "Assets/Stages/Karnak/Materials/M_DefaultSand.mat",
            "Assets/Stages/Karnak/Textures/krnk_trrn_sand_01_d.png",
            "Assets/Stages/Karnak/Textures/krnk_trrn_sand_01_n.png",
            0.10f, 0.25f);

        // 7. Create New Scene
        Debug.Log("=== [3/6] Setting Up Scene Lighting and Environment ===");
        Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        // Warm Golden Sunlight
        GameObject sunGo = new GameObject("Sun (Karnak Desert)");
        Light sun = sunGo.AddComponent<Light>();
        sun.type = LightType.Directional;
        sun.color = new Color(1.0f, 0.94f, 0.85f);
        sun.intensity = 1.35f;
        sun.shadows = LightShadows.Soft;
        sunGo.transform.rotation = Quaternion.Euler(38.0f, -42.0f, 0.0f);

        // Oasis Sky Fill Light
        GameObject fillGo = new GameObject("Sky Fill Light");
        Light fill = fillGo.AddComponent<Light>();
        fill.type = LightType.Directional;
        fill.color = new Color(0.68f, 0.78f, 0.92f);
        fill.intensity = 0.45f;
        fillGo.transform.rotation = Quaternion.Euler(-25.0f, 138.0f, 0.0f);

        // Ambient Light
        RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
        RenderSettings.ambientLight = new Color(0.42f, 0.38f, 0.33f);

        // 8. Assemble Karnak Environment
        GameObject envRoot = new GameObject("Environment_Karnak");
        string[] meshFiles = Directory.GetFiles("Assets/Stages/Karnak/Meshes", "*.obj");
        int spawnedMeshCount = 0;
        foreach (string mf in meshFiles) {
            string meshName = Path.GetFileNameWithoutExtension(mf);
            if (!meshName.StartsWith("krnk_", StringComparison.OrdinalIgnoreCase)) {
                continue;
            }

            GameObject meshPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(mf);
            if (meshPrefab != null) {
                GameObject instance = UnityEngine.Object.Instantiate(meshPrefab, envRoot.transform);
                instance.name = meshName;
                instance.transform.localPosition = Vector3.zero;
                instance.transform.localRotation = Quaternion.identity;
                instance.transform.localScale = Vector3.one;

                Renderer rend = instance.GetComponentInChildren<Renderer>();
                if (rend != null) {
                    Material matched = defaultSandMat;
                    foreach (var pair in karnakMats) {
                        if (meshName.IndexOf(pair.Key, StringComparison.OrdinalIgnoreCase) >= 0) {
                            matched = pair.Value;
                            break;
                        }
                    }
                    rend.sharedMaterial = matched;
                }
                spawnedMeshCount++;
            }
        }
        Debug.Log($"[✓] Successfully spawned {spawnedMeshCount} official Karnak stage meshes");

        // 9. Place Combiners Outside the Battlefield Disc
        Debug.Log("=== [4/6] Spawning and Placing Combiners ===");
        // Volcanicus: Left/Rear-Left theta1 = 145 deg -> X = -18.0, Z = +13.0
        // Victorion: Right/Rear-Right theta2 = 45 deg -> X = +15.5, Z = +15.5
        // Angular Separation = 100 deg (Strictly in 90~150 deg range)

        // Spawn Volcanicus
        GameObject volcPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(volcFBXPath);
        GameObject volcInstance = null;
        if (volcPrefab != null) {
            volcInstance = UnityEngine.Object.Instantiate(volcPrefab);
            volcInstance.name = "Volcanicus_Colossus";
            volcInstance.transform.position = new Vector3(-18.0f, 0.0f, 13.0f);
            volcInstance.transform.localScale = new Vector3(145.0f, 145.0f, 145.0f);
            volcInstance.transform.rotation = Quaternion.LookRotation(new Vector3(18.0f, 0.0f, -13.0f));

            foreach (Renderer r in volcInstance.GetComponentsInChildren<Renderer>()) {
                string rName = r.gameObject.name.ToLower();
                if (rName.Contains("weapon")) {
                    r.sharedMaterial = volcWeaponMat;
                } else {
                    r.sharedMaterial = volcBodyMat;
                }
                if (r is SkinnedMeshRenderer) {
                    ((SkinnedMeshRenderer)r).updateWhenOffscreen = true;
                }
            }

            string volcCtrlPath = "Assets/Combiners/Volcanicus/Volcanicus_LoopController.controller";
            AnimatorController volcCtrl = AnimatorController.CreateAnimatorControllerAtPath(volcCtrlPath);
            AnimationClip volcClip = FindClip(volcFBXPath, "Volcanicus");
            if (volcClip != null) {
                AnimatorState state = volcCtrl.layers[0].stateMachine.AddState("Assembly_PingPong_Loop");
                state.motion = volcClip;
            }
            Animator anim = volcInstance.GetComponent<Animator>();
            if (anim == null) anim = volcInstance.AddComponent<Animator>();
            anim.runtimeAnimatorController = volcCtrl;
            anim.cullingMode = AnimatorCullingMode.AlwaysAnimate;
            Debug.Log("[✓] Spawned Volcanicus at (-18.0, 0, 13.0), Scale=(88,88,88), Facing Center");
        }

        // Spawn Victorion
        GameObject vicPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(vicFBXPath);
        GameObject vicInstance = null;
        if (vicPrefab != null) {
            vicInstance = UnityEngine.Object.Instantiate(vicPrefab);
            vicInstance.name = "Victorion_Colossus";
            vicInstance.transform.position = new Vector3(15.5f, 0.0f, 15.5f);
            vicInstance.transform.localScale = new Vector3(38.0f, 38.0f, 38.0f);
            vicInstance.transform.rotation = Quaternion.LookRotation(new Vector3(-15.5f, 0.0f, -15.5f));

            foreach (Renderer r in vicInstance.GetComponentsInChildren<Renderer>()) {
                string rName = r.gameObject.name.ToLower();
                if (rName.Contains("sword")) {
                    r.sharedMaterials = new Material[] { vicSwordMat };
                } else {
                    // Victorion_Mesh has 2 slots: Slot 0 = Glass, Slot 1 = Body
                    r.sharedMaterials = new Material[] { vicGlassMat, vicBodyMat };
                }
                if (r is SkinnedMeshRenderer) {
                    ((SkinnedMeshRenderer)r).updateWhenOffscreen = true;
                }
            }

            string vicCtrlPath = "Assets/Combiners/Victorion/Victorion_LoopController.controller";
            AnimatorController vicCtrl = AnimatorController.CreateAnimatorControllerAtPath(vicCtrlPath);
            AnimationClip vicClip = FindClip(vicFBXPath, "Victorion");
            if (vicClip != null) {
                AnimatorState state = vicCtrl.layers[0].stateMachine.AddState("Attack_PingPong_Loop");
                state.motion = vicClip;
            }
            Animator anim = vicInstance.GetComponent<Animator>();
            if (anim == null) anim = vicInstance.AddComponent<Animator>();
            anim.runtimeAnimatorController = vicCtrl;
            anim.cullingMode = AnimatorCullingMode.AlwaysAnimate;
            Debug.Log("[✓] Spawned Victorion at (15.5, 0, 15.5), Scale=(38,38,38), Facing Center");
        }

        // 10. Add Reference Combatants in Center Ring
        GameObject p1 = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        p1.name = "Fighter_P1_Autobot (Reference)";
        p1.transform.position = new Vector3(-2.8f, 1.0f, 0.0f);
        p1.transform.localScale = new Vector3(0.9f, 1.0f, 0.9f);
        Material p1Mat = new Material(Shader.Find("Standard"));
        p1Mat.color = new Color(0.2f, 0.5f, 0.95f);
        p1.GetComponent<Renderer>().sharedMaterial = p1Mat;

        GameObject p2 = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        p2.name = "Fighter_P2_Decepticon (Reference)";
        p2.transform.position = new Vector3(2.8f, 1.0f, 0.0f);
        p2.transform.localScale = new Vector3(0.9f, 1.0f, 0.9f);
        Material p2Mat = new Material(Shader.Find("Standard"));
        p2Mat.color = new Color(0.95f, 0.2f, 0.2f);
        p2.GetComponent<Renderer>().sharedMaterial = p2Mat;

        // 10. Add Permanent Main Camera (TFTF Combat View)
        GameObject mainCamGo = new GameObject("Main Camera (TFTF Combat View)");
        mainCamGo.tag = "MainCamera";
        Camera mainCam = mainCamGo.AddComponent<Camera>();
        mainCam.clearFlags = CameraClearFlags.Skybox;
        mainCam.fieldOfView = 56.0f;
        mainCamGo.transform.position = new Vector3(0.0f, 3.2f, -13.0f);
        mainCamGo.transform.LookAt(new Vector3(0.0f, 2.5f, 3.0f));

        // 11. Save Scene
        string scenePath = "Assets/Scenes/Karnak_Combiners_Stage.unity";
        EditorSceneManager.SaveScene(scene, scenePath);
        Debug.Log($"[✓] Saved scene with permanent Main Camera to: {scenePath}");

        // 12. Sample Animations & Capture Preview Screenshots
        Debug.Log("=== [5/6] Sampling Poses & Capturing Preview Screenshots ===");
        if (volcInstance != null) {
            AnimationClip vClip = FindClip(volcFBXPath, "Volcanicus");
            if (vClip != null) vClip.SampleAnimation(volcInstance, 4.0f);
        }
        if (vicInstance != null) {
            AnimationClip vicClip = FindClip(vicFBXPath, "Victorion");
            if (vicClip != null) vicClip.SampleAnimation(vicInstance, 2.0f);
        }

        // Camera 1: TFTF Combat View (Foreground arena, both combiners towering in the background)
        CaptureCameraView(
            "Main Combat View",
            new Vector3(0.0f, 3.2f, -13.0f),
            new Vector3(0.0f, 2.5f, 3.0f),
            56.0f,
            "E:/Agent/TFTF-blender/stage_karnak_combat_view.png");

        // Camera 2: Wide Arena Overview (High panoramic angle displaying circular separation & disc)
        CaptureCameraView(
            "Wide Arena View",
            new Vector3(0.0f, 22.0f, -32.0f),
            new Vector3(0.0f, 3.0f, 10.0f),
            55.0f,
            "E:/Agent/TFTF-blender/stage_karnak_wide_overview.png");

        // Camera 3: Volcanicus Closeup
        CaptureCameraView(
            "Volcanicus Hero Closeup",
            new Vector3(-12.0f, 4.8f, 7.5f),
            new Vector3(-18.0f, 4.8f, 13.0f),
            45.0f,
            "E:/Agent/TFTF-blender/stage_karnak_volcanicus_closeup.png");

        // Camera 4: Victorion Closeup
        CaptureCameraView(
            "Victorion Hero Closeup",
            new Vector3(9.5f, 4.8f, 9.5f),
            new Vector3(15.5f, 4.8f, 15.5f),
            45.0f,
            "E:/Agent/TFTF-blender/stage_karnak_victorion_closeup.png");

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("=== [6/6] Karnak Combiners Preview Scene Build & Capture Complete! ===");
    }

    private static AnimationClip FindClip(string fbxPath, string nameHint) {
        UnityEngine.Object[] assets = AssetDatabase.LoadAllAssetsAtPath(fbxPath);
        foreach (var a in assets) {
            if (a is AnimationClip && !a.name.StartsWith("__preview__")) {
                return a as AnimationClip;
            }
        }
        return null;
    }

    private static void CaptureCameraView(string camName, Vector3 pos, Vector3 target, float fov, string outPath) {
        GameObject camGo = new GameObject(camName);
        Camera cam = camGo.AddComponent<Camera>();
        cam.clearFlags = CameraClearFlags.Skybox;
        cam.fieldOfView = fov;
        cam.cullingMask = -1;
        camGo.transform.position = pos;
        camGo.transform.LookAt(target);

        int width = 1920;
        int height = 1080;
        RenderTexture rt = new RenderTexture(width, height, 24);
        cam.targetTexture = rt;
        Texture2D screenShot = new Texture2D(width, height, TextureFormat.RGB24, false);

        cam.Render();
        RenderTexture.active = rt;
        screenShot.ReadPixels(new Rect(0, 0, width, height), 0, 0);
        screenShot.Apply();

        cam.targetTexture = null;
        RenderTexture.active = null;
        UnityEngine.Object.DestroyImmediate(rt);
        UnityEngine.Object.DestroyImmediate(camGo);

        byte[] bytes = screenShot.EncodeToPNG();
        File.WriteAllBytes(outPath, bytes);
        Debug.Log($"[✓] Captured '{camName}' ({width}x{height}) to: {outPath}");
    }

    private static Material CreateStandardMaterial(
        string matPath,
        string diffuseTexPath,
        string normalTexPath = null,
        float metallic = 0.2f,
        float glossiness = 0.35f,
        string emissionTexPath = null,
        string occlusionTexPath = null) {

        Material mat = AssetDatabase.LoadAssetAtPath<Material>(matPath);
        if (mat == null) {
            mat = new Material(Shader.Find("Standard"));
            AssetDatabase.CreateAsset(mat, matPath);
        }

        mat.SetFloat("_Metallic", metallic);
        mat.SetFloat("_Glossiness", glossiness);

        // Reset emission
        mat.DisableKeyword("_EMISSION");
        mat.SetColor("_EmissionColor", Color.black);
        mat.SetTexture("_EmissionMap", null);

        if (!string.IsNullOrEmpty(diffuseTexPath) && File.Exists(diffuseTexPath)) {
            Texture2D tex = AssetDatabase.LoadAssetAtPath<Texture2D>(diffuseTexPath);
            if (tex != null) mat.SetTexture("_MainTex", tex);
        }

        if (!string.IsNullOrEmpty(normalTexPath) && File.Exists(normalTexPath)) {
            TextureImporter nImporter = AssetImporter.GetAtPath(normalTexPath) as TextureImporter;
            if (nImporter != null && nImporter.textureType != TextureImporterType.NormalMap) {
                nImporter.textureType = TextureImporterType.NormalMap;
                nImporter.SaveAndReimport();
            }
            Texture2D nTex = AssetDatabase.LoadAssetAtPath<Texture2D>(normalTexPath);
            if (nTex != null) {
                mat.EnableKeyword("_NORMALMAP");
                mat.SetTexture("_BumpMap", nTex);
            }
        }

        if (!string.IsNullOrEmpty(occlusionTexPath) && File.Exists(occlusionTexPath)) {
            Texture2D oTex = AssetDatabase.LoadAssetAtPath<Texture2D>(occlusionTexPath);
            if (oTex != null) {
                mat.SetTexture("_OcclusionMap", oTex);
                mat.SetFloat("_OcclusionStrength", 0.75f);
            }
        }

        EditorUtility.SetDirty(mat);
        return mat;
    }
}
