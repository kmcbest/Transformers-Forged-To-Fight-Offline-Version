using UnityEngine;
using UnityEngine.Playables;
using UnityEngine.Animations;
using System.IO;
using System.Collections.Generic;

public class OnslaughtPreviewController : MonoBehaviour {
    public Animator animIronhide;
    public Animator animOnslaught;

    private Animator animTransIronhide;
    private Animator animTransOnslaught;

    private SkinnedMeshRenderer smrRobotIronhide;
    private SkinnedMeshRenderer smrVehIronhide;
    private SkinnedMeshRenderer smrRobotOnslaught;
    private SkinnedMeshRenderer smrVehOnslaught;

    private AssetBundle bundleProcedural;
    private AssetBundle bundleIronhide;
    private AssetBundle bundleIronhideAnims;
    private Dictionary<string, AnimationClip> loadedClips = new Dictionary<string, AnimationClip>();

    private PlayableGraph graphIronhide;
    private PlayableGraph graphOnslaught;
    private PlayableGraph graphTransIronhide;
    private PlayableGraph graphTransOnslaught;

    private AnimationClipPlayable playableIronhide;
    private AnimationClipPlayable playableOnslaught;
    private AnimationClipPlayable playableTransIronhide;
    private AnimationClipPlayable playableTransOnslaught;

    private List<string> displayAnimNames = new List<string>();
    private string currentAnim = "";
    private bool loop = true;
    private bool rootMotion = false;
    private string statusMessage = "";

    private const string SP3_ANIM_NAME = "Ironhide_Normal_attackSpecial_03";
    private const string SP3_TRANS_CLIP = "Ironhide_Normal_attackSpecial_03_transformed";
    private const string HEAVY_ANIM_NAME = "Ironhide_Normal_attackHeavy";
    private const string HEAVY_TRANS_CLIP = "Ironhide_Normal_attackHeavy_transformed";
    private const string VEHICLE_SHOWCASE_KEY = "__VEHICLE_SHOWCASE__";
    private const string VEHICLE_ROOT_IDLE_CLIP = "frontend_Optimus_levelup_vehicle_idle";
    private const string VEHICLE_IDLE_CLIP = "frontend_Ironhide_levelup_vehicle_idle_transformed";

    private Transform refIronhide;
    private Transform refOnslaught;
    private Transform hipsIronhide;
    private Transform hipsOnslaught;
    private Vector3 hipsInitPosIh, hipsInitPosOns;
    private Quaternion hipsInitRotIh, hipsInitRotOns;
    private Dictionary<Transform, Vector3> initBonePos = new Dictionary<Transform, Vector3>();
    private Dictionary<Transform, Quaternion> initBoneRot = new Dictionary<Transform, Quaternion>();
    private Dictionary<Transform, Vector3> initBoneScl = new Dictionary<Transform, Vector3>();
    private bool vehUsesSp3Window = false;

    public float sp3VehicleStart = 1.15f;
    public float sp3VehicleEnd = 3.65f;
    public float heavyVehicleStart = 0.22f;
    public float heavyVehicleEnd = 0.72f;
    private bool isPlayingSP3 = false;
    private bool isPlayingHeavy = false;
    private bool isVehicleShowcase = false;

    // Simple camera orbit state
    private float camYaw = 180.0f;
    private float camPitch = 6.0f;
    private float camDist = 17.5f;
    private Vector3 camPivot = new Vector3(0.0f, 5.0f, 0.0f);

