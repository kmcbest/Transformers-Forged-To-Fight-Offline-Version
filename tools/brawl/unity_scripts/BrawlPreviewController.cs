using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;

public class BrawlPreviewController : MonoBehaviour {
    public Animator animOfficialMegatron;
    public Animator animBrawl;

    private Animator animTrOfficial;
    private Animator animTrBrawl;

    private SkinnedMeshRenderer smrRobotOfficial;
    private SkinnedMeshRenderer smrVehOfficial;
    private SkinnedMeshRenderer smrRobotBrawl;
    private SkinnedMeshRenderer smrVehBrawl;

    private PlayableGraph graphMegatron;
    private PlayableGraph graphBrawl;
    private PlayableGraph graphTrMegatron;
    private PlayableGraph graphTrBrawl;

    private AnimationClipPlayable playableMegatron;
    private AnimationClipPlayable playableBrawl;
    private AnimationClipPlayable playableTrMegatron;
    private AnimationClipPlayable playableTrBrawl;

    private readonly List<AnimationClip> m_Clips = new List<AnimationClip>();
    private int m_CurrentClipIdx = 0;
    private bool m_IsVehicle = false;
    private bool m_IsPlaying = true;
    private float m_PlaySpeed = 1.0f;
    private float m_ScrubTime = 0.0f;

    private float camYaw = 180.0f;
    private float camPitch = 6.0f;
    private float camDist = 17.5f;
    private Vector3 camPivot = new Vector3(-2.2f, 5.0f, 0.0f);

    private readonly Dictionary<Transform, Vector3> m_RestPos = new Dictionary<Transform, Vector3>();
    private readonly Dictionary<Transform, Quaternion> m_RestRot = new Dictionary<Transform, Quaternion>();

    void Start() {
        InitReferences();
        LoadAnimations();
        ApplyCameraOrbit();
        if (m_Clips.Count > 0) PlayClip(0);
    }

    void InitReferences() {
        if (animOfficialMegatron == null) {
            var go = GameObject.Find("Megatron_Official_Reference");
            if (go != null) animOfficialMegatron = go.GetComponent<Animator>();
        }
        if (animBrawl == null) {
            var go = GameObject.Find("Brawl_Candidate");
            if (go != null) animBrawl = go.GetComponent<Animator>();
        }

        if (animOfficialMegatron != null) {
            foreach (var smr in animOfficialMegatron.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
                if (smr.name.Contains("_00")) smrRobotOfficial = smr;
                else if (smr.name.Contains("_01")) smrVehOfficial = smr;
            }
            Transform tr = FindChildRecursive(animOfficialMegatron.transform, "transformed");
            if (tr != null) animTrOfficial = tr.GetComponent<Animator>() ?? tr.gameObject.AddComponent<Animator>();
        }

        if (animBrawl != null) {
            foreach (var smr in animBrawl.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
                if (smr.name.Contains("_00")) smrRobotBrawl = smr;
                else if (smr.name.Contains("_01")) smrVehBrawl = smr;
            }
            Transform tr = FindChildRecursive(animBrawl.transform, "transformed");
            if (tr != null) animTrBrawl = tr.GetComponent<Animator>() ?? tr.gameObject.AddComponent<Animator>();
        }

        SnapshotRests(animOfficialMegatron);
        SnapshotRests(animBrawl);
    }

    void SnapshotRests(Animator anim) {
        if (anim == null) return;
        foreach (var t in anim.GetComponentsInChildren<Transform>(true)) {
            m_RestPos[t] = t.localPosition;
            m_RestRot[t] = t.localRotation;
        }
    }

    void RestoreRests() {
        foreach (var kvp in m_RestPos) {
            if (kvp.Key != null) {
                kvp.Key.localPosition = kvp.Value;
                kvp.Key.localRotation = m_RestRot[kvp.Key];
            }
        }
    }

