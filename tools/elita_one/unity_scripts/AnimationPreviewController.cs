using UnityEngine;
using UnityEngine.Playables;
using UnityEngine.Animations;
using System.IO;
using System.Collections.Generic;

public class AnimationPreviewController : MonoBehaviour {
    public Animator animArcee;
    public Animator animElita;

    private Animator animTransArcee;
    private Animator animTransElita;

    private SkinnedMeshRenderer smrRobotArcee;
    private SkinnedMeshRenderer smrVehArcee;
    private SkinnedMeshRenderer smrRobotElita;
    private SkinnedMeshRenderer smrVehElita;

    private AssetBundle bundleProcedural;
    private AssetBundle bundleArcee;
    private Dictionary<string, AnimationClip> loadedClips = new Dictionary<string, AnimationClip>();

    private PlayableGraph graphArcee;
    private PlayableGraph graphElita;
    private PlayableGraph graphTransArcee;
    private PlayableGraph graphTransElita;

    private AnimationClipPlayable playableArcee;
    private AnimationClipPlayable playableElita;
    private AnimationClipPlayable playableTransArcee;
    private AnimationClipPlayable playableTransElita;

    private List<string> displayAnimNames = new List<string>();
    private string currentAnim = "";
    private bool loop = true;
    private bool rootMotion = false;
    private string statusMessage = "";

    // SP3 Special Timing
    private const string SP3_ANIM_NAME = "Arcee_Normal_attackSpecial_03";
    private const string SP3_TRANS_CLIP = "Arcee_Normal_attackSpecial_03_transformed";
    private const float SP3_VEHICLE_START = 2.000f;
    private const float SP3_VEHICLE_END = 3.230f;
    private bool isPlayingSP3 = false;

    void Start() {
        CleanScene();
        InitAnimators();
        InitRenderers();
        LoadBundlesAndClips();
        RestoreArceeMeshes();
        ReloadElitaGraftedMeshes();
        if (displayAnimNames.Count > 0) {
            PlayAnimation(displayAnimNames[0]);
        }
    }

    void CleanScene() {
        var ground = GameObject.Find("Ground");
        if (ground != null) {
            ground.SetActive(false);
            Debug.Log("[✓] Hidden ground plane so full legs and feet are visible.");
        }
    }

    void InitAnimators() {
        if (animArcee == null) {
            var go = GameObject.Find("Arcee_Official_Reference");
            if (go != null) animArcee = go.GetComponent<Animator>();
        }
        if (animElita == null) {
            var go = GameObject.Find("ElitaOne_Candidate");
            if (go != null) animElita = go.GetComponent<Animator>();
        }

        if (animArcee != null) {
            var tr = animArcee.transform.Find("character_model/Reference/Hips/transformed");
            if (tr != null) {
                animTransArcee = tr.GetComponent<Animator>();
                if (animTransArcee == null) animTransArcee = tr.gameObject.AddComponent<Animator>();
            }
        }

        if (animElita != null) {
            var tr = animElita.transform.Find("character_model/Reference/Hips/transformed");
            if (tr != null) {
                animTransElita = tr.GetComponent<Animator>();
                if (animTransElita == null) animTransElita = tr.gameObject.AddComponent<Animator>();
            }
        }
    }

    void InitRenderers() {
        if (animArcee != null) {
            foreach (var smr in animArcee.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
                if (smr.name.Contains("_00")) smrRobotArcee = smr;
                else if (smr.name.Contains("_01")) smrVehArcee = smr;
            }
        }

        if (animElita != null) {
            foreach (var smr in animElita.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
                if (smr.name.Contains("_00") || smr.name.Contains("cha_elita_one_gs_00") || (smr.name.Contains("elita") && !smr.name.Contains("01") && !smr.name.Contains("vehicle"))) {
                    smrRobotElita = smr;
                } else if (smr.name.Contains("_01") || smr.name.Contains("vehicle")) {
                    smrVehElita = smr;
                }
            }
        }
    }

    void SetVehicleMode(bool vehicleActive) {
        if (smrRobotArcee != null) smrRobotArcee.enabled = !vehicleActive;
        if (smrVehArcee != null) {
            smrVehArcee.gameObject.SetActive(true);
            smrVehArcee.enabled = vehicleActive;
        }

        if (smrRobotElita != null) smrRobotElita.enabled = !vehicleActive;
        if (smrVehElita != null) {
            smrVehElita.gameObject.SetActive(true);
            smrVehElita.enabled = vehicleActive;
        }
    }

