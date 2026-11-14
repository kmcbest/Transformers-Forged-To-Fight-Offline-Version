using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;

public class TarnPreviewController : MonoBehaviour {
    public Animator animOfficialUM;
    public Animator animTarn;

    private Animator animTransUM;
    private Animator animTransTarn;

    private SkinnedMeshRenderer smrRobotUM;
    private SkinnedMeshRenderer smrVehUM;
    private SkinnedMeshRenderer smrRobotTarn;
    private SkinnedMeshRenderer smrVehTarn;

    private AssetBundle bundleUmAnims;
    private AssetBundle bundleProcedural;
    private readonly Dictionary<string, AnimationClip> loadedClips = new Dictionary<string, AnimationClip>();

    private PlayableGraph graphUM;
    private PlayableGraph graphTarn;
    private PlayableGraph graphTransUM;
    private PlayableGraph graphTransTarn;

    private AnimationClipPlayable playableUM;
    private AnimationClipPlayable playableTarn;
    private AnimationClipPlayable playableTransUM;
    private AnimationClipPlayable playableTransTarn;

    private readonly List<string> displayAnimNames = new List<string>();
    private string currentAnim = "";
    private bool loop = true;
    private bool rootMotion = false;
    private string statusMessage = "";

    private const string SP3_ANIM = "UltraMagnus_gs_attackSpecial_03";
    private const string SP3_TRANS = "UltraMagnus_gs_attackSpecial_03_transformed";
    private const string HEAVY_ANIM = "UltraMagnus_Normal_attackHeavy";
    private const string HEAVY_TRANS = "UltraMagnus_Normal_attackHeavy_transformed";
    private const string VEHICLE_SHOWCASE_KEY = "__VEHICLE_SHOWCASE__";
    private const string VEH_IDLE_TRANS = "frontend_Ultramagnus_gs_levelup_vehicle_idle_transformed";

    private Transform hipsUM;
    private Transform hipsTarn;
    private readonly Dictionary<Transform, Vector3> initPos = new Dictionary<Transform, Vector3>();
    private readonly Dictionary<Transform, Quaternion> initRot = new Dictionary<Transform, Quaternion>();
    private readonly Dictionary<Transform, Vector3> initScl = new Dictionary<Transform, Vector3>();

    private bool isPlayingSP3 = false;
    private bool isPlayingHeavy = false;
    private bool isVehicleShowcase = false;

    private float camYaw = 180.0f;
    private float camPitch = 6.0f;
    private float camDist = 19.5f;
    private Vector3 camPivot = new Vector3(0.0f, 5.8f, 0.0f);
    private Rect previewWindowRect = new Rect(16, 16, 370, 680);
    private Vector2 scrollPos = Vector2.zero;

    void Start() {
        InitAnimators();
        InitRenderers();
        LoadBundlesAndClips();
        ApplyCameraOrbit();
        if (displayAnimNames.Count > 0) PlayAnimation(displayAnimNames[0]);
    }

    void InitAnimators() {
        if (animOfficialUM == null) {
            var go = GameObject.Find("UltraMagnus_Official_Reference");
            if (go != null) animOfficialUM = go.GetComponent<Animator>();
        }
        if (animTarn == null) {
            var go = GameObject.Find("Tarn_Candidate");
            if (go != null) animTarn = go.GetComponent<Animator>();
        }

        foreach (var pair in new[] { animOfficialUM, animTarn }) {
            if (pair == null) continue;
            var hips = FindChildRecursive(pair.transform, "Hips");
            if (pair == animOfficialUM) hipsUM = hips; else hipsTarn = hips;
            var tr = FindChildRecursive(pair.transform, "transformed");
            if (tr != null) {
                var ta = tr.GetComponent<Animator>() ?? tr.gameObject.AddComponent<Animator>();
                if (pair == animOfficialUM) animTransUM = ta; else animTransTarn = ta;
            }
            foreach (var t in pair.GetComponentsInChildren<Transform>(true)) {
                initPos[t] = t.localPosition;
                initRot[t] = t.localRotation;
                initScl[t] = t.localScale;
            }
        }
    }

