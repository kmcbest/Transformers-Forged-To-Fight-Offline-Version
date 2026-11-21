using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;

public class SideswipePreviewController : MonoBehaviour {
    public Animator animOfficialBarricade;
    public Animator animSideswipe;

    private Animator animTrOfficial;
    private Animator animTrSideswipe;

    private SkinnedMeshRenderer smrRobotOfficial;
    private SkinnedMeshRenderer smrVehOfficial;
    private SkinnedMeshRenderer smrRobotSideswipe;
    private SkinnedMeshRenderer smrVehSideswipe;

    private PlayableGraph graphBarricade;
    private PlayableGraph graphSideswipe;
    private PlayableGraph graphTrBarricade;
    private PlayableGraph graphTrSideswipe;

    private AnimationClipPlayable playableBarricade;
    private AnimationClipPlayable playableSideswipe;
    private AnimationClipPlayable playableTrBarricade;
    private AnimationClipPlayable playableTrSideswipe;

    private readonly List<AnimationClip> m_Clips = new List<AnimationClip>();
    private int m_CurrentClipIdx = 0;
    private bool m_IsVehicle = false;
    private bool m_IsPlaying = true;
    private float m_PlaySpeed = 1.0f;
    private float m_ScrubTime = 0.0f;

    private float camYaw = 180.0f;
    private float camPitch = 6.0f;
    private float camDist = 17.5f;
    private Vector3 camPivot = new Vector3(-2.0f, 5.0f, 0.0f);

    private readonly Dictionary<Transform, Vector3> m_RestPos = new Dictionary<Transform, Vector3>();
    private readonly Dictionary<Transform, Quaternion> m_RestRot = new Dictionary<Transform, Quaternion>();

    void Start() {
        InitReferences();
        LoadAnimations();
        ApplyCameraOrbit();
        if (m_Clips.Count > 0) PlayClip(0);
    }

    void InitReferences() {
        if (animOfficialBarricade == null) {
            var go = GameObject.Find("Barricade_Official_Reference");
            if (go != null) animOfficialBarricade = go.GetComponent<Animator>();
        }
        if (animSideswipe == null) {
            var go = GameObject.Find("Sideswipe_Candidate");
            if (go != null) animSideswipe = go.GetComponent<Animator>();
        }

        if (animOfficialBarricade != null) {
            foreach (var smr in animOfficialBarricade.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
                if (smr.name.Contains("_00")) smrRobotOfficial = smr;
                else if (smr.name.Contains("_01")) smrVehOfficial = smr;
            }
            Transform tr = FindChildRecursive(animOfficialBarricade.transform, "transformed");
            if (tr != null) animTrOfficial = tr.GetComponent<Animator>() ?? tr.gameObject.AddComponent<Animator>();
        }

        if (animSideswipe != null) {
            foreach (var smr in animSideswipe.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
                if (smr.name.Contains("_00")) smrRobotSideswipe = smr;
                else if (smr.name.Contains("_01")) smrVehSideswipe = smr;
            }
            Transform tr = FindChildRecursive(animSideswipe.transform, "transformed");
            if (tr != null) animTrSideswipe = tr.GetComponent<Animator>() ?? tr.gameObject.AddComponent<Animator>();
        }

        SnapshotRests(animOfficialBarricade);
        SnapshotRests(animSideswipe);
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
        var added = new HashSet<string>();
        Action<AnimationClip> add = c => {
            if (c != null && added.Add(c.name)) m_Clips.Add(c);
        };

        if (animOfficialBarricade != null && animOfficialBarricade.runtimeAnimatorController != null) {
            foreach (var c in animOfficialBarricade.runtimeAnimatorController.animationClips) add(c);
        }

        string procPath = @"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle";
        if (File.Exists(procPath)) {
            var ab = AssetBundle.LoadFromFile(procPath);
            if (ab != null) {
                foreach (var obj in ab.LoadAllAssets<AnimationClip>()) {
                    string n = obj.name.ToLower();
                    if (n.Contains("feral") || n.Contains("barricade") || n.Contains("victory") || n.Contains("bonecrusher")) add(obj);
                }
                ab.Unload(false);
            }
        }
        Debug.Log($"[SideswipePreviewController] Loaded {m_Clips.Count} animation clips.");
    }

    void PlayClip(int idx) {
        if (idx < 0 || idx >= m_Clips.Count) return;
        m_CurrentClipIdx = idx;
        var clip = m_Clips[idx];
        m_IsVehicle = clip.name.ToLower().Contains("trans") || clip.name.ToLower().Contains("vehicle");

        DestroyGraphs();
        RestoreRests();

        if (smrRobotOfficial != null) smrRobotOfficial.enabled = !m_IsVehicle;
        if (smrVehOfficial != null) {
            smrVehOfficial.gameObject.SetActive(m_IsVehicle);
            smrVehOfficial.enabled = m_IsVehicle;
        }
        if (smrRobotSideswipe != null) smrRobotSideswipe.enabled = !m_IsVehicle;
        if (smrVehSideswipe != null) {
            smrVehSideswipe.gameObject.SetActive(m_IsVehicle);
            smrVehSideswipe.enabled = m_IsVehicle;
        }

        Animator aOfficial = m_IsVehicle && animTrOfficial != null ? animTrOfficial : animOfficialBarricade;
        Animator aSideswipe = m_IsVehicle && animTrSideswipe != null ? animTrSideswipe : animSideswipe;

        if (aOfficial != null) {
            graphBarricade = PlayableGraph.Create("OfficialBarricadeGraph");
            var outP = AnimationPlayableOutput.Create(graphBarricade, "Out", aOfficial);
            playableBarricade = AnimationClipPlayable.Create(graphBarricade, clip);
            outP.SetSourcePlayable(playableBarricade);
            graphBarricade.Play();
        }

        if (aSideswipe != null) {
            graphSideswipe = PlayableGraph.Create("SideswipeGraph");
            var outP = AnimationPlayableOutput.Create(graphSideswipe, "Out", aSideswipe);
            playableSideswipe = AnimationClipPlayable.Create(graphSideswipe, clip);
            outP.SetSourcePlayable(playableSideswipe);
            graphSideswipe.Play();
        }
    }

