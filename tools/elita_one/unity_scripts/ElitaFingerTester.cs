using System;
using System.Collections.Generic;
using UnityEngine;

[ExecuteAlways]
public class ElitaFingerTester : MonoBehaviour {
    [Header("Auto Motion (Real-time waving)")]
    public bool autoWiggle = false;
    [Range(0.5f, 10f)] public float wiggleSpeed = 2.5f;
    [Range(10f, 90f)] public float wiggleRange = 45f;

    [Header("Manual Curl Controls (-90 to +90 degrees)")]
    [Range(-90f, 90f)] public float curlAll = 0f;
    [Range(-90f, 90f)] public float curlThumb = 0f;
    [Range(-90f, 90f)] public float curlIndex = 0f;
    [Range(-90f, 90f)] public float curlMiddle = 0f;
    [Range(-90f, 90f)] public float curlRing = 0f;
    [Range(-90f, 90f)] public float curlPinky = 0f;

    public enum CurlAxis {
        Forward_Z,
        Back_NegZ,
        Right_X,
        Left_NegX,
        Up_Y,
        Down_NegY
    }

    [Header("Rotation Axis")]
    public CurlAxis leftHandAxis = CurlAxis.Forward_Z;
    public CurlAxis rightHandAxis = CurlAxis.Forward_Z;

    [Header("Diagnostics")]
    public int leftFingerBonesFound = 0;
    public int rightFingerBonesFound = 0;

    private readonly Dictionary<Transform, Quaternion> restRotations = new Dictionary<Transform, Quaternion>();
    private readonly List<Transform> leftThumbBones = new List<Transform>();
    private readonly List<Transform> leftIndexBones = new List<Transform>();
    private readonly List<Transform> leftMiddleBones = new List<Transform>();
    private readonly List<Transform> leftRingBones = new List<Transform>();
    private readonly List<Transform> leftPinkyBones = new List<Transform>();

    private readonly List<Transform> rightThumbBones = new List<Transform>();
    private readonly List<Transform> rightIndexBones = new List<Transform>();
    private readonly List<Transform> rightMiddleBones = new List<Transform>();
    private readonly List<Transform> rightRingBones = new List<Transform>();
    private readonly List<Transform> rightPinkyBones = new List<Transform>();

    private bool initialized = false;

    void OnEnable() {
        InitializeBones();
    }

    void Start() {
        InitializeBones();
    }

    public void InitializeBones() {
        restRotations.Clear();
        leftThumbBones.Clear();
        leftIndexBones.Clear();
        leftMiddleBones.Clear();
        leftRingBones.Clear();
        leftPinkyBones.Clear();

        rightThumbBones.Clear();
        rightIndexBones.Clear();
        rightMiddleBones.Clear();
        rightRingBones.Clear();
        rightPinkyBones.Clear();

        // Search recursively under this object for LeftHand and RightHand finger bones
        Transform[] allTransforms = GetComponentsInChildren<Transform>(true);
        foreach (var t in allTransforms) {
            string n = t.name;
            if (n.StartsWith("LeftHandThumb")) { leftThumbBones.Add(t); RecordRest(t); }
            else if (n.StartsWith("LeftHandIndex")) { leftIndexBones.Add(t); RecordRest(t); }
            else if (n.StartsWith("LeftHandMiddle")) { leftMiddleBones.Add(t); RecordRest(t); }
            else if (n.StartsWith("LeftHandRing")) { leftRingBones.Add(t); RecordRest(t); }
            else if (n.StartsWith("LeftHandPinky")) { leftPinkyBones.Add(t); RecordRest(t); }
            else if (n.StartsWith("RightHandThumb")) { rightThumbBones.Add(t); RecordRest(t); }
            else if (n.StartsWith("RightHandIndex")) { rightIndexBones.Add(t); RecordRest(t); }
            else if (n.StartsWith("RightHandMiddle")) { rightMiddleBones.Add(t); RecordRest(t); }
            else if (n.StartsWith("RightHandRing")) { rightRingBones.Add(t); RecordRest(t); }
            else if (n.StartsWith("RightHandPinky")) { rightPinkyBones.Add(t); RecordRest(t); }
        }

        leftFingerBonesFound = leftThumbBones.Count + leftIndexBones.Count + leftMiddleBones.Count + leftRingBones.Count + leftPinkyBones.Count;
        rightFingerBonesFound = rightThumbBones.Count + rightIndexBones.Count + rightMiddleBones.Count + rightRingBones.Count + rightPinkyBones.Count;

        Debug.Log($"[ElitaFingerTester] Initialized: Found {leftFingerBonesFound} Left Finger Bones and {rightFingerBonesFound} Right Finger Bones.");
        initialized = true;
    }

    void RecordRest(Transform t) {
        if (!restRotations.ContainsKey(t)) {
            restRotations[t] = t.localRotation;
        }
    }