    void Start() {
        CleanScene();
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
        if (animIronhide == null) {
            var go = GameObject.Find("Ironhide_Official_Reference");
            if (go != null) animIronhide = go.GetComponent<Animator>();
        }
        if (animOnslaught == null) {
            var go = GameObject.Find("Onslaught_Candidate");
            if (go != null) animOnslaught = go.GetComponent<Animator>();
        }

        if (animIronhide != null) {
            refIronhide = FindChildRecursive(animIronhide.transform, "Reference");
            hipsIronhide = FindChildRecursive(animIronhide.transform, "Hips");
            if (hipsIronhide != null) {
                hipsInitPosIh = hipsIronhide.localPosition;
                hipsInitRotIh = hipsIronhide.localRotation;
            }
            var tr = FindChildRecursive(animIronhide.transform, "transformed");
            if (tr != null) {
                animTransIronhide = tr.GetComponent<Animator>();
                if (animTransIronhide == null) animTransIronhide = tr.gameObject.AddComponent<Animator>();
            }
        }

        if (animOnslaught != null) {
            refOnslaught = FindChildRecursive(animOnslaught.transform, "Reference");
            hipsOnslaught = FindChildRecursive(animOnslaught.transform, "Hips");
            if (hipsOnslaught != null) {
                hipsInitPosOns = hipsOnslaught.localPosition;
                hipsInitRotOns = hipsOnslaught.localRotation;
            }
            var tr = FindChildRecursive(animOnslaught.transform, "transformed");
            if (tr != null) {
                animTransOnslaught = tr.GetComponent<Animator>();
                if (animTransOnslaught == null) animTransOnslaught = tr.gameObject.AddComponent<Animator>();
            }
        }

        initBonePos.Clear();
        initBoneRot.Clear();
        initBoneScl.Clear();
        if (animIronhide != null) {
            foreach (var t in animIronhide.GetComponentsInChildren<Transform>(true)) {
                initBonePos[t] = t.localPosition; initBoneRot[t] = t.localRotation; initBoneScl[t] = t.localScale;
            }
        }
        if (animOnslaught != null) {
            foreach (var t in animOnslaught.GetComponentsInChildren<Transform>(true)) {
                initBonePos[t] = t.localPosition; initBoneRot[t] = t.localRotation; initBoneScl[t] = t.localScale;
            }
        }
    }

    void RestoreInitialBones() {
        foreach (var kv in initBonePos) {
            if (kv.Key != null) {
                kv.Key.localPosition = kv.Value;
                kv.Key.localRotation = initBoneRot[kv.Key];
                kv.Key.localScale = initBoneScl[kv.Key];
            }
        }
    }

    void InitRenderers() {
        if (animIronhide != null) {
            foreach (var smr in animIronhide.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
                if (smr.name.Contains("_00")) smrRobotIronhide = smr;
                else if (smr.name.Contains("_01")) smrVehIronhide = smr;
            }
        }

        if (animOnslaught != null) {
            foreach (var smr in animOnslaught.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
                if (smr.name.Contains("_00") || smr.name.Contains("cha_onslaught_gs_00")) smrRobotOnslaught = smr;
                else if (smr.name.Contains("_01") || smr.name.Contains("cha_onslaught_gs_01")) smrVehOnslaught = smr;
            }
        }
    }

    public void SetVehicleMode(bool vehicleActive) {
        if (smrRobotIronhide != null) smrRobotIronhide.enabled = !vehicleActive;
        if (smrVehIronhide != null) {
            smrVehIronhide.gameObject.SetActive(true);
            smrVehIronhide.enabled = vehicleActive;
        }

        if (smrRobotOnslaught != null) smrRobotOnslaught.enabled = !vehicleActive;
        if (smrVehOnslaught != null) {
            smrVehOnslaught.gameObject.SetActive(true);
            smrVehOnslaught.enabled = vehicleActive;
        }
    }

