using UnityEngine;
using UnityEngine.Playables;
using UnityEngine.Animations;
using System.IO;
using System.Collections.Generic;

public class VortexPreviewController : MonoBehaviour {
    public Animator animGrindor;
    public Animator animVortex;

    private Animator animTransGrindor;
    private Animator animTransVortex;

    private SkinnedMeshRenderer smrRobotGrindor;
    private SkinnedMeshRenderer smrVehGrindor;
    private SkinnedMeshRenderer smrRobotVortex;
    private SkinnedMeshRenderer smrVehVortex;

    private Transform hipsGrindor;
    private Transform hipsVortex;

    private AssetBundle bundleGrindor;
    private Dictionary<string, AnimationClip> loadedClips = new Dictionary<string, AnimationClip>();

    private PlayableGraph graphGrindor;
    private PlayableGraph graphVortex;
    private PlayableGraph graphTransGrindor;
    private PlayableGraph graphTransVortex;

    private AnimationClipPlayable playableGrindor;
    private AnimationClipPlayable playableVortex;
    private AnimationClipPlayable playableTransGrindor;
    private AnimationClipPlayable playableTransVortex;

    private List<string> displayAnimNames = new List<string>();
    private string currentAnim = "";
    private bool loop = true;
    private bool rootMotion = false;
    private string statusMessage = "";

    private const string SP3_ANIM_NAME = "Grindor_Normal_attackSpecial_03";
    private const string SP3_TRANS_CLIP = "Grindor_Normal_attackSpecial_03_transformed";
    private const string HEAVY_ANIM_NAME = "Grindor_Normal_attackHeavy";
    private const string HEAVY_TRANS_CLIP = "Grindor_Normal_attackHeavy_transformed";
    private const string VEHICLE_SHOWCASE_KEY = "__VEHICLE_SHOWCASE__";
    private const string VEHICLE_IDLE_CLIP = "frontend_Grindor_levelup_vehicle_idle_transformed";

    private bool isPlayingSP3 = false;
    private bool isPlayingHeavy = false;
    private bool isVehicleShowcase = false;

    private float camYaw = 180.0f;
    private float camPitch = 5.0f;
    private float camDist = 18.0f;
    private Vector3 camPivot = new Vector3(0.0f, 5.0f, 0.0f);

    private Rect previewWindowRect = new Rect(16, 16, 340, 620);
    private Vector2 scrollPos = Vector2.zero;

    private Dictionary<Transform, Vector3> initBonePos = new Dictionary<Transform, Vector3>();
    private Dictionary<Transform, Quaternion> initBoneRot = new Dictionary<Transform, Quaternion>();

    void Start() {
        CleanScene();
        Camera cam = Camera.main;
        if (cam != null) cam.targetTexture = null;
        InitAnimators();
        InitRenderers();
        LoadBundlesAndClips();
        ApplyCameraOrbit();
        if (displayAnimNames.Count > 0) {
            PlayAnimation(displayAnimNames[0]);
        }
    }

    void CleanScene() {
        var ground = GameObject.Find("Ground");
        if (ground != null) ground.SetActive(false);
    }

    void InitAnimators() {
        if (animGrindor == null) {
            var go = GameObject.Find("Grindor_Official_Reference");
            if (go != null) animGrindor = go.GetComponent<Animator>();
        }
        if (animVortex == null) {
            var go = GameObject.Find("Vortex_Candidate");
            if (go != null) animVortex = go.GetComponent<Animator>();
        }

        if (animGrindor != null) {
            hipsGrindor = FindChildRecursive(animGrindor.transform, "Hips");
            Transform tTr = FindChildRecursive(animGrindor.transform, "transformed");
            if (tTr != null) {
                animTransGrindor = tTr.GetComponent<Animator>();
                if (animTransGrindor == null) animTransGrindor = tTr.gameObject.AddComponent<Animator>();
            }
        }
        if (animVortex != null) {
            hipsVortex = FindChildRecursive(animVortex.transform, "Hips");
            Transform tTr = FindChildRecursive(animVortex.transform, "transformed");
            if (tTr != null) {
                animTransVortex = tTr.GetComponent<Animator>();
                if (animTransVortex == null) animTransVortex = tTr.gameObject.AddComponent<Animator>();
            }
        }

        initBonePos.Clear();
        initBoneRot.Clear();
        if (animGrindor != null) {
            foreach (var t in animGrindor.GetComponentsInChildren<Transform>(true)) {
                initBonePos[t] = t.localPosition;
                initBoneRot[t] = t.localRotation;
            }
        }
        if (animVortex != null) {
            foreach (var t in animVortex.GetComponentsInChildren<Transform>(true)) {
                initBonePos[t] = t.localPosition;
                initBoneRot[t] = t.localRotation;
            }
        }
    }