    void RestoreInitialBones() {
        foreach (var kv in initPos) {
            if (kv.Key != null) {
                kv.Key.localPosition = kv.Value;
                kv.Key.localRotation = initRot[kv.Key];
                kv.Key.localScale = initScl[kv.Key];
            }
        }
    }

    void InitRenderers() {
        if (animOfficialUM != null) {
            foreach (var smr in animOfficialUM.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
                if (smr.name.Contains("_00") && !smr.name.Contains("wpns")) smrRobotUM = smr;
                else if (smr.name.Contains("_01")) smrVehUM = smr;
            }
        }
        if (animTarn != null) {
            foreach (var smr in animTarn.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
                if (smr.name.Contains("_00") || smr.name.Contains("cha_tarn_gs_00")) smrRobotTarn = smr;
                else if (smr.name.Contains("_01") || smr.name.Contains("cha_tarn_gs_01")) smrVehTarn = smr;
            }
        }
    }

    public void SetVehicleMode(bool vehicleActive) {
        if (smrRobotUM != null) smrRobotUM.enabled = !vehicleActive;
        if (smrVehUM != null) { smrVehUM.gameObject.SetActive(true); smrVehUM.enabled = vehicleActive; }
        if (smrRobotTarn != null) smrRobotTarn.enabled = !vehicleActive;
        if (smrVehTarn != null) { smrVehTarn.gameObject.SetActive(true); smrVehTarn.enabled = vehicleActive; }
    }

    void LoadBundlesAndClips() {
        foreach (var b in AssetBundle.GetAllLoadedAssetBundles()) {
            if (b.name.Contains("character_anim_procedural")) bundleProcedural = b;
            else if (b.name.Contains("ultramagnus")) bundleUmAnims = b;
        }
        string umPath = @"E:\Agent\TFTF-blender\toolchain\ultramagnus_anims_registered.assetbundle";
        string procPath = @"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle";
        if (bundleUmAnims == null && File.Exists(umPath)) bundleUmAnims = AssetBundle.LoadFromFile(umPath);
        if (bundleProcedural == null && File.Exists(procPath)) bundleProcedural = AssetBundle.LoadFromFile(procPath);

        Avatar av00 = null, av01 = null;
        if (bundleUmAnims != null) {
            GameObject prefab = bundleUmAnims.LoadAsset<GameObject>("assets/bundles/characters/merged/ultramagnus_gs_leader/ultramagnus_gs_leader.prefab");
            if (prefab == null) prefab = bundleUmAnims.LoadAsset<GameObject>("UltraMagnus_GS_Leader");
            if (prefab != null) {
                var pAnim = prefab.GetComponent<Animator>();
                if (pAnim != null) av00 = pAnim.avatar;
                var tr = FindChildRecursive(prefab.transform, "transformed");
                if (tr != null && tr.GetComponent<Animator>() != null) av01 = tr.GetComponent<Animator>().avatar;
            }
            foreach (var c in bundleUmAnims.LoadAllAssets<AnimationClip>()) {
                if (c != null && !loadedClips.ContainsKey(c.name)) loadedClips[c.name] = c;
            }
        }
        if (bundleProcedural != null) {
            foreach (string ap in bundleProcedural.GetAllAssetNames()) {
                var subs = bundleProcedural.LoadAssetWithSubAssets(ap);
                if (subs != null) {
                    foreach (var s in subs) {
                        if (s is AnimationClip ac && !loadedClips.ContainsKey(ac.name)) loadedClips[ac.name] = ac;
                    }
                }
            }
        }

        if (av00 != null) {
            if (animOfficialUM != null) { animOfficialUM.avatar = av00; animOfficialUM.cullingMode = AnimatorCullingMode.AlwaysAnimate; }
            if (animTarn != null) { animTarn.avatar = av00; animTarn.cullingMode = AnimatorCullingMode.AlwaysAnimate; }
        }
        if (av01 != null) {
            if (animTransUM != null) { animTransUM.avatar = av01; animTransUM.cullingMode = AnimatorCullingMode.AlwaysAnimate; }
            if (animTransTarn != null) { animTransTarn.avatar = av01; animTransTarn.cullingMode = AnimatorCullingMode.AlwaysAnimate; }
        }

        string[] preferred = new[] {
            "UltraMagnus_gs_CombatIdle",
            "TeamSelect_Brawler_idle",
            "Prefight_Tactical_idle",
            "UltraMagnus_Normal_attackHeavy",
            "ultra_magnus_attackSpecial_01",
            "ultra_magnus_attackSpecial_02",
            SP3_ANIM,
            VEHICLE_SHOWCASE_KEY,
            "tactical_normal_attacklight_01_jab_L",
            "tactical_normal_attacklight_02_jab_R",
            "tactical_normal_attacklight_03_hook_L",
            "tactical_normal_attacklight_04_uppercut_R",
            "tactical_normal_attackMedium_01_elbow_L_01",
            "tactical_normal_attackMedium_02_kick_R",
            "dual pistols_attackRanged_gun_01",
            "dual pistols_attackRanged_gun_02",
            "dual pistols_attackRanged_gun_03",
            "Brute_Normal_Block",
            "brawler_normal_locoRun",
            "Ultramagnus_Normal_victory",
            "frontend_Tactical_Gacha_Reveal"
        };
        foreach (string n in preferred) {
            if (n == VEHICLE_SHOWCASE_KEY || (loadedClips.ContainsKey(n) && !displayAnimNames.Contains(n))) {
                displayAnimNames.Add(n);
            }
        }
        statusMessage = $"Loaded {loadedClips.Count} clips | Avatar00={(av00 != null ? av00.name : "NULL")}";
    }