    void LoadAnimations() {
        m_Clips.Clear();

        string megPath = @"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle";
        if (File.Exists(megPath)) {
            AssetBundle b = AssetBundle.LoadFromFile(megPath);
            if (b != null) {
                GameObject mp = b.LoadAsset<GameObject>("assets/bundles/characters/merged/megatron_cin_rotf/megatron_cin_rotf.prefab");
                if (mp != null) {
                    Avatar av0 = mp.GetComponent<Animator>() != null ? mp.GetComponent<Animator>().avatar : null;
                    Transform mpTr = FindChildRecursive(mp.transform, "transformed");
                    Avatar av1 = (mpTr != null && mpTr.GetComponent<Animator>() != null) ? mpTr.GetComponent<Animator>().avatar : null;
                    if (av0 != null) {
                        if (animOfficialMegatron != null) animOfficialMegatron.avatar = av0;
                        if (animBrawl != null) animBrawl.avatar = av0;
                    }
                    if (av1 != null) {
                        if (animTrOfficial != null) animTrOfficial.avatar = av1;
                        if (animTrBrawl != null) animTrBrawl.avatar = av1;
                    }
                }
                foreach (var c in b.LoadAllAssets<AnimationClip>()) {
                    if (c != null && !m_Clips.Contains(c)) m_Clips.Add(c);
                }
                b.Unload(false);
            }
        }

        string procPath = @"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle";
        if (File.Exists(procPath)) {
            AssetBundle b = AssetBundle.LoadFromFile(procPath);
            if (b != null) {
                foreach (string ap in b.GetAllAssetNames()) {
                    foreach (var sub in b.LoadAssetWithSubAssets(ap)) {
                        if (sub is AnimationClip c && !m_Clips.Contains(c)) {
                            string cl = c.name.ToLower();
                            if (cl.Contains("brawler") || cl.Contains("optimus") || cl.Contains("idle") || cl.Contains("victory") || cl.Contains("heavy")) {
                                m_Clips.Add(c);
                            }
                        }
                    }
                }
                b.Unload(false);
            }
        }

        Debug.Log($"[BrawlPreviewController] Loaded {m_Clips.Count} animation clips.");
    }

    void DestroyGraphs() {
        if (graphMegatron.IsValid()) graphMegatron.Destroy();
        if (graphBrawl.IsValid()) graphBrawl.Destroy();
        if (graphTrMegatron.IsValid()) graphTrMegatron.Destroy();
        if (graphTrBrawl.IsValid()) graphTrBrawl.Destroy();
    }

    public void PlayClip(int idx) {
        if (idx < 0 || idx >= m_Clips.Count) return;
        m_CurrentClipIdx = idx;
        AnimationClip c = m_Clips[idx];
        string cl = c.name.ToLower();
        m_IsVehicle = cl.Contains("transformed") || cl.Contains("vehicle");

        if (smrRobotOfficial != null) smrRobotOfficial.enabled = !m_IsVehicle;
        if (smrVehOfficial != null) { smrVehOfficial.gameObject.SetActive(true); smrVehOfficial.enabled = m_IsVehicle; }
        if (smrRobotBrawl != null) smrRobotBrawl.enabled = !m_IsVehicle;
        if (smrVehBrawl != null) { smrVehBrawl.gameObject.SetActive(true); smrVehBrawl.enabled = m_IsVehicle; }

        DestroyGraphs();
        RestoreRests();

        if (animOfficialMegatron != null) {
            animOfficialMegatron.applyRootMotion = false;
            graphMegatron = PlayableGraph.Create("MegGraph");
            playableMegatron = AnimationClipPlayable.Create(graphMegatron, c);
            playableMegatron.SetApplyFootIK(false);
            var o = AnimationPlayableOutput.Create(graphMegatron, "Anim", animOfficialMegatron);
            o.SetSourcePlayable(playableMegatron);
            graphMegatron.Play();
        }

        if (animBrawl != null) {
            animBrawl.applyRootMotion = false;
            graphBrawl = PlayableGraph.Create("BrawlGraph");
            playableBrawl = AnimationClipPlayable.Create(graphBrawl, c);
            playableBrawl.SetApplyFootIK(false);
            var o = AnimationPlayableOutput.Create(graphBrawl, "Anim", animBrawl);
            o.SetSourcePlayable(playableBrawl);
            graphBrawl.Play();
        }

        if (m_IsVehicle) {
            if (animTrOfficial != null) {
                animTrOfficial.applyRootMotion = false;
                graphTrMegatron = PlayableGraph.Create("TrMegGraph");
                playableTrMegatron = AnimationClipPlayable.Create(graphTrMegatron, c);
                playableTrMegatron.SetApplyFootIK(false);
                var o = AnimationPlayableOutput.Create(graphTrMegatron, "Anim", animTrOfficial);
                o.SetSourcePlayable(playableTrMegatron);
                graphTrMegatron.Play();
            }
            if (animTrBrawl != null) {
                animTrBrawl.applyRootMotion = false;
                graphTrBrawl = PlayableGraph.Create("TrBrawlGraph");
                playableTrBrawl = AnimationClipPlayable.Create(graphTrBrawl, c);
                playableTrBrawl.SetApplyFootIK(false);
                var o = AnimationPlayableOutput.Create(graphTrBrawl, "Anim", animTrBrawl);
                o.SetSourcePlayable(playableTrBrawl);
                graphTrBrawl.Play();
            }
        }

        m_ScrubTime = 0.0f;
    }