    void RestoreInitialBones() {
        foreach (var kv in initBonePos) {
            if (kv.Key != null) {
                kv.Key.localPosition = kv.Value;
                kv.Key.localRotation = initBoneRot[kv.Key];
            }
        }
    }

    void InitRenderers() {
        if (animGrindor != null) {
            foreach (var smr in animGrindor.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
                string nm = smr.name.ToLower();
                if (nm.Contains("_01") || nm.Contains("vehicle")) smrVehGrindor = smr;
                else if (nm.Contains("_00") && !nm.Contains("wpns")) smrRobotGrindor = smr;
            }
        }
        if (animVortex != null) {
            foreach (var smr in animVortex.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
                string nm = smr.name.ToLower();
                if (nm.Contains("_01") || nm.Contains("vehicle")) smrVehVortex = smr;
                else if (nm.Contains("_00") && !nm.Contains("wpns")) smrRobotVortex = smr;
            }
        }
    }

    void LoadBundlesAndClips() {
        string bundlePath = @"E:\Agent\TFTF-blender\toolchain\grindor_anims_registered.assetbundle";
        if (!File.Exists(bundlePath)) {
            bundlePath = @"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle";
        }
        if (File.Exists(bundlePath)) {
            bundleGrindor = AssetBundle.LoadFromFile(bundlePath);
            if (bundleGrindor != null) {
                foreach (var clip in bundleGrindor.LoadAllAssets<AnimationClip>()) {
                    loadedClips[clip.name] = clip;
                }
            }
        }

        Avatar officialAvatar00 = null;
        Avatar officialAvatar01 = null;

        if (bundleGrindor != null) {
            foreach (var av in bundleGrindor.LoadAllAssets<Avatar>()) {
                if (av.name.Contains("_00") && !av.name.Contains("wpns")) {
                    officialAvatar00 = av;
                } else if (av.name.Contains("_01")) {
                    officialAvatar01 = av;
                }
            }
            if (officialAvatar00 == null) {
                officialAvatar00 = bundleGrindor.LoadAsset<Avatar>("cha_grindor_cin_rotf_00Avatar");
            }
            if (officialAvatar01 == null) {
                officialAvatar01 = bundleGrindor.LoadAsset<Avatar>("cha_grindor_cin_rotf_01Avatar");
            }
            if (officialAvatar00 == null) {
                GameObject prefab = bundleGrindor.LoadAsset<GameObject>("Grindor_Cin_ROTF");
                if (prefab != null) {
                    Animator pAnim = prefab.GetComponent<Animator>();
                    if (pAnim != null) officialAvatar00 = pAnim.avatar;
                }
            }
        }

        if (officialAvatar00 != null) {
            if (animGrindor != null) {
                animGrindor.avatar = officialAvatar00;
                animGrindor.cullingMode = AnimatorCullingMode.AlwaysAnimate;
                animGrindor.applyRootMotion = false;
            }
            if (animVortex != null) {
                animVortex.avatar = officialAvatar00;
                animVortex.cullingMode = AnimatorCullingMode.AlwaysAnimate;
                animVortex.applyRootMotion = false;
            }
        }

        if (officialAvatar01 != null) {
            if (animTransGrindor != null) {
                animTransGrindor.avatar = officialAvatar01;
                animTransGrindor.cullingMode = AnimatorCullingMode.AlwaysAnimate;
                animTransGrindor.applyRootMotion = false;
            }
            if (animTransVortex != null) {
                animTransVortex.avatar = officialAvatar01;
                animTransVortex.cullingMode = AnimatorCullingMode.AlwaysAnimate;
                animTransVortex.applyRootMotion = false;
            }
        }

        // Ordered list of key actions for verification
        string[] priorityClips = new string[] {
            "Brute_Normal_CombatIdle",
            "Prefight_Brute_idle",
            "brute_normal_attackLight_01_rightHandPunch",
            "brute_normal_attackLight_02_leftHandPunch",
            "brute_normal_attackLight_03_sideKick",
            "brute_normal_attackLight_04_upperCut",
            "Grindor_Normal_attackHeavy",
            "Grindor_Normal_attackSpecial_02",
            "Grindor_Normal_attackSpecial_03",
            VEHICLE_SHOWCASE_KEY
        };

        foreach (var cname in priorityClips) {
            if (cname == VEHICLE_SHOWCASE_KEY || loadedClips.ContainsKey(cname)) {
                displayAnimNames.Add(cname);
            }
        }

        statusMessage = $"Loaded {loadedClips.Count} clips | Avatar={(officialAvatar00 != null ? officialAvatar00.name : "NULL")}";
        Debug.Log($"[VortexPreview] Loaded {loadedClips.Count} Grindor clips. Registered {displayAnimNames.Count} actions. Avatar00={officialAvatar00}");
    }