    public void PlayAnimation(string animName) {
        DestroyGraphs();
        RestoreInitialBones();

        if (animName == VEHICLE_SHOWCASE_KEY) {
            currentAnim = animName;
            isPlayingSP3 = false;
            isPlayingHeavy = false;
            isVehicleShowcase = true;
            SetVehicleMode(true);
            camPivot = new Vector3(0f, 2.5f, 0f);
            ApplyCameraOrbit();
            if (loadedClips.TryGetValue(VEH_IDLE_TRANS, out AnimationClip vTr)) {
                SetupTransformedGraphs(vTr);
                if (graphTransUM.IsValid()) graphTransUM.Evaluate(0f);
                if (graphTransTarn.IsValid()) graphTransTarn.Evaluate(0f);
            }
            statusMessage = "Vehicle Mode Comparison (Tarn Tank vs UM Truck)";
            return;
        }

        if (!loadedClips.ContainsKey(animName)) {
            statusMessage = "Clip not found: " + animName;
            return;
        }

        currentAnim = animName;
        if (isVehicleShowcase) {
            camPivot = new Vector3(0f, 5.8f, 0f);
            ApplyCameraOrbit();
        }
        isVehicleShowcase = false;
        AnimationClip clip = loadedClips[animName];
        isPlayingSP3 = (animName == SP3_ANIM);
        isPlayingHeavy = (animName == HEAVY_ANIM);

        SetupRootGraphs(clip);
        if (isPlayingSP3 && loadedClips.TryGetValue(SP3_TRANS, out AnimationClip sp3Tr)) SetupTransformedGraphs(sp3Tr);
        else if (isPlayingHeavy && loadedClips.TryGetValue(HEAVY_TRANS, out AnimationClip hvTr)) SetupTransformedGraphs(hvTr);

        SetVehicleMode(false);
        statusMessage = $"Playing: {animName} ({clip.length:F2}s)";
    }