    void ReloadElitaGraftedMeshes() {
        if (animElita == null) return;

#if UNITY_EDITOR
        Mesh robotMesh = UnityEditor.AssetDatabase.LoadAssetAtPath<Mesh>("Assets/ElitaOne/cha_elita_one_grafted.asset");
        Mesh vehMesh = UnityEditor.AssetDatabase.LoadAssetAtPath<Mesh>("Assets/ElitaOne/cha_elita_one_vehicle_grafted.asset");
        Material matMain = UnityEditor.AssetDatabase.LoadAssetAtPath<Material>("Assets/ElitaOne/M_Elita_Main.mat");
        Material matVh = UnityEditor.AssetDatabase.LoadAssetAtPath<Material>("Assets/ElitaOne/M_Elita_Vh.mat");
        Material matV00 = UnityEditor.AssetDatabase.LoadAssetAtPath<Material>("Assets/ElitaOne/Vehicle/M_Elita_Vehicle_00.mat");
        Material matV01 = UnityEditor.AssetDatabase.LoadAssetAtPath<Material>("Assets/ElitaOne/Vehicle/M_Elita_Vehicle_01.mat");
        Material matVGlass = UnityEditor.AssetDatabase.LoadAssetAtPath<Material>("Assets/ElitaOne/Vehicle/M_Elita_Vehicle_Glass.mat");

        if (smrRobotElita != null && robotMesh != null) {
            smrRobotElita.sharedMesh = robotMesh;
            if (matMain != null && matVh != null) smrRobotElita.sharedMaterials = new Material[] { matMain, matVh };
            Debug.Log("[✓] Reloaded cha_elita_one_grafted.asset onto Elita robot!");
        }

        if (smrVehElita != null && vehMesh != null) {
            smrVehElita.sharedMesh = vehMesh;
            if (matV00 != null && matV01 != null && matVGlass != null) {
                smrVehElita.sharedMaterials = new Material[] { matV00, matV01, matVGlass };
            }
            Debug.Log("[✓] Reloaded cha_elita_one_vehicle_grafted.asset onto Elita vehicle!");
        }
#endif
    }

    void RestoreArceeMeshes() {
        if (animArcee == null || bundleArcee == null) return;

        Mesh mesh01 = null;
        foreach (var m in bundleArcee.LoadAllAssets<Mesh>()) {
            if (m != null && m.name == "cha_arcee_gs_deluxe2014_01") {
                mesh01 = m;
                break;
            }
        }

        Material matMain = null;
        Material matMisc = null;
        Material matWpns = null;
#if UNITY_EDITOR
        matMain = UnityEditor.AssetDatabase.LoadAssetAtPath<Material>("Assets/ElitaOne/Arcee/M_Arcee_Official.mat");
        matMisc = UnityEditor.AssetDatabase.LoadAssetAtPath<Material>("Assets/ElitaOne/Arcee/M_Arcee_Misc.mat");
        matWpns = UnityEditor.AssetDatabase.LoadAssetAtPath<Material>("Assets/ElitaOne/Arcee/M_Arcee_Wpns.mat");
#endif

        if (smrVehArcee != null) {
            if (mesh01 != null) smrVehArcee.sharedMesh = mesh01;
            if (matWpns != null && matMain != null && matMisc != null) {
                smrVehArcee.sharedMaterials = new Material[] { matWpns, matMain, matMisc };
            }
        }
        if (smrRobotArcee != null && matMain != null && matMisc != null) {
            smrRobotArcee.sharedMaterials = new Material[] { matMain, matMisc };
        }
    }