    public void PlayAnimation(string animName) {
        currentAnim = animName;
        isPlayingSP3 = (animName == SP3_ANIM_NAME);
        isPlayingHeavy = (animName == HEAVY_ANIM_NAME);
        isVehicleShowcase = (animName == VEHICLE_SHOWCASE_KEY);

        DestroyGraphs();
        RestoreInitialBones();

        if (isVehicleShowcase) {
            SetMode(false); // Vehicle mode
            camPivot = new Vector3(0.0f, 3.2f, 0.0f);
            ApplyCameraOrbit();

            if (loadedClips.TryGetValue(VEHICLE_IDLE_CLIP, out AnimationClip vClip)) {
                PlayClipOnTransformed(vClip);
            }
            statusMessage = "Mode: Vehicle Mode (载具直升机并排展示)";
            return;
        }

        camPivot = new Vector3(0.0f, 5.0f, 0.0f);
        SetMode(true); // Robot mode

        if (!loadedClips.TryGetValue(animName, out AnimationClip clip)) {
            statusMessage = "Clip not found: " + animName;
            return;
        }

        if (animGrindor != null) {
            animGrindor.applyRootMotion = rootMotion;
            graphGrindor = PlayableGraph.Create("GrindorGraph");
            playableGrindor = AnimationClipPlayable.Create(graphGrindor, clip);
            playableGrindor.SetApplyFootIK(false);
            var outputG = AnimationPlayableOutput.Create(graphGrindor, "Animation", animGrindor);
            outputG.SetSourcePlayable(playableGrindor);
            graphGrindor.Play();
        }

        if (animVortex != null) {
            animVortex.applyRootMotion = rootMotion;
            graphVortex = PlayableGraph.Create("VortexGraph");
            playableVortex = AnimationClipPlayable.Create(graphVortex, clip);
            playableVortex.SetApplyFootIK(false);
            var outputV = AnimationPlayableOutput.Create(graphVortex, "Animation", animVortex);
            outputV.SetSourcePlayable(playableVortex);
            graphVortex.Play();
        }

        if (isPlayingSP3 && loadedClips.TryGetValue(SP3_TRANS_CLIP, out AnimationClip sp3Trans)) {
            PlayClipOnTransformed(sp3Trans);
        } else if (isPlayingHeavy && loadedClips.TryGetValue(HEAVY_TRANS_CLIP, out AnimationClip heavyTrans)) {
            PlayClipOnTransformed(heavyTrans);
        }

        statusMessage = $"Playing: {GetFriendlyLabel(animName)} ({clip.length:F2}s)";
    }