    void SetupRootGraphs(AnimationClip clip) {
        if (animOfficialUM != null) {
            animOfficialUM.applyRootMotion = rootMotion;
            graphUM = PlayableGraph.Create("UMGraph");
            playableUM = AnimationClipPlayable.Create(graphUM, clip);
            playableUM.SetApplyFootIK(false);
            var o = AnimationPlayableOutput.Create(graphUM, "Anim", animOfficialUM);
            o.SetSourcePlayable(playableUM);
            graphUM.Play();
        }
        if (animTarn != null) {
            animTarn.applyRootMotion = rootMotion;
            graphTarn = PlayableGraph.Create("TarnGraph");
            playableTarn = AnimationClipPlayable.Create(graphTarn, clip);
            playableTarn.SetApplyFootIK(false);
            var o = AnimationPlayableOutput.Create(graphTarn, "Anim", animTarn);
            o.SetSourcePlayable(playableTarn);
            graphTarn.Play();
        }
    }

    void SetupTransformedGraphs(AnimationClip transClip) {
        if (animTransUM != null) {
            animTransUM.applyRootMotion = rootMotion;
            graphTransUM = PlayableGraph.Create("TransUMGraph");
            playableTransUM = AnimationClipPlayable.Create(graphTransUM, transClip);
            playableTransUM.SetApplyFootIK(false);
            var o = AnimationPlayableOutput.Create(graphTransUM, "Anim", animTransUM);
            o.SetSourcePlayable(playableTransUM);
            graphTransUM.Play();
        }
        if (animTransTarn != null) {
            animTransTarn.applyRootMotion = rootMotion;
            graphTransTarn = PlayableGraph.Create("TransTarnGraph");
            playableTransTarn = AnimationClipPlayable.Create(graphTransTarn, transClip);
            playableTransTarn.SetApplyFootIK(false);
            var o = AnimationPlayableOutput.Create(graphTransTarn, "Anim", animTransTarn);
            o.SetSourcePlayable(playableTransTarn);
            graphTransTarn.Play();
        }
    }

    void Update() {
        if (Input.GetMouseButton(1) || Input.GetMouseButton(2)) {
            camYaw += Input.GetAxis("Mouse X") * 3.5f;
            camPitch = Mathf.Clamp(camPitch - Input.GetAxis("Mouse Y") * 2.5f, -25.0f, 65.0f);
            ApplyCameraOrbit();
        }
        float scroll = Input.GetAxis("Mouse ScrollWheel");
        if (Mathf.Abs(scroll) > 0.001f && !previewWindowRect.Contains(new Vector2(Input.mousePosition.x, Screen.height - Input.mousePosition.y))) {
            camDist = Mathf.Clamp(camDist - scroll * 6.0f, 6.0f, 36.0f);
            ApplyCameraOrbit();
        }

        if (isVehicleShowcase) {
            if (loadedClips.TryGetValue(VEH_IDLE_TRANS, out AnimationClip vc) && graphTransUM.IsValid() && playableTransUM.IsValid()) {
                double vt = playableTransUM.GetTime();
                if (loop && vt >= vc.length) {
                    playableTransUM.SetTime(0.0);
                    if (graphTransTarn.IsValid() && playableTransTarn.IsValid()) playableTransTarn.SetTime(0.0);
                }
            }
            return;
        }

        if (!loadedClips.TryGetValue(currentAnim, out AnimationClip clip)) return;
        double t = (graphUM.IsValid() && playableUM.IsValid()) ? playableUM.GetTime() : 0.0;
        if (isPlayingSP3) SetVehicleMode(t >= 0.85 && t <= 3.10);
        else if (isPlayingHeavy) SetVehicleMode(t >= 0.20 && t <= 0.85);

        if (loop && t >= clip.length) {
            if (graphUM.IsValid() && playableUM.IsValid()) playableUM.SetTime(0.0);
            if (graphTarn.IsValid() && playableTarn.IsValid()) playableTarn.SetTime(0.0);
            if (graphTransUM.IsValid() && playableTransUM.IsValid()) playableTransUM.SetTime(0.0);
            if (graphTransTarn.IsValid() && playableTransTarn.IsValid()) playableTransTarn.SetTime(0.0);
        }
    }