    void Update() {
        if (m_Clips.Count == 0) return;
        var clip = m_Clips[m_CurrentClipIdx];
        float dur = Mathf.Max(0.1f, clip.length);

        if (m_IsPlaying) {
            m_ScrubTime = Mathf.Repeat(m_ScrubTime + Time.deltaTime * m_PlaySpeed, dur);
            if (playableBarricade.IsValid()) playableBarricade.SetTime(m_ScrubTime);
            if (playableSideswipe.IsValid()) playableSideswipe.SetTime(m_ScrubTime);
        }

        HandleMouseOrbit();
    }

    void HandleMouseOrbit() {
        if (Input.GetMouseButton(1)) {
            camYaw += Input.GetAxis("Mouse X") * 4.0f;
            camPitch -= Input.GetAxis("Mouse Y") * 3.0f;
            camPitch = Mathf.Clamp(camPitch, -30f, 75f);
            ApplyCameraOrbit();
        }
        float scroll = Input.GetAxis("Mouse ScrollWheel");
        if (Mathf.Abs(scroll) > 0.01f) {
            camDist = Mathf.Clamp(camDist - scroll * 5.0f, 3.0f, 40.0f);
            ApplyCameraOrbit();
        }
    }

    void ApplyCameraOrbit() {
        var cam = Camera.main;
        if (cam == null) return;
        Quaternion rot = Quaternion.Euler(camPitch, camYaw, 0f);
        cam.transform.position = camPivot + rot * new Vector3(0f, 0f, -camDist);
        cam.transform.LookAt(camPivot);
    }

    void OnGUI() {
        GUILayout.BeginArea(new Rect(10, 10, 360, Screen.height - 20), GUI.skin.box);
        GUILayout.Label("<b>Sideswipe vs Barricade Side-by-Side</b>", GUILayout.Height(24));
        GUILayout.Label($"Mode: {(m_IsVehicle ? "Vehicle" : "Robot")} | Time: {m_ScrubTime:F2}s");

        GUILayout.BeginHorizontal();
        if (GUILayout.Button(m_IsPlaying ? "Pause" : "Play", GUILayout.Width(70))) m_IsPlaying = !m_IsPlaying;
        if (GUILayout.Button("Prev", GUILayout.Width(50))) { int p = (m_CurrentClipIdx - 1 + m_Clips.Count) % m_Clips.Count; PlayClip(p); }
        if (GUILayout.Button("Next", GUILayout.Width(50))) { int n = (m_CurrentClipIdx + 1) % m_Clips.Count; PlayClip(n); }
        GUILayout.EndHorizontal();

        if (m_Clips.Count > 0) {
            float dur = Mathf.Max(0.1f, m_Clips[m_CurrentClipIdx].length);
            float newT = GUILayout.HorizontalSlider(m_ScrubTime, 0f, dur);
            if (Mathf.Abs(newT - m_ScrubTime) > 0.001f) {
                m_ScrubTime = newT;
                m_IsPlaying = false;
                if (playableBarricade.IsValid()) playableBarricade.SetTime(m_ScrubTime);
                if (playableSideswipe.IsValid()) playableSideswipe.SetTime(m_ScrubTime);
            }
        }

        GUILayout.Space(6);
        GUILayout.Label("<b>Clips:</b>");
        for (int i = 0; i < m_Clips.Count; i++) {
            var c = m_Clips[i];
            bool active = (i == m_CurrentClipIdx);
            if (GUILayout.Toggle(active, c.name)) {
                if (!active) PlayClip(i);
            }
        }

        GUILayout.EndArea();
    }

    void DestroyGraphs() {
        if (graphBarricade.IsValid()) graphBarricade.Destroy();
        if (graphSideswipe.IsValid()) graphSideswipe.Destroy();
        if (graphTrBarricade.IsValid()) graphTrBarricade.Destroy();
        if (graphTrSideswipe.IsValid()) graphTrSideswipe.Destroy();
    }

    void OnDestroy() {
        DestroyGraphs();
    }

    static Transform FindChildRecursive(Transform parent, string name) {
        if (parent == null) return null;
        if (parent.name == name) return parent;
        for (int i = 0; i < parent.childCount; i++) {
            var f = FindChildRecursive(parent.GetChild(i), name);
            if (f != null) return f;
        }
        return null;
    }
}