    void PlayClipOnTransformed(AnimationClip transClip) {
        if (animTransGrindor != null) {
            animTransGrindor.applyRootMotion = rootMotion;
            graphTransGrindor = PlayableGraph.Create("TransGrindorGraph");
            playableTransGrindor = AnimationClipPlayable.Create(graphTransGrindor, transClip);
            playableTransGrindor.SetApplyFootIK(false);
            var outTG = AnimationPlayableOutput.Create(graphTransGrindor, "TransAnimation", animTransGrindor);
            outTG.SetSourcePlayable(playableTransGrindor);
            graphTransGrindor.Play();
        }
        if (animTransVortex != null) {
            animTransVortex.applyRootMotion = rootMotion;
            graphTransVortex = PlayableGraph.Create("TransVortexGraph");
            playableTransVortex = AnimationClipPlayable.Create(graphTransVortex, transClip);
            playableTransVortex.SetApplyFootIK(false);
            var outTV = AnimationPlayableOutput.Create(graphTransVortex, "TransAnimation", animTransVortex);
            outTV.SetSourcePlayable(playableTransVortex);
            graphTransVortex.Play();
        }
    }

    void SetMode(bool isRobot) {
        if (smrRobotGrindor != null) smrRobotGrindor.enabled = isRobot;
        if (smrRobotVortex != null) smrRobotVortex.enabled = isRobot;
        if (smrVehGrindor != null) {
            smrVehGrindor.gameObject.SetActive(true);
            smrVehGrindor.enabled = !isRobot;
        }
        if (smrVehVortex != null) {
            smrVehVortex.gameObject.SetActive(true);
            smrVehVortex.enabled = !isRobot;
        }

        // Handle Grindor weapon attachments
        if (animGrindor != null) {
            foreach (var r in animGrindor.GetComponentsInChildren<Renderer>(true)) {
                if (r != smrRobotGrindor && r != smrVehGrindor) {
                    if (r.name.Contains("_00") || r.name.Contains("wpns")) {
                        r.enabled = isRobot;
                    }
                }
            }
        }

        if (animTransGrindor != null) animTransGrindor.gameObject.SetActive(!isRobot || isPlayingSP3 || isPlayingHeavy);
        if (animTransVortex != null) animTransVortex.gameObject.SetActive(!isRobot || isPlayingSP3 || isPlayingHeavy);
    }

    void Update() {
        // Orbit & zoom controls (outside GUI area)
        if (Input.GetMouseButton(1) || Input.GetMouseButton(2)) {
            camYaw += Input.GetAxis("Mouse X") * 3.5f;
            camPitch = Mathf.Clamp(camPitch - Input.GetAxis("Mouse Y") * 2.5f, -25.0f, 65.0f);
            ApplyCameraOrbit();
        }
        float scroll = Input.GetAxis("Mouse ScrollWheel");
        if (Mathf.Abs(scroll) > 0.001f && !previewWindowRect.Contains(new Vector2(Input.mousePosition.x, Screen.height - Input.mousePosition.y))) {
            camDist = Mathf.Clamp(camDist - scroll * 6.0f, 6.0f, 32.0f);
            ApplyCameraOrbit();
        }

        if (isVehicleShowcase) {
            if (loadedClips.TryGetValue(VEHICLE_IDLE_CLIP, out AnimationClip vClip) && graphTransGrindor.IsValid() && playableTransGrindor.IsValid()) {
                double vt = playableTransGrindor.GetTime();
                if (loop && vt >= vClip.length) {
                    playableTransGrindor.SetTime(0.0);
                    if (graphTransVortex.IsValid() && playableTransVortex.IsValid()) playableTransVortex.SetTime(0.0);
                }
            }
            return;
        }

        if (!loadedClips.TryGetValue(currentAnim, out AnimationClip clip)) return;

        double t = 0.0;
        if (graphGrindor.IsValid() && playableGrindor.IsValid()) t = playableGrindor.GetTime();

        // SP3 and Heavy vehicle transform window
        if (isPlayingSP3) {
            bool inVehicle = (t >= 1.15 && t <= 3.65);
            SetMode(!inVehicle);
        } else if (isPlayingHeavy) {
            bool inVehicle = (t >= 0.22 && t <= 0.72);
            SetMode(!inVehicle);
        }

        if (loop && t >= clip.length) {
            if (graphGrindor.IsValid() && playableGrindor.IsValid()) playableGrindor.SetTime(0.0);
            if (graphVortex.IsValid() && playableVortex.IsValid()) playableVortex.SetTime(0.0);
            if (graphTransGrindor.IsValid() && playableTransGrindor.IsValid()) playableTransGrindor.SetTime(0.0);
            if (graphTransVortex.IsValid() && playableTransVortex.IsValid()) playableTransVortex.SetTime(0.0);
        }
    }

