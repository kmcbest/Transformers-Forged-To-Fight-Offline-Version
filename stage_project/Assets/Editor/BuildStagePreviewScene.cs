using System;
using System.IO;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine.SceneManagement;
using UnityEditor.Animations;

public class BuildStagePreviewScene {
    [MenuItem("TFTF/Build Rust Sea Devastator Scene")]
    public static void Build() {
        Debug.Log("=== Starting Rust Sea Devastator Stage Build ===");

        // 1. Ensure Directories
        string sceneDir = "Assets/Scenes";
        string matDir = "Assets/Stages/Rust/Materials";
        string devMatDir = "Assets/Devastator/Materials";
        if (!Directory.Exists(sceneDir)) Directory.CreateDirectory(sceneDir);
        if (!Directory.Exists(matDir)) Directory.CreateDirectory(matDir);
        if (!Directory.Exists(devMatDir)) Directory.CreateDirectory(devMatDir);

        // 2. Configure Devastator FBX
        string fbxPath = "Assets/Devastator/Devastator.fbx";
        ModelImporter devImporter = AssetImporter.GetAtPath(fbxPath) as ModelImporter;
        if (devImporter != null) {
            devImporter.animationType = ModelImporterAnimationType.Generic;
            devImporter.importAnimation = true;

            ModelImporterClipAnimation[] clips = devImporter.defaultClipAnimations;
            List<ModelImporterClipAnimation> newClips = new List<ModelImporterClipAnimation>();
            foreach (var clip in clips) {
                if (clip.name.IndexOf("transform_r_garage", StringComparison.OrdinalIgnoreCase) >= 0) {
                    clip.name = "Devastator_Combine";
                    clip.loopTime = true;
                    clip.loopPose = true;
                    newClips.Add(clip);
                    Debug.Log("[✓] Found and configured Devastator_Combine looping animation clip!");
                }
            }
            if (newClips.Count > 0) {
                devImporter.clipAnimations = newClips.ToArray();
            }
            devImporter.SaveAndReimport();
        }

        // 3. Create Devastator Materials
        Material devMat = CreateStandardMaterial("Assets/Devastator/Materials/M_Devastator.mat",
            "Assets/Devastator/Textures/Tx_Devastator_D.png",
            "Assets/Devastator/Textures/Tx_Devastator_N.png");

        Material catMat = CreateStandardMaterial("Assets/Devastator/Materials/M_Caterpillar.mat",
            "Assets/Devastator/Textures/Tx_Megatron_Caterpillar_D.png",
            "Assets/Devastator/Textures/Tx_Megatron_Caterpillar_N.png");

        Material wpnMat = CreateStandardMaterial("Assets/Devastator/Materials/M_Weapon.mat",
            "Assets/Devastator/Textures/Tx_Devastator_Weapon_D.png",
            "Assets/Devastator/Textures/Tx_Devastator_Weapon_N.png");

        // 4. Create materials for Rust stage
        Dictionary<string, Material> rustMats = new Dictionary<string, Material>();
        string[] texFiles = Directory.GetFiles("Assets/Stages/Rust/Textures", "*.png");
        foreach (string tf in texFiles) {
            string texName = Path.GetFileNameWithoutExtension(tf);
            if (texName.EndsWith("_d")) {
                string basePrefix = texName.Substring(0, texName.Length - 2);
                string normPath = $"Assets/Stages/Rust/Textures/{basePrefix}_n.png";
                string matPath = $"Assets/Stages/Rust/Materials/M_{basePrefix}.mat";
                Material m = CreateStandardMaterial(matPath, tf, File.Exists(normPath) ? normPath : null);
                rustMats[basePrefix] = m;
            }
        }

        // 5. Create Scene
        Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        // 6. Lighting & Atmosphere
        GameObject sunGo = new GameObject("Sun (Rust Sea)");
        Light sun = sunGo.AddComponent<Light>();
        sun.type = LightType.Directional;
        sun.color = new Color(1.0f, 0.88f, 0.72f);
        sun.intensity = 1.35f;
        sun.shadows = LightShadows.Soft;
        sunGo.transform.rotation = Quaternion.Euler(35.0f, -35.0f, 0.0f);

        GameObject fillLightGo = new GameObject("Sky Fill Light");
        Light fillLight = fillLightGo.AddComponent<Light>();
        fillLight.type = LightType.Directional;
        fillLight.color = new Color(0.65f, 0.75f, 0.9f);
        fillLight.intensity = 0.5f;
        fillLightGo.transform.rotation = Quaternion.Euler(-20.0f, 145.0f, 0.0f);

        RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
        RenderSettings.ambientLight = new Color(0.38f, 0.35f, 0.32f);

        // 7. Spawn Stage Environment Meshes
        GameObject envRoot = new GameObject("Environment_RustSea");
        string[] meshFiles = Directory.GetFiles("Assets/Stages/Rust/Meshes", "*.obj");

        Material defaultSandMat = CreateStandardMaterial("Assets/Stages/Rust/Materials/M_DefaultSand.mat",
            "Assets/Stages/Rust/Textures/rust_trrn_platform_03_d.png",
            "Assets/Stages/Rust/Textures/rust_trrn_platform_03_n.png");

        foreach (string mf in meshFiles) {
            string meshName = Path.GetFileNameWithoutExtension(mf);
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
                    foreach (var pair in rustMats) {
                        if (meshName.IndexOf(pair.Key, StringComparison.OrdinalIgnoreCase) >= 0) {
                            matched = pair.Value;
                            break;
                        }
                    }
                    rend.sharedMaterial = matched;
                }
            }
        }

        // 8. Spawn Devastator in the Background
        GameObject devPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
        if (devPrefab != null) {
            GameObject devInstance = UnityEngine.Object.Instantiate(devPrefab);
            devInstance.name = "Devastator_Colossus";
            // Set true colossus scale and position in the background
            devInstance.transform.localScale = new Vector3(550.0f, 550.0f, 550.0f);
            devInstance.transform.position = new Vector3(0.0f, 1.0f, 26.0f);
            devInstance.transform.rotation = Quaternion.Euler(0.0f, 180.0f, 0.0f);

            // Assign materials
            foreach (Renderer r in devInstance.GetComponentsInChildren<Renderer>()) {
                string rName = r.gameObject.name.ToLower();
                if (rName.Contains("caterpillar")) {
                    r.sharedMaterial = catMat;
                } else if (rName.Contains("weapon")) {
                    r.sharedMaterial = wpnMat;
                } else {
                    r.sharedMaterial = devMat;
                }
            }

            // Create Animator Controller
            string controllerPath = "Assets/Devastator/Devastator_CombineController.controller";
            AnimatorController controller = AnimatorController.CreateAnimatorControllerAtPath(controllerPath);

            AnimationClip combineClip = null;
            UnityEngine.Object[] assets = AssetDatabase.LoadAllAssetsAtPath(fbxPath);
            foreach (var a in assets) {
                if (a is AnimationClip && a.name.IndexOf("combine", StringComparison.OrdinalIgnoreCase) >= 0) {
                    combineClip = a as AnimationClip;
                    break;
                }
            }
            if (combineClip == null) {
                foreach (var a in assets) {
                    if (a is AnimationClip && !a.name.StartsWith("__preview__")) {
                        combineClip = a as AnimationClip;
                        break;
                    }
                }
            }

            if (combineClip != null) {
                AnimatorStateMachine sm = controller.layers[0].stateMachine;
                AnimatorState state = sm.AddState("Combining_Loop");
                state.motion = combineClip;
                Debug.Log($"[✓] Attached clip '{combineClip.name}' to AnimatorController");
            }

            Animator animator = devInstance.GetComponent<Animator>();
            if (animator == null) animator = devInstance.AddComponent<Animator>();
            animator.runtimeAnimatorController = controller;
            animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;
        }

        // 9. Add Reference Combatants
        GameObject p1 = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        p1.name = "Fighter_P1_Autobot (Reference)";
        p1.transform.position = new Vector3(-2.8f, 1.0f, 0.0f);
        p1.transform.localScale = new Vector3(0.9f, 1.0f, 0.9f);
        Material p1Mat = new Material(Shader.Find("Standard"));
        p1Mat.color = new Color(0.2f, 0.5f, 0.9f);
        p1.GetComponent<Renderer>().sharedMaterial = p1Mat;

        GameObject p2 = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        p2.name = "Fighter_P2_Decepticon (Reference)";
        p2.transform.position = new Vector3(2.8f, 1.0f, 0.0f);
        p2.transform.localScale = new Vector3(0.9f, 1.0f, 0.9f);
        Material p2Mat = new Material(Shader.Find("Standard"));
        p2Mat.color = new Color(0.9f, 0.2f, 0.2f);
        p2.GetComponent<Renderer>().sharedMaterial = p2Mat;

        // 10. Main Battle Camera (Matching TFTF Combat View)
        GameObject camGo = new GameObject("Main Camera (TFTF Combat View)");
        camGo.tag = "MainCamera";
        Camera cam = camGo.AddComponent<Camera>();
        cam.clearFlags = CameraClearFlags.Skybox;
        cam.fieldOfView = 48.0f;
        camGo.transform.position = new Vector3(0.0f, 2.7f, -9.0f);
        camGo.transform.LookAt(new Vector3(0.0f, 2.2f, 2.5f));

        // 11. Save Scene
        string scenePath = "Assets/Scenes/RustSea_Devastator_Stage.unity";
        EditorSceneManager.SaveScene(scene, scenePath);
        Debug.Log($"[✓] Scene saved successfully to: {scenePath}");

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("=== Rust Sea Devastator Stage Build Complete! ===");
    }

    private static Material CreateStandardMaterial(string matPath, string diffuseTexPath, string normalTexPath = null) {
        Material mat = AssetDatabase.LoadAssetAtPath<Material>(matPath);
        if (mat == null) {
            mat = new Material(Shader.Find("Standard"));
            mat.SetFloat("_Glossiness", 0.35f);
            mat.SetFloat("_Metallic", 0.2f);
            AssetDatabase.CreateAsset(mat, matPath);
        }

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
        EditorUtility.SetDirty(mat);
        return mat;
    }
}