    Vector3 GetAxisVector(CurlAxis axis) {
        switch (axis) {
            case CurlAxis.Forward_Z: return Vector3.forward;
            case CurlAxis.Back_NegZ: return Vector3.back;
            case CurlAxis.Right_X: return Vector3.right;
            case CurlAxis.Left_NegX: return Vector3.left;
            case CurlAxis.Up_Y: return Vector3.up;
            case CurlAxis.Down_NegY: return Vector3.down;
            default: return Vector3.forward;
        }
    }

    void LateUpdate() {
        if (!initialized || restRotations.Count == 0) {
            InitializeBones();
            if (restRotations.Count == 0) return;
        }

        float effectiveCurlAll = curlAll;
        float effectiveThumb = curlThumb;
        float effectiveIndex = curlIndex;
        float effectiveMiddle = curlMiddle;
        float effectiveRing = curlRing;
        float effectivePinky = curlPinky;

        if (autoWiggle) {
            float wave = Mathf.Sin(Time.time * wiggleSpeed) * wiggleRange;
            effectiveCurlAll += wave;
            effectiveThumb += wave * 0.8f;
            effectiveIndex += wave;
            effectiveMiddle += wave * 1.1f;
            effectiveRing += wave;
            effectivePinky += wave * 0.9f;
        }

        Vector3 lAxis = GetAxisVector(leftHandAxis);
        Vector3 rAxis = GetAxisVector(rightHandAxis);

        // Apply Left Hand rotations
        ApplyRotation(leftThumbBones, lAxis, effectiveThumb + effectiveCurlAll);
        ApplyRotation(leftIndexBones, lAxis, effectiveIndex + effectiveCurlAll);
        ApplyRotation(leftMiddleBones, lAxis, effectiveMiddle + effectiveCurlAll);
        ApplyRotation(leftRingBones, lAxis, effectiveRing + effectiveCurlAll);
        ApplyRotation(leftPinkyBones, lAxis, effectivePinky + effectiveCurlAll);

        // Apply Right Hand rotations
        ApplyRotation(rightThumbBones, rAxis, effectiveThumb + effectiveCurlAll);
        ApplyRotation(rightIndexBones, rAxis, effectiveIndex + effectiveCurlAll);
        ApplyRotation(rightMiddleBones, rAxis, effectiveMiddle + effectiveCurlAll);
        ApplyRotation(rightRingBones, rAxis, effectiveRing + effectiveCurlAll);
        ApplyRotation(rightPinkyBones, rAxis, effectivePinky + effectiveCurlAll);
    }

    void ApplyRotation(List<Transform> bones, Vector3 axis, float angle) {
        foreach (var b in bones) {
            if (b == null) continue;
            if (restRotations.TryGetValue(b, out Quaternion rest)) {
                b.localRotation = rest * Quaternion.AngleAxis(angle, axis);
            }
        }
    }

    public void ResetAll() {
        curlAll = 0f;
        curlThumb = 0f;
        curlIndex = 0f;
        curlMiddle = 0f;
        curlRing = 0f;
        curlPinky = 0f;
        autoWiggle = false;

        foreach (var kvp in restRotations) {
            if (kvp.Key != null) {
                kvp.Key.localRotation = kvp.Value;
            }
        }
    }

    private Rect windowRect = new Rect(0, 0, 0, 0);

    void OnGUI() {
        if (windowRect.width == 0) {
            windowRect = new Rect(Screen.width - 340, 20, 320, 520);
        }
        windowRect = GUI.Window(9912, windowRect, DrawTesterWindow, "Elita 手指骨骼活动测试器 (可拖拽)");
    }

    void DrawTesterWindow(int id) {
        GUILayout.Label($"左手手指骨骼: {leftFingerBonesFound} 根");
        GUILayout.Label($"右手手指骨骼: {rightFingerBonesFound} 根");

        GUILayout.Space(6);
        bool newAuto = GUILayout.Toggle(autoWiggle, " 自动挥动/活动手指 (Auto Wiggle)");
        if (newAuto != autoWiggle) autoWiggle = newAuto;

        if (autoWiggle) {
            GUILayout.Label($"挥动速度: {wiggleSpeed:F1}");
            wiggleSpeed = GUILayout.HorizontalSlider(wiggleSpeed, 0.5f, 8f);
            GUILayout.Label($"挥动角度幅度: {wiggleRange:F0}°");
            wiggleRange = GUILayout.HorizontalSlider(wiggleRange, 10f, 90f);
        }

        GUILayout.Space(8);
        GUILayout.Label($"全手指整体屈伸 (Curl All): {curlAll:F0}°");
        curlAll = GUILayout.HorizontalSlider(curlAll, -90f, 90f);

        GUILayout.Space(4);
        GUILayout.Label($"拇指 (Thumb): {curlThumb:F0}°");
        curlThumb = GUILayout.HorizontalSlider(curlThumb, -90f, 90f);

        GUILayout.Label($"食指 (Index): {curlIndex:F0}°");
        curlIndex = GUILayout.HorizontalSlider(curlIndex, -90f, 90f);

        GUILayout.Label($"中指 (Middle): {curlMiddle:F0}°");
        curlMiddle = GUILayout.HorizontalSlider(curlMiddle, -90f, 90f);

        GUILayout.Label($"无名指 (Ring): {curlRing:F0}°");
        curlRing = GUILayout.HorizontalSlider(curlRing, -90f, 90f);

        GUILayout.Label($"小指 (Pinky): {curlPinky:F0}°");
        curlPinky = GUILayout.HorizontalSlider(curlPinky, -90f, 90f);

        GUILayout.Space(10);
        if (GUILayout.Button("一键诊断 BindPose 偏差 (Diagnose Bindposes)")) {
            DiagnoseBindposes();
        }

        if (GUILayout.Button("重置全部手指姿态 (Reset)")) {
            ResetAll();
        }

#if UNITY_EDITOR
        GUILayout.Space(8);
        GUI.backgroundColor = new Color(0.2f, 1.0f, 0.4f);
        if (GUILayout.Button("★ 一键重构灵动指节 (1:1 对齐真实指骨)", GUILayout.Height(36))) {
            var fixerType = System.Type.GetType("ElitaHandFixer, Assembly-CSharp-Editor");
            if (fixerType != null) {
                var method = fixerType.GetMethod("RebuildFlexibleFingers", System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Static);
                if (method != null) {
                    method.Invoke(null, null);
                }
            }
        }
        GUI.backgroundColor = Color.white;
#endif

        GUI.DragWindow(new Rect(0, 0, 10000, 25));
    }