    void LateUpdate() {
        if (rootMotion) return;
        float spacing = 3.3f;
        if (isVehicleShowcase && smrVehGrindor != null && smrVehVortex != null && animGrindor != null && animVortex != null) {
            animGrindor.transform.rotation = Quaternion.identity;
            animVortex.transform.rotation = Quaternion.identity;
            Bounds bG = smrVehGrindor.bounds;
            Bounds bV = smrVehVortex.bounds;
            animGrindor.transform.position += new Vector3(spacing - bG.center.x, 2.8f - bG.min.y, 0.0f - bG.center.z);
            animVortex.transform.position += new Vector3(-spacing - bV.center.x, 2.8f - bV.min.y, 0.0f - bV.center.z);
            return;
        }

        if (animGrindor != null && animVortex != null && hipsGrindor != null && hipsVortex != null) {
            animGrindor.transform.rotation = Quaternion.identity;
            animVortex.transform.rotation = Quaternion.identity;
            Vector3 dG = hipsGrindor.position - animGrindor.transform.position;
            animGrindor.transform.position = new Vector3(spacing - dG.x, 0.0f, 0.0f - dG.z);
            Vector3 dV = hipsVortex.position - animVortex.transform.position;
            animVortex.transform.position = new Vector3(-spacing - dV.x, 0.0f, 0.0f - dV.z);
        }
    }

    void DestroyGraphs() {
        if (graphGrindor.IsValid()) graphGrindor.Destroy();
        if (graphVortex.IsValid()) graphVortex.Destroy();
        if (graphTransGrindor.IsValid()) graphTransGrindor.Destroy();
        if (graphTransVortex.IsValid()) graphTransVortex.Destroy();
    }

    void OnDestroy() {
        DestroyGraphs();
        if (bundleGrindor != null) bundleGrindor.Unload(true);
    }

    void ApplyCameraOrbit() {
        Camera cam = Camera.main;
        if (cam == null) return;
        Quaternion rot = Quaternion.Euler(camPitch, camYaw, 0f);
        Vector3 offset = rot * new Vector3(0f, 0f, -camDist);
        cam.transform.position = camPivot + offset;
        cam.transform.LookAt(camPivot);
    }

    Transform FindChildRecursive(Transform parent, string childName) {
        foreach (Transform c in parent) {
            if (c.name.Equals(childName, System.StringComparison.OrdinalIgnoreCase)) return c;
            Transform found = FindChildRecursive(c, childName);
            if (found != null) return found;
        }
        return null;
    }

    void OnGUI() {
        Camera cam = Camera.main;
        if (cam != null) {
            GUIStyle tagStyle = new GUIStyle(GUI.skin.box);
            tagStyle.fontSize = 14;
            tagStyle.fontStyle = FontStyle.Bold;
            tagStyle.alignment = TextAnchor.MiddleCenter;
            tagStyle.normal.textColor = Color.white;

            bool vehOn = (smrVehVortex != null && smrVehVortex.enabled);
            float labelHeight = vehOn ? 3.5f : 10.5f;

            if (animGrindor != null) {
                Vector3 sp = cam.WorldToScreenPoint(animGrindor.transform.position + Vector3.up * labelHeight);
                if (sp.z > 0) {
                    GUI.backgroundColor = new Color(0.15f, 0.60f, 0.95f, 0.92f);
                    string mode = vehOn ? " [西科斯基CH-53载具]" : " [官方人形母体]";
                    GUI.Box(new Rect(sp.x - 155, Screen.height - sp.y - 28, 310, 28), "电影眩晕 (Grindor 官方原版)" + mode, tagStyle);
                }
            }

            if (animVortex != null) {
                Vector3 sp = cam.WorldToScreenPoint(animVortex.transform.position + Vector3.up * labelHeight);
                if (sp.z > 0) {
                    GUI.backgroundColor = new Color(0.62f, 0.25f, 0.92f, 0.92f);
                    string mode = vehOn ? " [塞伯坦攻击直升机]" : " [战车队新模具]";
                    GUI.Box(new Rect(sp.x - 155, Screen.height - sp.y - 28, 310, 28), "旋风 (Vortex 战车队突击兵)" + mode, tagStyle);
                }
            }
            GUI.backgroundColor = Color.white;
        }

        previewWindowRect = GUI.Window(9933, previewWindowRect, DrawPreviewWindow, "旋风 vs 电影眩晕 同步动作验收台 (可拖拽/右键旋转/滚轮缩放)");
    }