    void LoadBundlesAndClips() {
        foreach (var b in AssetBundle.GetAllLoadedAssetBundles()) {
            if (b.name.Contains("character_anim_procedural")) bundleProcedural = b;
            else if (b.name.Contains("arcee_gs_deluxe2014")) bundleArcee = b;
        }

        string arceePath = @"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle";
        if (!File.Exists(arceePath)) {
            arceePath = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle"));
        }

        if (bundleArcee == null && File.Exists(arceePath)) {
            bundleArcee = AssetBundle.LoadFromFile(arceePath);
        }

        Avatar officialAvatar = null;
        Avatar carAvatar = null;
        if (bundleArcee != null) {
            foreach (var av in bundleArcee.LoadAllAssets<Avatar>()) {
                if (av != null) {
                    if (av.name.Contains("00Avatar") || (av.isHuman && !av.name.Contains("wpn"))) officialAvatar = av;
                    else if (av.name.Contains("01Avatar") || av.name.Contains("car")) carAvatar = av;
                }
            }

            GameObject prefab = bundleArcee.LoadAsset<GameObject>("Arcee_GS_Deluxe2014");
            if (prefab != null) {
                var pAnim = prefab.GetComponent<Animator>();
                if (pAnim != null) {
                    if (officialAvatar == null) officialAvatar = pAnim.avatar;
                    if (pAnim.runtimeAnimatorController != null) {
                        foreach (var c in pAnim.runtimeAnimatorController.animationClips) {
                            if (c != null && !loadedClips.ContainsKey(c.name)) loadedClips[c.name] = c;
                        }
                    }
                }

                Transform tr = prefab.transform.Find("character_model/Reference/Hips/transformed");
                if (tr != null) {
                    var cAnim = tr.GetComponent<Animator>();
                    if (cAnim != null) {
                        if (carAvatar == null) carAvatar = cAnim.avatar;
                        if (cAnim.runtimeAnimatorController != null) {
                            foreach (var c in cAnim.runtimeAnimatorController.animationClips) {
                                if (c != null && !loadedClips.ContainsKey(c.name)) loadedClips[c.name] = c;
                            }
                        }
                    }
                }
            }
        }

        if (officialAvatar != null) {
            if (animArcee != null) { animArcee.avatar = officialAvatar; animArcee.cullingMode = AnimatorCullingMode.AlwaysAnimate; }
            if (animElita != null) { animElita.avatar = officialAvatar; animElita.cullingMode = AnimatorCullingMode.AlwaysAnimate; }
        }

        if (carAvatar != null) {
            if (animTransArcee != null) { animTransArcee.avatar = carAvatar; animTransArcee.cullingMode = AnimatorCullingMode.AlwaysAnimate; }
            if (animTransElita != null) { animTransElita.avatar = carAvatar; animTransElita.cullingMode = AnimatorCullingMode.AlwaysAnimate; }
        }

        string procPath = @"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle";
        if (bundleProcedural == null && File.Exists(procPath)) {
            bundleProcedural = AssetBundle.LoadFromFile(procPath);
        }

        if (bundleProcedural != null) {
            foreach (string assetPath in bundleProcedural.GetAllAssetNames()) {
                Object[] subs = bundleProcedural.LoadAssetWithSubAssets(assetPath);
                if (subs != null) {
                    foreach (var s in subs) {
                        if (s is AnimationClip clip && !loadedClips.ContainsKey(clip.name)) {
                            loadedClips[clip.name] = clip;
                        }
                    }
                }
            }
        }

        string[] preferredOrder = new string[] {
            "TeamSelect_Agile_idle",
            "Prefight_Agile_idle",
            SP3_ANIM_NAME,
            "Arcee_Normal_attackSpecial_01",
            "Arcee_Normal_attackSpecial_02",
            "Arcee_Normal_attackHeavy",
            "agile_normal_attackLight_01_jab_R",
            "agile_normal_attackLight_02_jab_L",
            "agile_normal_attackLight_04_sidekick_R",
            "agile_normal_attackMedium_02_kicks_LR",
            "Agile_Normal_Block",
            "Agile_Backflip_Victory"
        };

        foreach (string name in preferredOrder) {
            if (loadedClips.ContainsKey(name) && !displayAnimNames.Contains(name)) {
                displayAnimNames.Add(name);
            }
        }

        statusMessage = $"Loaded {loadedClips.Count} clips. SP3 Available: {loadedClips.ContainsKey(SP3_ANIM_NAME)}";
        Debug.Log($"[AnimationPreview] Successfully cached {loadedClips.Count} clips, {displayAnimNames.Count} buttons.");
    }

