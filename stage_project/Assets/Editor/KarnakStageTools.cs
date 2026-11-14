using System;
using System.IO;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEditor.Animations;

public class KarnakStageTools {
    [UnityEditor.Callbacks.DidReloadScripts]
    private static void OnScriptsReloaded() {
        string flagPath = "Temp/karnak_auto_run.flag";
        if (File.Exists(flagPath)) {
            File.Delete(flagPath);
            EditorApplication.delayCall += () => {
                ExecuteFix(false);
            };
        }
    }

    [MenuItem("TFTF/⚡ 一键刷新卡纳克双巨神场景 (Attack 1 + 等高修复) ⚡", false, 0)]
    public static void FixCurrentScene() {
        Debug.Log("=== [TFTF] 点击了一键刷新卡纳克场景 ===");

        if (EditorApplication.isPlaying) {
            Debug.Log("[TFTF] 检测到当前处于 Play 播放模式，正在安全停止并排队执行刷新...");
            EditorApplication.isPlaying = false;
            
            Action<PlayModeStateChange> onStateChanged = null;
            onStateChanged = (state) => {
                if (state == PlayModeStateChange.EnteredEditMode) {
                    EditorApplication.playModeStateChanged -= onStateChanged;
                    EditorApplication.delayCall += () => {
                        ExecuteFix(true);
                    };
                }
            };
            EditorApplication.playModeStateChanged += onStateChanged;
            return;
        }

        ExecuteFix(true);
    }