    void LateUpdate() {
        if (rootMotion) return;
        if (isVehicleShowcase && smrVehUM != null && smrVehTarn != null && animOfficialUM != null && animTarn != null) {
            animOfficialUM.transform.rotation = Quaternion.identity;
            animTarn.transform.rotation = Quaternion.identity;
            Bounds bU = smrVehUM.bounds;
            Bounds bT = smrVehTarn.bounds;
            animOfficialUM.transform.position += new Vector3(4.6f - bU.center.x, -bU.min.y, 0.0f - bU.center.z);
            animTarn.transform.position += new Vector3(-4.6f - bT.center.x, -bT.min.y, 0.0f - bT.center.z);
            return;
        }
        if (animOfficialUM != null && animTarn != null && hipsUM != null && hipsTarn != null) {
            animOfficialUM.transform.rotation = Quaternion.identity;
            animTarn.transform.rotation = Quaternion.identity;
            float spacing = 5.0f;
            Vector3 dU = hipsUM.position - animOfficialUM.transform.position;
            animOfficialUM.transform.position = new Vector3(spacing - dU.x, 0.0f, 0.0f - dU.z);
            Vector3 dT = hipsTarn.position - animTarn.transform.position;
            animTarn.transform.position = new Vector3(-spacing - dT.x, 0.0f, 0.0f - dT.z);
        }
    }

    void ApplyCameraOrbit() {
        Camera cam = Camera.main;
        if (cam == null) return;
        Quaternion rot = Quaternion.Euler(camPitch, camYaw, 0.0f);
        cam.transform.position = camPivot + rot * new Vector3(0.0f, 0.0f, -camDist);
        cam.transform.LookAt(camPivot);
    }

    void DestroyGraphs() {
        if (graphUM.IsValid()) graphUM.Destroy();
        if (graphTarn.IsValid()) graphTarn.Destroy();
        if (graphTransUM.IsValid()) graphTransUM.Destroy();
        if (graphTransTarn.IsValid()) graphTransTarn.Destroy();
    }

    void OnDestroy() {
        DestroyGraphs();
        if (bundleProcedural != null) bundleProcedural.Unload(false);
        if (bundleUmAnims != null) bundleUmAnims.Unload(false);
    }

    void OnGUI() {
        previewWindowRect = GUI.Window(9942, previewWindowRect, DrawPreviewWindow, "塔恩 (Tarn) vs 通天晓 同步动作验收台");
    }

    void DrawPreviewWindow(int id) {
        double currentT = (graphUM.IsValid() && playableUM.IsValid()) ? playableUM.GetTime() : 0.0;
        GUILayout.Label($"当前动作: {currentAnim} [{currentT:F2}s]");
        GUILayout.BeginHorizontal();
        if (GUILayout.Button("正面全景")) { camYaw = 180f; camPitch = 6f; camDist = 19.5f; camPivot = new Vector3(0f, 5.8f, 0f); ApplyCameraOrbit(); }
        if (GUILayout.Button("45°斜侧")) { camYaw = 148f; camPitch = 10f; camDist = 19.5f; camPivot = new Vector3(0f, 5.8f, 0f); ApplyCameraOrbit(); }
        if (GUILayout.Button("背面")) { camYaw = 15f; camPitch = 10f; camDist = 19.5f; camPivot = new Vector3(0f, 5.8f, 0f); ApplyCameraOrbit(); }
        GUILayout.EndHorizontal();

        scrollPos = GUILayout.BeginScrollView(scrollPos, GUILayout.Height(520));
        foreach (string aName in displayAnimNames) {
            GUI.color = (aName == currentAnim) ? Color.green : Color.white;
            if (GUILayout.Button(aName, GUILayout.Height(26))) PlayAnimation(aName);
        }
        GUI.color = Color.white;
        GUILayout.EndScrollView();
        GUILayout.Label(statusMessage, GUI.skin.box);
        GUI.DragWindow(new Rect(0, 0, 10000, 24));
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