    public void PlayAnimation(string animName) {
        if (!loadedClips.ContainsKey(animName)) {
            statusMessage = "Clip not found: " + animName;
            Debug.LogWarning(statusMessage);
            return;
        }

        currentAnim = animName;
        AnimationClip clip = loadedClips[animName];
        isPlayingSP3 = (animName == SP3_ANIM_NAME);

        // Clean up previous graphs
        if (graphArcee.IsValid()) graphArcee.Destroy();
        if (graphElita.IsValid()) graphElita.Destroy();
        if (graphTransArcee.IsValid()) graphTransArcee.Destroy();
        if (graphTransElita.IsValid()) graphTransElita.Destroy();

        // 1. Root character graphs
        if (animArcee != null) {
            animArcee.applyRootMotion = rootMotion;
            graphArcee = PlayableGraph.Create("ArceeGraph");
            playableArcee = AnimationClipPlayable.Create(graphArcee, clip);
            playableArcee.SetApplyFootIK(false);
            var output = AnimationPlayableOutput.Create(graphArcee, "Animation", animArcee);
            output.SetSourcePlayable(playableArcee);
            graphArcee.Play();
        }

        if (animElita != null) {
            animElita.applyRootMotion = rootMotion;
            graphElita = PlayableGraph.Create("ElitaGraph");
            playableElita = AnimationClipPlayable.Create(graphElita, clip);
            playableElita.SetApplyFootIK(false);
            var output = AnimationPlayableOutput.Create(graphElita, "Animation", animElita);
            output.SetSourcePlayable(playableElita);
            graphElita.Play();
        }

        // 2. Transformed graphs if playing SP3
        if (isPlayingSP3 && loadedClips.TryGetValue(SP3_TRANS_CLIP, out AnimationClip transClip)) {
            if (animTransArcee != null) {
                animTransArcee.applyRootMotion = rootMotion;
                graphTransArcee = PlayableGraph.Create("TransArceeGraph");
                playableTransArcee = AnimationClipPlayable.Create(graphTransArcee, transClip);
                playableTransArcee.SetApplyFootIK(false);
                var outTrans = AnimationPlayableOutput.Create(graphTransArcee, "Animation", animTransArcee);
                outTrans.SetSourcePlayable(playableTransArcee);
                graphTransArcee.Play();
            }

            if (animTransElita != null) {
                animTransElita.applyRootMotion = rootMotion;
                graphTransElita = PlayableGraph.Create("TransElitaGraph");
                playableTransElita = AnimationClipPlayable.Create(graphTransElita, transClip);
                playableTransElita.SetApplyFootIK(false);
                var outTrans = AnimationPlayableOutput.Create(graphTransElita, "Animation", animTransElita);
                outTrans.SetSourcePlayable(playableTransElita);
                graphTransElita.Play();
            }
        }

        // Initial visibility
        SetVehicleMode(false);

        statusMessage = $"Playing: {animName} ({clip.length:F2}s)";
        Debug.Log($"[AnimationPreview] Playing: {animName} (isSP3={isPlayingSP3})");
    }

    void Update() {
        if (!loadedClips.TryGetValue(currentAnim, out AnimationClip clip)) return;

        double t = 0.0;
        if (graphArcee.IsValid() && playableArcee.IsValid()) {
            t = playableArcee.GetTime();
        } else if (graphElita.IsValid() && playableElita.IsValid()) {
            t = playableElita.GetTime();
        }

        if (isPlayingSP3) {
            bool inVehicle = (t >= SP3_VEHICLE_START && t <= SP3_VEHICLE_END);
            SetVehicleMode(inVehicle);
        }

        if (loop && t >= clip.length) {
            if (graphArcee.IsValid() && playableArcee.IsValid()) playableArcee.SetTime(0.0);
            if (graphElita.IsValid() && playableElita.IsValid()) playableElita.SetTime(0.0);
            if (graphTransArcee.IsValid() && playableTransArcee.IsValid()) playableTransArcee.SetTime(0.0);
            if (graphTransElita.IsValid() && playableTransElita.IsValid()) playableTransElita.SetTime(0.0);
        }
    }

    void OnDestroy() {
        if (graphArcee.IsValid()) graphArcee.Destroy();
        if (graphElita.IsValid()) graphElita.Destroy();
        if (graphTransArcee.IsValid()) graphTransArcee.Destroy();
        if (graphTransElita.IsValid()) graphTransElita.Destroy();
        if (bundleProcedural != null) bundleProcedural.Unload(false);
        if (bundleArcee != null) bundleArcee.Unload(false);
    }