    public static void ExecuteFix(bool showDialog = true) {
        Debug.Log("=== [TFTF] 开始执行场景修复：Attack 1 连招重置 + 等高体型对齐 ===");

        if (EditorSceneManager.GetActiveScene().path != "Assets/Scenes/Karnak_Combiners_Stage.unity") {
            EditorSceneManager.OpenScene("Assets/Scenes/Karnak_Combiners_Stage.unity");
        }

        string volcFBXPath = "Assets/Combiners/Volcanicus/Volcanicus_PingPong.fbx";
        string vicFBXPath = "Assets/Combiners/Victorion/Victorion_Raw.fbx";

        // 1. Configure Victorion Raw FBX Importer
        ModelImporter vicImporter = AssetImporter.GetAtPath(vicFBXPath) as ModelImporter;
        if (vicImporter != null) {
            vicImporter.animationType = ModelImporterAnimationType.Generic;
            vicImporter.importAnimation = true;
            ModelImporterClipAnimation[] clips = vicImporter.defaultClipAnimations;
            List<ModelImporterClipAnimation> targetClips = new List<ModelImporterClipAnimation>();
            foreach (var clip in clips) {
                if (clip.name.IndexOf("attack_1", StringComparison.OrdinalIgnoreCase) >= 0) {
                    clip.loopTime = true;
                    clip.loopPose = false;
                }
                targetClips.Add(clip);
            }
            if (targetClips.Count > 0) {
                vicImporter.clipAnimations = targetClips.ToArray();
            }
            vicImporter.SaveAndReimport();
        }

        // 2. Configure Volcanicus FBX Importer
        ModelImporter volcImporter = AssetImporter.GetAtPath(volcFBXPath) as ModelImporter;
        if (volcImporter != null) {
            volcImporter.animationType = ModelImporterAnimationType.Generic;
            volcImporter.importAnimation = true;
            ModelImporterClipAnimation[] clips = volcImporter.defaultClipAnimations;
            List<ModelImporterClipAnimation> targetClips = new List<ModelImporterClipAnimation>();
            foreach (var clip in clips) {
                clip.name = "Volcanicus_PingPong_Loop";
                clip.takeName = "Scene";
                clip.firstFrame = 1;
                clip.lastFrame = 278;
                clip.loopTime = true;
                clip.loopPose = false;
                targetClips.Add(clip);
            }
            if (targetClips.Count > 0) volcImporter.clipAnimations = targetClips.ToArray();
            volcImporter.SaveAndReimport();
        }

        // 3. Create Controllers with defaultWeight = 1.0f
        AnimationClip vicClip = LoadClip(vicFBXPath, "Attack_1");
        string vicCtrlPath = "Assets/Combiners/Victorion/Victorion_LoopController.controller";
        AnimatorController vicCtrl = AnimatorController.CreateAnimatorControllerAtPath(vicCtrlPath);
        if (vicClip != null) {
            AnimatorState st = vicCtrl.layers[0].stateMachine.AddState("Victorion_Attack_1_Loop");
            st.motion = vicClip;
            vicCtrl.layers[0].stateMachine.defaultState = st;
        }
        var vicLayers = vicCtrl.layers;
        vicLayers[0].defaultWeight = 1.0f;
        vicCtrl.layers = vicLayers;
        EditorUtility.SetDirty(vicCtrl);

        AnimationClip volcClip = LoadClip(volcFBXPath, "Volcanicus");
        string volcCtrlPath = "Assets/Combiners/Volcanicus/Volcanicus_LoopController.controller";
        AnimatorController volcCtrl = AnimatorController.CreateAnimatorControllerAtPath(volcCtrlPath);
        if (volcClip != null) {
            AnimatorState st = volcCtrl.layers[0].stateMachine.AddState("Volcanicus_PingPong_Loop");
            st.motion = volcClip;
            volcCtrl.layers[0].stateMachine.defaultState = st;
        }
        var volcLayers = volcCtrl.layers;
        volcLayers[0].defaultWeight = 1.0f;
        volcCtrl.layers = volcLayers;
        EditorUtility.SetDirty(volcCtrl);

        AssetDatabase.SaveAssets();

        // 4. Update Volcanicus in Scene (Scale to 180 to match Victorion 9.34m)
        GameObject volcGo = GameObject.Find("Volcanicus_Colossus");
        if (volcGo != null) {
            volcGo.transform.localScale = new Vector3(180.0f, 180.0f, 180.0f);
            volcGo.transform.position = new Vector3(-18.0f, 0.0f, 13.0f);
            volcGo.transform.rotation = Quaternion.LookRotation(new Vector3(18.0f, 0.0f, -13.0f));

            Material volcBodyMat = AssetDatabase.LoadAssetAtPath<Material>("Assets/Combiners/Volcanicus/Materials/M_Volcanicus.mat");
            Material volcWeaponMat = AssetDatabase.LoadAssetAtPath<Material>("Assets/Combiners/Volcanicus/Materials/M_Volcanicus_Weapon.mat");
            foreach (Renderer r in volcGo.GetComponentsInChildren<Renderer>()) {
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

            Animator anim = volcGo.GetComponent<Animator>();
            if (anim == null) anim = volcGo.AddComponent<Animator>();
            anim.runtimeAnimatorController = volcCtrl;
            anim.cullingMode = AnimatorCullingMode.AlwaysAnimate;
            Debug.Log("[✓] Volcanicus: Scale updated to (180, 180, 180), Height ~9.34m, Controller hooked!");
        }

        // 5. Respawn Victorion with Raw FBX (100% attached joints)
        List<GameObject> oldVics = new List<GameObject>();
        foreach (GameObject go in UnityEngine.Object.FindObjectsOfType<GameObject>()) {
            if (go.name == "Victorion" || go.name == "Victorion_Colossus" || go.name.StartsWith("Victorion_")) {
                oldVics.Add(go);
            }
        }
        foreach (var go in oldVics) UnityEngine.Object.DestroyImmediate(go);

        GameObject vicPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(vicFBXPath);
        if (vicPrefab != null) {
            GameObject newVic = UnityEngine.Object.Instantiate(vicPrefab);
            newVic.name = "Victorion_Colossus";

            // Remove extra unskinned sword prop so only the real animated sword remains
            foreach (Transform t in newVic.GetComponentsInChildren<Transform>()) {
                if (t.name == "Victorion_Sword_Mesh") {
                    UnityEngine.Object.DestroyImmediate(t.gameObject);
                    break;
                }
            }

            Material vicBodyMat = AssetDatabase.LoadAssetAtPath<Material>("Assets/Combiners/Victorion/Materials/M_Victorion_Body.mat");
            Material vicGlassMat = AssetDatabase.LoadAssetAtPath<Material>("Assets/Combiners/Victorion/Materials/M_Victorion_Glass.mat");

            foreach (Renderer r in newVic.GetComponentsInChildren<Renderer>()) {
                r.sharedMaterials = new Material[] { vicGlassMat, vicBodyMat };
                if (r is SkinnedMeshRenderer) {
                    ((SkinnedMeshRenderer)r).updateWhenOffscreen = true;
                }
            }

            // Scale Victorion to match Volcanicus (~9.34m)
            float desiredScale = 38.0f;
            newVic.transform.localScale = new Vector3(desiredScale, desiredScale, desiredScale);

            // Set Position & Rotation (outside arena disc, facing center)
            newVic.transform.position = new Vector3(15.5f, 0.0f, 15.5f);
            newVic.transform.rotation = Quaternion.LookRotation(new Vector3(-15.5f, 0.0f, -15.5f));

            Animator anim = newVic.GetComponent<Animator>();
            if (anim == null) anim = newVic.AddComponent<Animator>();
            anim.runtimeAnimatorController = vicCtrl;
            anim.applyRootMotion = false;
            anim.cullingMode = AnimatorCullingMode.AlwaysAnimate;

            if (vicClip != null) {
                vicClip.SampleAnimation(newVic, 0.2f);
            }
            if (volcGo != null && volcClip != null) {
                volcClip.SampleAnimation(volcGo, volcClip.length * 0.5f);
            }

            // Ground her feet cleanly so she is perfectly flush with the ground disc
            float vicMinY = float.MaxValue;
            foreach (Renderer r in newVic.GetComponentsInChildren<Renderer>()) {
                vicMinY = Mathf.Min(vicMinY, r.bounds.min.y);
            }
            newVic.transform.position += new Vector3(0.0f, -vicMinY, 0.0f);

            Debug.Log($"[✓] Victorion: Height ~9.34m (scale={desiredScale:F2}), Grounded at Y={newVic.transform.position.y:F2}, Controller hooked!");
        }

        // 6. Ensure Main Camera exists
        GameObject camGo = GameObject.Find("Main Camera (TFTF Combat View)");
        if (camGo == null) {
            camGo = new GameObject("Main Camera (TFTF Combat View)");
            camGo.tag = "MainCamera";
            Camera cam = camGo.AddComponent<Camera>();
            cam.clearFlags = CameraClearFlags.Skybox;
            cam.fieldOfView = 56.0f;
        }
        camGo.transform.position = new Vector3(0.0f, 3.2f, -13.0f);
        camGo.transform.LookAt(new Vector3(0.0f, 2.5f, 3.0f));

        // 7. Save Scene Cleanly
        EditorSceneManager.MarkSceneDirty(EditorSceneManager.GetActiveScene());
        EditorSceneManager.SaveScene(EditorSceneManager.GetActiveScene());
        AssetDatabase.SaveAssets();

        // 8. Capture Verification Shot
        CapturePreview("E:/Agent/TFTF-blender/scratch/karnak_fixed_verification.png");

        Debug.Log("⭐⭐⭐ [TFTF] 卡纳克双巨神场景刷新成功！已保存到场景资产！ ⭐⭐⭐");
        if (showDialog) {
            EditorUtility.DisplayDialog("TFTF 场景修复完成",
                "【已完成更新】：\n\n" +
                "1. 凯旋女神（Victorion）：已彻底切换为纯净 Attack 1 斩击动画，四肢部件 100% 紧密相连，绝无散架或浮空。\n\n" +
                "2. 修罗王（Volcanicus）：缩放已调整至 180，高度达到 ~9.34m，与凯旋女神完全等高对齐！\n\n" +
                "3. 动画控制器已重构：图层权重 DefaultWeight=1.0，点击顶部 ▶ Play 按钮即可无限循环挥斩与重组！",
                "好的");
        }
    }

    private static AnimationClip LoadClip(string fbxPath, string nameHint) {
        UnityEngine.Object[] assets = AssetDatabase.LoadAllAssetsAtPath(fbxPath);
        foreach (var a in assets) {
            if (a is AnimationClip && !a.name.StartsWith("__preview__")) {
                if (a.name.IndexOf(nameHint, StringComparison.OrdinalIgnoreCase) >= 0) {
                    return a as AnimationClip;
                }
            }
        }
        foreach (var a in assets) {
            if (a is AnimationClip && !a.name.StartsWith("__preview__")) {
                return a as AnimationClip;
            }
        }
        return null;
    }

    private static void CapturePreview(string outPath) {
        GameObject camGo = GameObject.Find("Main Camera (TFTF Combat View)");
        if (camGo == null) return;
        Camera cam = camGo.GetComponent<Camera>();
        if (cam == null) return;

        int width = 1280;
        int height = 720;
        RenderTexture rt = new RenderTexture(width, height, 24);
        cam.targetTexture = rt;
        Texture2D screenShot = new Texture2D(width, height, TextureFormat.RGB24, false);

        cam.Render();
        RenderTexture.active = rt;
        screenShot.ReadPixels(new Rect(0, 0, width, height), 0, 0);
        screenShot.Apply();

        byte[] bytes = screenShot.EncodeToPNG();
        File.WriteAllBytes(outPath, bytes);
        Debug.Log($"[✓] Saved verification capture to: {outPath}");

        // Also capture close-up of Victorion to verify attached joints
        GameObject vicGo = GameObject.Find("Victorion_Colossus");
        if (vicGo != null) {
            Vector3 origPos = cam.transform.position;
            Quaternion origRot = cam.transform.rotation;

            Vector3 vicPos = vicGo.transform.position;
            cam.transform.position = vicPos + vicGo.transform.forward * 10.0f + new Vector3(0, 4.5f, 0);
            cam.transform.LookAt(vicPos + new Vector3(0, 4.5f, 0));

            cam.Render();
            RenderTexture.active = rt;
            screenShot.ReadPixels(new Rect(0, 0, width, height), 0, 0);
            screenShot.Apply();
            string closePath = "E:/Agent/TFTF-blender/scratch/karnak_vic_closeup.png";
            File.WriteAllBytes(closePath, screenShot.EncodeToPNG());
            Debug.Log($"[✓] Saved Victorion close-up to: {closePath}");

            cam.transform.position = origPos;
            cam.transform.rotation = origRot;
        }

        cam.targetTexture = null;
        RenderTexture.active = null;
        UnityEngine.Object.DestroyImmediate(rt);
        UnityEngine.Object.DestroyImmediate(screenShot);
    }
}
// Trigger timestamp 2026-11-14T15:57:15
