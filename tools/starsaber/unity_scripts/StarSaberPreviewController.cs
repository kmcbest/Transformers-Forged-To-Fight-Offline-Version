using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;

public class StarSaberPreviewController : MonoBehaviour {
    public Animator animOfficialJetfire;
    public Animator animStarSaber;

    private Animator animTrOfficial;
    private Animator animTrStarSaber;

    private SkinnedMeshRenderer smrRobotOfficial;
    private SkinnedMeshRenderer smrVehOfficial;
    private SkinnedMeshRenderer smrRobotStarSaber;
    private SkinnedMeshRenderer smrVehStarSaber;

    private PlayableGraph graphJetfire;
    private PlayableGraph graphStarSaber;
    private PlayableGraph graphTrJetfire;
    private PlayableGraph graphTrStarSaber;

    private AnimationClipPlayable playableJetfire;
    private AnimationClipPlayable playableStarSaber;
    private AnimationClipPlayable playableTrJetfire;
    private AnimationClipPlayable playableTrStarSaber;

    private readonly List<AnimationClip> m_Clips = new List<AnimationClip>();
    private int m_CurrentClipIdx = 0;
    private bool m_IsVehicle = false;
    private bool m_IsPlaying = true;
    private float m_PlaySpeed = 1.0f;
    private float m_ScrubTime = 0.0f;

    private float camYaw = 180.0f;
    private float camPitch = 6.0f;
    private float camDist = 18.0f;
    private Vector3 camPivot = new Vector3(0.0f, 5.5f, 0.0f);

    private readonly Dictionary<Transform, Vector3> m_RestPos = new Dictionary<Transform, Vector3>();
    private readonly Dictionary<Transform, Quaternion> m_RestRot = new Dictionary<Transform, Quaternion>();

    void Start() {
        InitReferences();
        LoadAnimations();
        ApplyCameraOrbit();
        if (m_Clips.Count > 0) PlayClip(0);
    }

    void InitReferences() {
        if (animOfficialJetfire == null) {
            var go = GameObject.Find("Jetfire_Official_Reference");
            if (go != null) animOfficialJetfire = go.GetComponent<Animator>();
        }
        if (animStarSaber == null) {
            var go = GameObject.Find("StarSaber_Candidate");
            if (go != null) animStarSaber = go.GetComponent<Animator>();
        }

        if (animOfficialJetfire != null) {
            foreach (var smr in animOfficialJetfire.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
                if (smr.name.Contains("_00")) smrRobotOfficial = smr;
                else if (smr.name.Contains("_01")) smrVehOfficial = smr;
            }
            Transform tr = FindChildRecursive(animOfficialJetfire.transform, "transformed");
            if (tr != null) animTrOfficial = tr.GetComponent<Animator>() ?? tr.gameObject.AddComponent<Animator>();
        }

        if (animStarSaber != null) {
            foreach (var smr in animStarSaber.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
                if (smr.name.Contains("_00")) smrRobotStarSaber = smr;
                else if (smr.name.Contains("_01")) smrVehStarSaber = smr;
            }
            Transform tr = FindChildRecursive(animStarSaber.transform, "transformed");
            if (tr != null) animTrStarSaber = tr.GetComponent<Animator>() ?? tr.gameObject.AddComponent<Animator>();
        }

        SnapshotRests(animOfficialJetfire);
        SnapshotRests(animStarSaber);
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
        string procPath = @"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle";
        if (File.Exists(procPath)) {
            var ab = AssetBundle.LoadFromFile(procPath);
            if (ab != null) {
                var allClips = ab.LoadAllAssets<AnimationClip>();
                foreach (var c in allClips) {
                    if (c == null) continue;
                    string n = c.name.ToLower();
                    if (n.Contains("idle") || n.Contains("attack") || n.Contains("hit") || n.Contains("special") || n.Contains("victory") || n.Contains("teamselect")) {
                        m_Clips.Add(c);
                    }
                }
                ab.Unload(false);
            }
        }
        Debug.Log("[StarSaberPreview] Loaded " + m_Clips.Count + " animation clips.");
    }