    void OnGUI() {
        Camera cam = Camera.main;
        if (cam != null) {
            GUIStyle tagStyle = new GUIStyle(GUI.skin.box);
            tagStyle.fontSize = 13;
            tagStyle.fontStyle = FontStyle.Bold;
            tagStyle.alignment = TextAnchor.MiddleCenter;

            if (animElita != null) {
                Vector3 headWorld = animElita.transform.position + Vector3.up * (isPlayingSP3 && smrVehElita != null && smrVehElita.enabled ? 3.0f : 9.2f);
                Vector3 screenPos = cam.WorldToScreenPoint(headWorld);
                if (screenPos.z > 0) {
                    GUI.backgroundColor = new Color(1.0f, 0.4f, 0.75f, 0.95f);
                    string modeStr = (smrVehElita != null && smrVehElita.enabled) ? " [载具模式 (Cybertronian Car)]" : " [人形模式]";
                    GUI.Box(new Rect(screenPos.x - 160, Screen.height - screenPos.y - 30, 320, 30), "艾丽塔 (Elita One)" + modeStr, tagStyle);
                }
            }

            if (animArcee != null) {
                Vector3 headWorld = animArcee.transform.position + Vector3.up * (isPlayingSP3 && smrVehArcee != null && smrVehArcee.enabled ? 3.0f : 9.2f);
                Vector3 screenPos = cam.WorldToScreenPoint(headWorld);
                if (screenPos.z > 0) {
                    GUI.backgroundColor = new Color(0.2f, 0.7f, 1.0f, 0.95f);
                    string modeStr = (smrVehArcee != null && smrVehArcee.enabled) ? " [载具模式 (Motorcycle)]" : " [人形模式]";
                    GUI.Box(new Rect(screenPos.x - 160, Screen.height - screenPos.y - 30, 320, 30), "阿尔茜 (Arcee 官方原版)" + modeStr, tagStyle);
                }
            }
            GUI.backgroundColor = Color.white;
        }

        previewWindowRect = GUI.Window(9911, previewWindowRect, DrawPreviewWindow, "Animation Preview Controls (可拖拽)");
    }

    private Rect previewWindowRect = new Rect(20, 20, 360, 600);

    void DrawPreviewWindow(int id) {
        double currentT = (graphArcee.IsValid() && playableArcee.IsValid()) ? playableArcee.GetTime() : 0.0;
        string animDisplay = currentAnim == SP3_ANIM_NAME ? "SP3 (变身突进大招)" : currentAnim;
        GUILayout.Label($"Current: {animDisplay} [{currentT:F2}s]", GUILayout.Height(20));

        if (isPlayingSP3) {
            bool inVeh = (currentT >= SP3_VEHICLE_START && currentT <= SP3_VEHICLE_END);
            GUI.color = inVeh ? Color.cyan : Color.yellow;
            GUILayout.Label(inVeh ? ">>> 载具形态冲撞中 (Vehicle Ramming) <<<" : ">>> 人形形态攻击中 (Robot Combat) <<<", GUI.skin.box);
            GUI.color = Color.white;
        }
        
        GUILayout.BeginHorizontal();
        loop = GUILayout.Toggle(loop, " Loop");
        bool prevRoot = rootMotion;
        rootMotion = GUILayout.Toggle(rootMotion, " Root Motion (位移)");
        if (prevRoot != rootMotion) {
            if (animArcee != null) animArcee.applyRootMotion = rootMotion;
            if (animElita != null) animElita.applyRootMotion = rootMotion;
            if (animTransArcee != null) animTransArcee.applyRootMotion = rootMotion;
            if (animTransElita != null) animTransElita.applyRootMotion = rootMotion;
        }
        GUILayout.EndHorizontal();

        GUILayout.Space(5);

        foreach (string aName in displayAnimNames) {
            bool isCurrent = (aName == currentAnim);
            GUI.color = isCurrent ? Color.green : Color.white;
            string btnLabel = aName;
            if (aName == SP3_ANIM_NAME) btnLabel = "★ SP3 变身大招 (Special 3)";
            else if (aName == "Arcee_Normal_attackSpecial_01") btnLabel = "SP1 突进双刀 (Special 1)";
            else if (aName == "Arcee_Normal_attackSpecial_02") btnLabel = "SP2 空翻射击 (Special 2)";
            else if (aName == "Arcee_Normal_attackHeavy") btnLabel = "重击 (Heavy Attack)";

            if (GUILayout.Button(btnLabel, GUILayout.Height(28))) {
                PlayAnimation(aName);
            }
        }
        GUI.color = Color.white;

        GUILayout.Space(8);
        GUILayout.Label(statusMessage, GUI.skin.box);

        GUI.DragWindow(new Rect(0, 0, 10000, 25));
    }
}