    void LoadBundlesAndClips() {
        foreach (var b in AssetBundle.GetAllLoadedAssetBundles()) {
            if (b.name.Contains("character_anim_procedural")) bundleProcedural = b;
            else if (b.name.Contains("ironhide") || b.GetAllAssetNames().Length > 0 && b.GetAllAssetNames()[0].Contains("ironhide")) bundleIronhide = b;
        }

        // Load ONLY ironhide_anims_registered.assetbundle (which is ironhide_cin_rotf + all registered clips in m_Container, avoiding CAB collision!)
        string ihAnimsPath = @"E:\Agent\TFTF-blender\toolchain\ironhide_anims_registered.assetbundle";
        string ihFallbackPath = @"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\ironhide_cin_rotf_odr\ironhide_cin_rotf.assetbundle";
        if (bundleIronhide == null) {
            if (File.Exists(ihAnimsPath)) bundleIronhide = AssetBundle.LoadFromFile(ihAnimsPath);
            else if (File.Exists(ihFallbackPath)) bundleIronhide = AssetBundle.LoadFromFile(ihFallbackPath);
        }

        string procPath = @"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle";
        if (bundleProcedural == null && File.Exists(procPath)) {
            bundleProcedural = AssetBundle.LoadFromFile(procPath);
        }

        Avatar officialAvatar = null;
        Avatar vhAvatar = null;

        if (bundleIronhide != null) {
            GameObject prefab = bundleIronhide.LoadAsset<GameObject>("assets/bundles/characters/merged/ironhide_cin_rotf/ironhide_cin_rotf.prefab");
            if (prefab == null) prefab = bundleIronhide.LoadAsset<GameObject>("IronHide_Cin_ROTF");
            if (prefab != null) {
                Animator pAnim = prefab.GetComponent<Animator>();
                if (pAnim != null) {
                    officialAvatar = pAnim.avatar;
                    if (pAnim.runtimeAnimatorController != null) {
                        foreach (var c in pAnim.runtimeAnimatorController.animationClips) {
                            if (c != null && !loadedClips.ContainsKey(c.name)) loadedClips[c.name] = c;
                        }
                    }
                }
                Transform tr = FindChildRecursive(prefab.transform, "transformed");
                if (tr != null) {
                    Animator trAnim = tr.GetComponent<Animator>();
                    if (trAnim != null) {
                        vhAvatar = trAnim.avatar;
                        if (trAnim.runtimeAnimatorController != null) {
                            foreach (var c in trAnim.runtimeAnimatorController.animationClips) {
                                if (c != null && !loadedClips.ContainsKey(c.name)) loadedClips[c.name] = c;
                            }
                        }
                    }
                }
            }

            foreach (var c in bundleIronhide.LoadAllAssets<AnimationClip>()) {
                if (c != null && !loadedClips.ContainsKey(c.name)) loadedClips[c.name] = c;
            }
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

        if (officialAvatar != null) {
            if (animIronhide != null) { animIronhide.avatar = officialAvatar; animIronhide.cullingMode = AnimatorCullingMode.AlwaysAnimate; }
            if (animOnslaught != null) { animOnslaught.avatar = officialAvatar; animOnslaught.cullingMode = AnimatorCullingMode.AlwaysAnimate; }
        }
        if (vhAvatar != null) {
            if (animTransIronhide != null) { animTransIronhide.avatar = vhAvatar; animTransIronhide.cullingMode = AnimatorCullingMode.AlwaysAnimate; }
            if (animTransOnslaught != null) { animTransOnslaught.avatar = vhAvatar; animTransOnslaught.cullingMode = AnimatorCullingMode.AlwaysAnimate; }
        }

        string[] preferredOrder = new string[] {
            "brawler_normal_idle",
            "TeamSelect_Brawler_idle",
            "Prefight_Brawler_idle",
            "Ironhide_Normal_attackHeavy",
            "Ironhide_Normal_attackSpecial_01",
            "Ironhide_Normal_attackSpecial_02",
            SP3_ANIM_NAME,
            VEHICLE_SHOWCASE_KEY,
            "brawler_normal_attackLight_01_jab",
            "brawler_normal_attackLight_02_jab",
            "brawler_normal_attackLight_03_uppcut",
            "brawler_normal_attackLight_04_frontkick",
            "brawler_normal_attackMedium_01_backhand",
            "brawler_normal_attackMedium_02_shouldercharge",
            "brawler_normal_block",
            "Brawler_Normal_Victory"
        };

        foreach (string name in preferredOrder) {
            if (name == VEHICLE_SHOWCASE_KEY) {
                displayAnimNames.Add(name);
            } else if (loadedClips.ContainsKey(name) && !displayAnimNames.Contains(name)) {
                displayAnimNames.Add(name);
            }
        }

        statusMessage = $"Loaded {loadedClips.Count} clips | Avatar00={(officialAvatar != null ? officialAvatar.name : "NULL")}";
    }

    public void PlayAnimation(string animName) {
        DestroyGraphs();
        RestoreInitialBones();

        if (animName == VEHICLE_SHOWCASE_KEY) {
            currentAnim = animName;
            isPlayingSP3 = false;
            isPlayingHeavy = false;
            isVehicleShowcase = true;
            vehUsesSp3Window = false;
            SetVehicleMode(true);
            camPivot = new Vector3(0.0f, 2.3f, 0.0f);
            ApplyCameraOrbit();

            // Use verified straight-forward level pose (Ironhide_Normal_attackHeavy + _transformed @ 0.45s, rot=(1.5, 0.2, 0.6)!)
            if (loadedClips.TryGetValue(HEAVY_ANIM_NAME, out AnimationClip hRoot) && loadedClips.TryGetValue(HEAVY_TRANS_CLIP, out AnimationClip hTr)) {
                SetupRootGraphs(hRoot);
                SetupTransformedGraphs(hTr);
                if (playableIronhide.IsValid()) { playableIronhide.SetTime(0.45); playableIronhide.SetSpeed(0.0); }
                if (playableOnslaught.IsValid()) { playableOnslaught.SetTime(0.45); playableOnslaught.SetSpeed(0.0); }
                if (playableTransIronhide.IsValid()) { playableTransIronhide.SetTime(0.45); playableTransIronhide.SetSpeed(0.0); }
                if (playableTransOnslaught.IsValid()) { playableTransOnslaught.SetTime(0.45); playableTransOnslaught.SetSpeed(0.0); }
                if (graphIronhide.IsValid()) graphIronhide.Evaluate(0f);
                if (graphOnslaught.IsValid()) graphOnslaught.Evaluate(0f);
                if (graphTransIronhide.IsValid()) graphTransIronhide.Evaluate(0f);
                if (graphTransOnslaught.IsValid()) graphTransOnslaught.Evaluate(0f);
                statusMessage = "Vehicle Mode Comparison (360° Level Showcase @ 0.45s)";
                return;
            }
            statusMessage = "Vehicle Mode Comparison";
            return;
        }

        if (!loadedClips.ContainsKey(animName)) {
            statusMessage = "Clip not found: " + animName;
            return;
        }

        currentAnim = animName;
        if (isVehicleShowcase) {
            camPivot = new Vector3(0.0f, 5.0f, 0.0f);
            ApplyCameraOrbit();
        }
        isVehicleShowcase = false;
        AnimationClip clip = loadedClips[animName];
        isPlayingSP3 = (animName == SP3_ANIM_NAME);
        isPlayingHeavy = (animName == HEAVY_ANIM_NAME);

        SetupRootGraphs(clip);

        if (isPlayingSP3 && loadedClips.TryGetValue(SP3_TRANS_CLIP, out AnimationClip transClip)) {
            SetupTransformedGraphs(transClip);
        } else if (isPlayingHeavy && loadedClips.TryGetValue(HEAVY_TRANS_CLIP, out AnimationClip heavyTransClip)) {
            SetupTransformedGraphs(heavyTransClip);
        }

        SetVehicleMode(false);
        statusMessage = $"Playing: {animName} ({clip.length:F2}s)";
    }

    void SetupRootGraphs(AnimationClip clip) {
        if (animIronhide != null) {
            animIronhide.applyRootMotion = rootMotion;
            graphIronhide = PlayableGraph.Create("IronhideGraph");
            playableIronhide = AnimationClipPlayable.Create(graphIronhide, clip);
            playableIronhide.SetApplyFootIK(false);
            var output = AnimationPlayableOutput.Create(graphIronhide, "Animation", animIronhide);
            output.SetSourcePlayable(playableIronhide);
            graphIronhide.Play();
        }

        if (animOnslaught != null) {
            animOnslaught.applyRootMotion = rootMotion;
            graphOnslaught = PlayableGraph.Create("OnslaughtGraph");
            playableOnslaught = AnimationClipPlayable.Create(graphOnslaught, clip);
            playableOnslaught.SetApplyFootIK(false);
            var output = AnimationPlayableOutput.Create(graphOnslaught, "Animation", animOnslaught);
            output.SetSourcePlayable(playableOnslaught);
            graphOnslaught.Play();
        }
    }

    void SetupTransformedGraphs(AnimationClip transClip) {
        if (animTransIronhide != null) {
            animTransIronhide.applyRootMotion = rootMotion;
            graphTransIronhide = PlayableGraph.Create("TransIronhideGraph");
            playableTransIronhide = AnimationClipPlayable.Create(graphTransIronhide, transClip);
            playableTransIronhide.SetApplyFootIK(false);
            var outTrans = AnimationPlayableOutput.Create(graphTransIronhide, "Animation", animTransIronhide);
            outTrans.SetSourcePlayable(playableTransIronhide);
            graphTransIronhide.Play();
        }

        if (animTransOnslaught != null) {
            animTransOnslaught.applyRootMotion = rootMotion;
            graphTransOnslaught = PlayableGraph.Create("TransOnslaughtGraph");
            playableTransOnslaught = AnimationClipPlayable.Create(graphTransOnslaught, transClip);
            playableTransOnslaught.SetApplyFootIK(false);
            var outTrans = AnimationPlayableOutput.Create(graphTransOnslaught, "Animation", animTransOnslaught);
            outTrans.SetSourcePlayable(playableTransOnslaught);
            graphTransOnslaught.Play();
        }
    }

    void Update() {
        // Right-mouse or Middle-mouse orbit + scroll zoom (outside GUI window)
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
            if (vehUsesSp3Window) {
                if (graphIronhide.IsValid() && playableIronhide.IsValid() && playableIronhide.GetTime() >= 2.65) {
                    playableIronhide.SetTime(1.90);
                    if (playableOnslaught.IsValid()) playableOnslaught.SetTime(1.90);
                    if (playableTransIronhide.IsValid()) playableTransIronhide.SetTime(1.90);
                    if (playableTransOnslaught.IsValid()) playableTransOnslaught.SetTime(1.90);
                }
            } else if (loadedClips.TryGetValue(VEHICLE_IDLE_CLIP, out AnimationClip vClip) && graphTransIronhide.IsValid() && playableTransIronhide.IsValid()) {
                double vt = playableTransIronhide.GetTime();
                if (loop && vt >= vClip.length) {
                    playableTransIronhide.SetTime(0.0);
                    if (graphTransOnslaught.IsValid() && playableTransOnslaught.IsValid()) playableTransOnslaught.SetTime(0.0);
                }
            }
            return;
        }

        if (!loadedClips.TryGetValue(currentAnim, out AnimationClip clip)) return;

        double t = 0.0;
        if (graphIronhide.IsValid() && playableIronhide.IsValid()) t = playableIronhide.GetTime();

        if (isPlayingSP3) {
            bool inVehicle = (t >= sp3VehicleStart && t <= sp3VehicleEnd);
            SetVehicleMode(inVehicle);
        } else if (isPlayingHeavy) {
            bool inVehicle = (t >= heavyVehicleStart && t <= heavyVehicleEnd);
            SetVehicleMode(inVehicle);
        }

        if (loop && t >= clip.length) {
            if (graphIronhide.IsValid() && playableIronhide.IsValid()) playableIronhide.SetTime(0.0);
            if (graphOnslaught.IsValid() && playableOnslaught.IsValid()) playableOnslaught.SetTime(0.0);
            if (graphTransIronhide.IsValid() && playableTransIronhide.IsValid()) playableTransIronhide.SetTime(0.0);
            if (graphTransOnslaught.IsValid() && playableTransOnslaught.IsValid()) playableTransOnslaught.SetTime(0.0);
        }
    }