    void DrawPreviewWindow(int id) {
        double currentT = (graphGrindor.IsValid() && playableGrindor.IsValid()) ? playableGrindor.GetTime() : 0.0;
        GUILayout.Label($"当前动作: {GetFriendlyLabel(currentAnim)} [{currentT:F2}s]");

        GUILayout.BeginHorizontal();
        if (GUILayout.Button("正面全景")) { camYaw = 180f; camPitch = 5f; camDist = 18f; camPivot = new Vector3(0, 5, 0); ApplyCameraOrbit(); }
        if (GUILayout.Button("45°斜侧")) { camYaw = 150f; camPitch = 8f; camDist = 14f; camPivot = new Vector3(0, 5.5f, 0); ApplyCameraOrbit(); }
        if (GUILayout.Button("背面旋翼")) { camYaw = 15f; camPitch = 10f; camDist = 17.5f; camPivot = new Vector3(0f, 5.2f, 0f); ApplyCameraOrbit(); }
        if (GUILayout.Button("手部特写")) { camYaw = 165f; camPitch = 2f; camDist = 7.5f; camPivot = new Vector3(2.8f, 4.8f, 0); ApplyCameraOrbit(); }
        GUILayout.EndHorizontal();

        GUILayout.BeginHorizontal();
        loop = GUILayout.Toggle(loop, " 循环播放 (Loop)");
        bool prevRoot = rootMotion;
        rootMotion = GUILayout.Toggle(rootMotion, " 根骨骼位移 (Root Motion)");
        if (prevRoot != rootMotion) {
            if (animGrindor != null) animGrindor.applyRootMotion = rootMotion;
            if (animVortex != null) animVortex.applyRootMotion = rootMotion;
            if (animTransGrindor != null) animTransGrindor.applyRootMotion = rootMotion;
            if (animTransVortex != null) animTransVortex.applyRootMotion = rootMotion;
        }
        GUILayout.EndHorizontal();

        GUILayout.Space(4);
        scrollPos = GUILayout.BeginScrollView(scrollPos, GUILayout.Height(430));
        foreach (string aname in displayAnimNames) {
            bool isCurrent = (aname == currentAnim);
            GUI.color = isCurrent ? Color.green : Color.white;
            if (GUILayout.Button(GetFriendlyLabel(aname), GUILayout.Height(30))) {
                PlayAnimation(aname);
            }
        }
        GUI.color = Color.white;
        GUILayout.EndScrollView();

        GUILayout.Label(statusMessage, GUI.skin.box);
        GUI.DragWindow(new Rect(0, 0, 10000, 24));
    }

    string GetFriendlyLabel(string aName) {
        switch (aName) {
            case "Brute_Normal_CombatIdle": return "战斗待机姿态 (Combat Idle)";
            case "Prefight_Brute_idle": return "战前登场待机 (Prefight Idle)";
            case "brute_normal_attackLight_01_rightHandPunch": return "轻击 1：右手离子刃刺击 (Light 1 Punch)";
            case "brute_normal_attackLight_02_leftHandPunch": return "轻击 2：左手勾拳 (Light 2 Punch)";
            case "brute_normal_attackLight_03_sideKick": return "轻击 3：侧踹腿 (Light 3 SideKick)";
            case "brute_normal_attackLight_04_upperCut": return "轻击 4：强力上勾拳 (Light 4 UpperCut)";
            case "Grindor_Normal_attackHeavy": return "★ 重击：旋翼重斩变形击 (Heavy Attack)";
            case "Grindor_Normal_attackSpecial_02": return "★ SP2：旋翼狂暴切割 (Special 2 Rotor Slash)";
            case "Grindor_Normal_attackSpecial_03": return "★ SP3：直升机终极轰炸 (Special 3 Ultimate)";
            case VEHICLE_SHOWCASE_KEY: return "★ 载具直升机并排展示 (Vehicle Mode)";
            default: return aName;
        }
    }
}