    void Update() {
        if (m_Clips.Count == 0) return;
        AnimationClip c = m_Clips[m_CurrentClipIdx];

        if (m_IsPlaying) {
            m_ScrubTime += Time.deltaTime * m_PlaySpeed;
            if (c.length > 0) {
                if (m_ScrubTime > c.length) m_ScrubTime %= c.length;
            }
        }

        if (playableMegatron.IsValid()) playableMegatron.SetTime(m_ScrubTime);
        if (playableBrawl.IsValid()) playableBrawl.SetTime(m_ScrubTime);
        if (playableTrMegatron.IsValid()) playableTrMegatron.SetTime(m_ScrubTime);
        if (playableTrBrawl.IsValid()) playableTrBrawl.SetTime(m_ScrubTime);

        if (graphMegatron.IsValid()) graphMegatron.Evaluate();
        if (graphBrawl.IsValid()) graphBrawl.Evaluate();
        if (graphTrMegatron.IsValid()) graphTrMegatron.Evaluate();
        if (graphTrBrawl.IsValid()) graphTrBrawl.Evaluate();

        HandleCameraOrbit();
    }

    void HandleCameraOrbit() {
        if (Input.GetMouseButton(1)) {
            camYaw += Input.GetAxis("Mouse X") * 3.5f;
            camPitch -= Input.GetAxis("Mouse Y") * 2.5f;
            camPitch = Mathf.Clamp(camPitch, -30f, 60f);
        }
        float scroll = Input.GetAxis("Mouse ScrollWheel");
        if (Mathf.Abs(scroll) > 0.01f) {
            camDist = Mathf.Clamp(camDist - scroll * 5.0f, 4.0f, 35.0f);
        }
        if (Input.GetMouseButton(2)) {
            camPivot.x -= Input.GetAxis("Mouse X") * 0.25f;
            camPivot.y -= Input.GetAxis("Mouse Y") * 0.25f;
        }
        ApplyCameraOrbit();
    }

    void ApplyCameraOrbit() {
        var cam = Camera.main;
        if (cam == null) return;
        Quaternion rot = Quaternion.Euler(camPitch, camYaw, 0f);
        Vector3 dir = rot * Vector3.forward;
        cam.transform.position = camPivot - dir * camDist;
        cam.transform.LookAt(camPivot);
    }

    private Vector2 m_Scroll = Vector2.zero;
    void OnGUI() {
        GUILayout.BeginArea(new Rect(16, 16, 340, Screen.height - 32), GUI.skin.box);
        GUILayout.Label("<b>BRAWL VS MEGATRON INSPECTION</b>", GUILayout.Height(24));
        if (m_Clips.Count > 0) {
            AnimationClip c = m_Clips[m_CurrentClipIdx];
            GUILayout.Label($"Clip: {c.name} ({m_ScrubTime:F2}s / {c.length:F2}s)");
            m_ScrubTime = GUILayout.HorizontalSlider(m_ScrubTime, 0f, c.length > 0 ? c.length : 1f);

            GUILayout.BeginHorizontal();
            if (GUILayout.Button(m_IsPlaying ? "Pause" : "Play")) m_IsPlaying = !m_IsPlaying;
            if (GUILayout.Button("Reset")) m_ScrubTime = 0f;
            GUILayout.EndHorizontal();

            GUILayout.Label($"Speed: {m_PlaySpeed:F1}x");
            m_PlaySpeed = GUILayout.HorizontalSlider(m_PlaySpeed, 0.1f, 2.0f);
        }

        GUILayout.Space(8);
        GUILayout.Label("<b>Available Animation Clips:</b>");
        m_Scroll = GUILayout.BeginScrollView(m_Scroll);
        for (int i = 0; i < m_Clips.Count; i++) {
            if (GUILayout.Button((i == m_CurrentClipIdx ? "> " : "") + m_Clips[i].name)) {
                PlayClip(i);
            }
        }
        GUILayout.EndScrollView();
        GUILayout.EndArea();
    }

    void OnDestroy() {
        DestroyGraphs();
    }

    static Transform FindChildRecursive(Transform parent, string name) {
        if (parent == null) return null;
        if (parent.name == name) return parent;
        for (int i = 0; i < parent.childCount; i++) {
            var found = FindChildRecursive(parent.GetChild(i), name);
            if (found != null) return found;
        }
        return null;
    }
}