    void LateUpdate() {
        if (rootMotion) return;
        if (isVehicleShowcase && smrVehIronhide != null && smrVehOnslaught != null && animIronhide != null && animOnslaught != null) {
            animIronhide.transform.rotation = Quaternion.identity;
            animOnslaught.transform.rotation = Quaternion.identity;
            Bounds bIh = smrVehIronhide.bounds;
            Bounds bOns = smrVehOnslaught.bounds;
            animIronhide.transform.position += new Vector3(4.5f - bIh.center.x, -bIh.min.y, 0.0f - bIh.center.z);
            animOnslaught.transform.position += new Vector3(-4.5f - bOns.center.x, -bOns.min.y, 0.0f - bOns.center.z);
            return;
        }
        // Keep both characters cleanly centered side-by-side at X = ±spacing, Z = 0 without touching bone/root rotations!
        if (animIronhide != null && animOnslaught != null && hipsIronhide != null && hipsOnslaught != null) {
            animIronhide.transform.rotation = Quaternion.identity;
            animOnslaught.transform.rotation = Quaternion.identity;
            float spacing = 3.9f;
            Vector3 dIh = hipsIronhide.position - animIronhide.transform.position;
            animIronhide.transform.position = new Vector3(spacing - dIh.x, 0.0f, 0.0f - dIh.z);
            Vector3 dOns = hipsOnslaught.position - animOnslaught.transform.position;
            animOnslaught.transform.position = new Vector3(-spacing - dOns.x, 0.0f, 0.0f - dOns.z);
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
        if (graphIronhide.IsValid()) graphIronhide.Destroy();
        if (graphOnslaught.IsValid()) graphOnslaught.Destroy();
        if (graphTransIronhide.IsValid()) graphTransIronhide.Destroy();
        if (graphTransOnslaught.IsValid()) graphTransOnslaught.Destroy();
    }

    void OnDestroy() {
        DestroyGraphs();
        if (bundleProcedural != null) bundleProcedural.Unload(false);
        if (bundleIronhideAnims != null) bundleIronhideAnims.Unload(false);
        if (bundleIronhide != null) bundleIronhide.Unload(false);
    }

    private Rect previewWindowRect = new Rect(16, 16, 370, 680);
    private Vector2 scrollPos = Vector2.zero;

    void OnGUI() {
        Camera cam = Camera.main;
        if (cam != null) {
            GUIStyle tagStyle = new GUIStyle(GUI.skin.box);
            tagStyle.fontSize = 13;
            tagStyle.fontStyle = FontStyle.Bold;
            tagStyle.alignment = TextAnchor.MiddleCenter;
            tagStyle.normal.textColor = Color.white;

            bool vehOn = (smrVehOnslaught != null && smrVehOnslaught.enabled);
            float labelHeight = vehOn ? 4.4f : 11.2f;

            if (animIronhide != null) {
                Vector3 sp = cam.WorldToScreenPoint(animIronhide.transform.position + Vector3.up * labelHeight);
                if (sp.z > 0) {
                    GUI.backgroundColor = new Color(0.15f, 0.60f, 0.95f, 0.92f);
                    string mode = vehOn ? " [GMC Topkick 载具]" : " [人形母体]";
                    GUI.Box(new Rect(sp.x - 155, Screen.height - sp.y - 28, 310, 28), "电影铁皮 (Ironhide 官方原版)" + mode, tagStyle);
                }
            }

            if (animOnslaught != null) {
                Vector3 sp = cam.WorldToScreenPoint(animOnslaught.transform.position + Vector3.up * labelHeight);
                if (sp.z > 0) {
                    GUI.backgroundColor = new Color(0.62f, 0.25f, 0.92f, 0.92f);
                    string mode = vehOn ? " [赛星重型导弹车]" : " [新角色模具]";
                    GUI.Box(new Rect(sp.x - 155, Screen.height - sp.y - 28, 310, 28), "袭击 (Onslaught 战车队首领)" + mode, tagStyle);
                }
            }
            GUI.backgroundColor = Color.white;
        }

        previewWindowRect = GUI.Window(9922, previewWindowRect, DrawPreviewWindow, "袭击 vs 电影铁皮 同步动作验收台 (右键旋转/滚轮缩放)");
    }

    void DrawPreviewWindow(int id) {
        double currentT = (graphIronhide.IsValid() && playableIronhide.IsValid()) ? playableIronhide.GetTime() : 0.0;
        GUILayout.Label($"当前动作: {GetFriendlyLabel(currentAnim)} [{currentT:F2}s]");

        GUILayout.BeginHorizontal();
        if (GUILayout.Button("正面全景")) { camYaw = 180f; camPitch = 6f; camDist = 17.5f; camPivot = new Vector3(0f, 5.0f, 0f); ApplyCameraOrbit(); }
        if (GUILayout.Button("45°斜侧")) { camYaw = 148f; camPitch = 10f; camDist = 17.5f; camPivot = new Vector3(0f, 5.0f, 0f); ApplyCameraOrbit(); }
        if (GUILayout.Button("背面背炮")) { camYaw = 15f; camPitch = 10f; camDist = 17.5f; camPivot = new Vector3(0f, 5.2f, 0f); ApplyCameraOrbit(); }
        if (GUILayout.Button("近景特写")) { camYaw = 180f; camPitch = 4f; camDist = 11.5f; camPivot = new Vector3(0f, 6.2f, 0f); ApplyCameraOrbit(); }
        GUILayout.EndHorizontal();

        GUILayout.BeginHorizontal();
        loop = GUILayout.Toggle(loop, " 循环播放 (Loop)");
        bool prevRoot = rootMotion;
        rootMotion = GUILayout.Toggle(rootMotion, " 根骨骼位移 (Root Motion)");
        if (prevRoot != rootMotion) {
            if (animIronhide != null) animIronhide.applyRootMotion = rootMotion;
            if (animOnslaught != null) animOnslaught.applyRootMotion = rootMotion;
            if (animTransIronhide != null) animTransIronhide.applyRootMotion = rootMotion;
            if (animTransOnslaught != null) animTransOnslaught.applyRootMotion = rootMotion;
        }
        GUILayout.EndHorizontal();

        GUILayout.Space(4);
        scrollPos = GUILayout.BeginScrollView(scrollPos, GUILayout.Height(495));
        foreach (string aName in displayAnimNames) {
            GUI.color = (aName == currentAnim) ? Color.green : Color.white;
            if (GUILayout.Button(GetFriendlyLabel(aName), GUILayout.Height(28))) {
                PlayAnimation(aName);
            }
        }
        GUI.color = Color.white;
        GUILayout.EndScrollView();

        GUILayout.Label(statusMessage, GUI.skin.box);
        GUI.DragWindow(new Rect(0, 0, 10000, 24));
    }

    string GetFriendlyLabel(string aName) {
        switch (aName) {
            case "brawler_normal_idle": return "战斗站姿 (Combat Stance Idle)";
            case "TeamSelect_Brawler_idle": return "展示厅待机 (TeamSelect Idle)";
            case "Prefight_Brawler_idle": return "战前待机 (Prefight Idle)";
            case "Ironhide_Normal_attackHeavy": return "★ 重击：双臂重炮齐射 (Heavy Shoot)";
            case "Ironhide_Normal_attackSpecial_01": return "★ SP1：翻滚重炮轰击 (Special 1)";
            case "Ironhide_Normal_attackSpecial_02": return "★ SP2：跃起双炮爆破 (Special 2)";
            case SP3_ANIM_NAME: return "★ SP3：变身突进全弹发射 (Special 3)";
            case VEHICLE_SHOWCASE_KEY: return "★ 载具形态静态/动态对比 (Vehicle Mode)";
            case "brawler_normal_attackLight_01_jab": return "轻击 1：刺拳 (Light 1 Jab)";
            case "brawler_normal_attackLight_02_jab": return "轻击 2：直拳 (Light 2 Jab)";
            case "brawler_normal_attackLight_03_uppcut": return "轻击 3：上勾拳 (Light 3 Uppercut)";
            case "brawler_normal_attackLight_04_frontkick": return "轻击 4：正蹬踢 (Light 4 Kick)";
            case "brawler_normal_attackMedium_01_backhand": return "中击 1：反手重锤 (Medium 1)";
            case "brawler_normal_attackMedium_02_shouldercharge": return "中击 2：铁山靠冲撞 (Medium 2)";
            case "brawler_normal_block": return "格挡姿态 (Block)";
            case "Brawler_Normal_Victory": return "胜利动作 (Victory)";
            default: return aName;
        }
    }

    private static Transform FindChildRecursive(Transform parent, string name) {
        if (parent.name == name) return parent;
        for (int i = 0; i < parent.childCount; i++) {
            Transform f = FindChildRecursive(parent.GetChild(i), name);
            if (f != null) return f;
        }
        return null;
    }
}