    public void DiagnoseBindposes() {
        var smr = GetComponentInChildren<SkinnedMeshRenderer>();
        if (smr == null || smr.sharedMesh == null) {
            Debug.LogError("[Diagnose] No SkinnedMeshRenderer found on Elita!");
            return;
        }

        Transform[] bones = smr.bones;
        Matrix4x4[] bindposes = smr.sharedMesh.bindposes;
        Debug.Log($"=== [Diagnose] Inspecting SMR '{smr.name}' with {bones.Length} bones and {bindposes.Length} bindposes ===");

        int mismatchCount = 0;
        for (int i = 0; i < bones.Length; i++) {
            if (i >= bindposes.Length) break;
            Transform b = bones[i];
            if (b == null) continue;

            string n = b.name;
            if (anyFinger(n)) {
                Matrix4x4 bindWorld = smr.transform.localToWorldMatrix * bindposes[i].inverse;
                Vector3 bindPos = bindWorld.MultiplyPoint3x4(Vector3.zero);
                Vector3 currentPos = b.position;
                float delta = Vector3.Distance(currentPos, bindPos);

                if (delta > 0.05f) { // Greater than 5cm offset
                    mismatchCount++;
                    Debug.LogWarning($"[OFFSET MISMATCH] Bone [{i}] '{n}': Current Pos={currentPos:F3}, BindPose Pos={bindPos:F3}, DELTA={delta:F3}m!");
                } else {
                    Debug.Log($"[OK] Bone [{i}] '{n}': Delta={delta*1000f:F1}mm (Perfect match)");
                }
            }
        }
        Debug.Log($"=== [Diagnose Done] Finger bone mismatches (>5cm): {mismatchCount} ===");
    }

    bool anyFinger(string name) {
        string l = name.ToLower();
        return l.Contains("thumb") || l.Contains("index") || l.Contains("middle") || l.Contains("ring") || l.Contains("pinky");
    }
}

#if UNITY_EDITOR
public static class ElitaFingerTesterMenu {
    [UnityEditor.MenuItem("TFTF/Run Finger Diagnosis", false, 9)]
    public static void RunDiagnosis() {
        var go = GameObject.Find("ElitaOne_Candidate");
        if (go != null) {
            var comp = go.GetComponent<ElitaFingerTester>();
            if (comp != null) comp.DiagnoseBindposes();
        }
    }

    [UnityEditor.MenuItem("TFTF/Attach Finger Tester to Elita", false, 10)]
    public static void Attach() {
        var go = GameObject.Find("ElitaOne_Candidate");
        if (go != null) {
            // Remove missing / corrupted script placeholders to clean up Inspector
            int removed = UnityEditor.GameObjectUtility.RemoveMonoBehavioursWithMissingScript(go);
            if (removed > 0) {
                Debug.Log($"[✓] Cleaned up {removed} missing script placeholders on ElitaOne_Candidate.");
            }

            var comp = go.GetComponent<ElitaFingerTester>();
            if (comp == null) {
                comp = go.AddComponent<ElitaFingerTester>();
            }
            comp.autoWiggle = true; // Auto start wiggling by default for immediate visual feedback!
            comp.InitializeBones();
            comp.DiagnoseBindposes();
            UnityEditor.EditorUtility.SetDirty(go);
            UnityEditor.Selection.activeGameObject = go;
            Debug.Log("[✓] Added ElitaFingerTester to ElitaOne_Candidate with Auto Wiggle enabled!");
        } else {
            Debug.LogError("Could not find 'ElitaOne_Candidate' in current scene!");
        }
    }
}
#endif