    public void PlayClip(int idx) {
        if (idx < 0 || idx >= m_Clips.Count) return;
        m_CurrentClipIdx = idx;
        var clip = m_Clips[idx];
        m_ScrubTime = 0.0f;
        SetupPlayableGraphs(clip);
    }

    void SetupPlayableGraphs(AnimationClip clip) {
        DestroyGraphs();
        RestoreRests();

        if (animOfficialJetfire != null) {
            graphJetfire = PlayableGraph.Create("Jetfire_Graph");
            playableJetfire = AnimationClipPlayable.Create(graphJetfire, clip);
            var output = AnimationPlayableOutput.Create(graphJetfire, "Jetfire_Output", animOfficialJetfire);
            output.SetSourcePlayable(playableJetfire);
            graphJetfire.Play();
        }

        if (animStarSaber != null) {
            graphStarSaber = PlayableGraph.Create("StarSaber_Graph");
            playableStarSaber = AnimationClipPlayable.Create(graphStarSaber, clip);
            var output = AnimationPlayableOutput.Create(graphStarSaber, "StarSaber_Output", animStarSaber);
            output.SetSourcePlayable(playableStarSaber);
            graphStarSaber.Play();
        }
    }

    void DestroyGraphs() {
        if (graphJetfire.IsValid()) graphJetfire.Destroy();
        if (graphStarSaber.IsValid()) graphStarSaber.Destroy();
        if (graphTrJetfire.IsValid()) graphTrJetfire.Destroy();
        if (graphTrStarSaber.IsValid()) graphTrStarSaber.Destroy();
    }

    void OnDestroy() {
        DestroyGraphs();
    }

    void Update() {
        HandleInput();
        if (m_IsPlaying && m_Clips.Count > 0) {
            var clip = m_Clips[m_CurrentClipIdx];
            m_ScrubTime += Time.deltaTime * m_PlaySpeed;
            if (m_ScrubTime > clip.length) m_ScrubTime = m_ScrubTime % clip.length;
            if (graphJetfire.IsValid()) playableJetfire.SetTime(m_ScrubTime);
            if (graphStarSaber.IsValid()) playableStarSaber.SetTime(m_ScrubTime);
        }
    }

    void HandleInput() {
        if (Input.GetKeyDown(KeyCode.Space)) m_IsPlaying = !m_IsPlaying;
        if (Input.GetKeyDown(KeyCode.RightArrow) && m_Clips.Count > 0) PlayClip((m_CurrentClipIdx + 1) % m_Clips.Count);
        if (Input.GetKeyDown(KeyCode.LeftArrow) && m_Clips.Count > 0) PlayClip((m_CurrentClipIdx - 1 + m_Clips.Count) % m_Clips.Count);

        if (Input.GetMouseButton(1)) {
            camYaw += Input.GetAxis("Mouse X") * 4.0f;
            camPitch -= Input.GetAxis("Mouse Y") * 3.0f;
            camPitch = Mathf.Clamp(camPitch, -30.0f, 80.0f);
            ApplyCameraOrbit();
        }

        float scroll = Input.GetAxis("Mouse ScrollWheel");
        if (Mathf.Abs(scroll) > 0.01f) {
            camDist = Mathf.Clamp(camDist - scroll * 5.0f, 3.0f, 40.0f);
            ApplyCameraOrbit();
        }
    }

    void ApplyCameraOrbit() {
        Camera cam = Camera.main;
        if (cam == null) return;
        Quaternion rot = Quaternion.Euler(camPitch, camYaw, 0.0f);
        cam.transform.position = camPivot + rot * new Vector3(0, 0, -camDist);
        cam.transform.LookAt(camPivot);
    }

    Transform FindChildRecursive(Transform parent, string name) {
        foreach (Transform child in parent) {
            if (child.name.ToLower().Contains(name.ToLower())) return child;
            var res = FindChildRecursive(child, name);
            if (res != null) return res;
        }
        return null;
    }
}
