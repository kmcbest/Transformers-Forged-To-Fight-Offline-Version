using System.Collections.Generic;
using UnityEngine;

[ExecuteAlways]
public class TarnFingerTester : MonoBehaviour {
    [Header("Auto Motion (Real-time waving)")]
    public bool autoWiggle = false;
    [Range(0.5f, 10f)] public float wiggleSpeed = 2.5f;
    [Range(10f, 80f)] public float wiggleRange = 50f;

    [Header("Manual Curl Controls (-45 to +85 degrees)")]
    [Range(-45f, 85f)] public float curlAll = 0f;
    [Range(-45f, 85f)] public float curlThumb = 0f;
    [Range(-45f, 85f)] public float curlIndex = 0f;
    [Range(-45f, 85f)] public float curlMiddle = 0f;
    [Range(-45f, 85f)] public float curlRing = 0f;
    [Range(-45f, 85f)] public float curlPinky = 0f;

    public enum CurlAxis {
        Forward_Z,
        Back_NegZ,
        Right_X,
        Left_NegX,
        Up_Y,
        Down_NegY
    }

    [Header("Rotation Axis (UM Left=+Z, Right=-Z)")]
    public CurlAxis leftHandAxis = CurlAxis.Forward_Z;
    public CurlAxis rightHandAxis = CurlAxis.Back_NegZ;

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
    private bool wasManualOverrideActive = false;
    private Vector2 scrollPos = Vector2.zero;
    private Rect windowRect = new Rect(0, 0, 0, 0);

    void OnEnable() { InitializeBones(); }
    void Start() { InitializeBones(); }

    public void InitializeBones() {
        restRotations.Clear();
        leftThumbBones.Clear(); leftIndexBones.Clear(); leftMiddleBones.Clear(); leftRingBones.Clear(); leftPinkyBones.Clear();
        rightThumbBones.Clear(); rightIndexBones.Clear(); rightMiddleBones.Clear(); rightRingBones.Clear(); rightPinkyBones.Clear();

        foreach (var t in GetComponentsInChildren<Transform>(true)) {
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
        initialized = true;
    }

    public void CaptureCurrentAsRest() {
        restRotations.Clear();
        foreach (var list in new[] { leftThumbBones, leftIndexBones, leftMiddleBones, leftRingBones, leftPinkyBones,
                                     rightThumbBones, rightIndexBones, rightMiddleBones, rightRingBones, rightPinkyBones }) {
            foreach (var b in list) {
                if (b != null) restRotations[b] = b.localRotation;
            }
        }
    }

    void RecordRest(Transform t) {
        if (!restRotations.ContainsKey(t)) restRotations[t] = t.localRotation;
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

    bool HasManualOverride() {
        return autoWiggle
            || Mathf.Abs(curlAll) > 0.01f
            || Mathf.Abs(curlThumb) > 0.01f
            || Mathf.Abs(curlIndex) > 0.01f
            || Mathf.Abs(curlMiddle) > 0.01f
            || Mathf.Abs(curlRing) > 0.01f
            || Mathf.Abs(curlPinky) > 0.01f;
    }

    public void EvaluatePoseNow() { LateUpdate(); }

    void LateUpdate() {
        if (!initialized || restRotations.Count == 0) {
            InitializeBones();
            if (restRotations.Count == 0) return;
        }

        bool manualActive = HasManualOverride();
        if (!manualActive) {
            if (!Application.isPlaying && wasManualOverrideActive) RestoreRestRotations();
            wasManualOverrideActive = false;
            return;
        }

        wasManualOverrideActive = true;
        float eAll = curlAll;
        float eThumb = curlThumb + eAll * 0.55f;
        float eIndex = curlIndex + eAll;
        float eMiddle = curlMiddle + eAll;
        float eRing = curlRing + eAll;
        float ePinky = curlPinky + eAll;

        if (autoWiggle) {
            float t = Application.isPlaying ? Time.time : Time.realtimeSinceStartup;
            float wave = (0.5f + 0.5f * Mathf.Sin(t * wiggleSpeed)) * wiggleRange;
            eThumb += wave * 0.55f;
            eIndex += wave;
            eMiddle += wave * 1.03f;
            eRing += wave;
            ePinky += wave * 0.96f;
        }

        Vector3 lAxis = GetAxisVector(leftHandAxis);
        Vector3 rAxis = GetAxisVector(rightHandAxis);

        ApplyRotation(leftThumbBones, lAxis, eThumb);
        ApplyRotation(leftIndexBones, lAxis, eIndex);
        ApplyRotation(leftMiddleBones, lAxis, eMiddle);
        ApplyRotation(leftRingBones, lAxis, eRing);
        ApplyRotation(leftPinkyBones, lAxis, ePinky);

        ApplyRotation(rightThumbBones, rAxis, eThumb);
        ApplyRotation(rightIndexBones, rAxis, eIndex);
        ApplyRotation(rightMiddleBones, rAxis, eMiddle);
        ApplyRotation(rightRingBones, rAxis, eRing);
        ApplyRotation(rightPinkyBones, rAxis, ePinky);
    }

    void ApplyRotation(List<Transform> bones, Vector3 axis, float angle) {
        foreach (var b in bones) {
            if (b != null && restRotations.TryGetValue(b, out Quaternion rest)) {
                b.localRotation = rest * Quaternion.AngleAxis(angle, axis);
            }
        }
    }

    void RestoreRestRotations() {
        foreach (var kvp in restRotations) {
            if (kvp.Key != null) kvp.Key.localRotation = kvp.Value;
        }
    }

    public void ResetAll() {
        curlAll = curlThumb = curlIndex = curlMiddle = curlRing = curlPinky = 0f;
        autoWiggle = false;
        RestoreRestRotations();
        wasManualOverrideActive = false;
    }

    void OnGUI() {
        float maxH = Mathf.Max(200f, Screen.height - 20f);
        float targetH = Mathf.Min(460f, maxH);
        if (windowRect.width == 0) windowRect = new Rect(Mathf.Max(10f, Screen.width - 356f), 16f, 340f, targetH);
        else {
            windowRect.width = 340f;
            windowRect.height = targetH;
            windowRect.x = Mathf.Clamp(windowRect.x, 0f, Mathf.Max(0f, Screen.width - windowRect.width));
            windowRect.y = Mathf.Clamp(windowRect.y, 0f, Mathf.Max(0f, Screen.height - windowRect.height));
        }
        windowRect = GUI.Window(9941, windowRect, DrawTesterWindow, "塔恩 (Tarn) 30指骨骼活动测试器");
    }

    void DrawTesterWindow(int id) {
        scrollPos = GUILayout.BeginScrollView(scrollPos);
        if (GUILayout.Button("重置手指姿态 (Reset)", GUILayout.Height(24))) ResetAll();
        GUILayout.Label($"手指骨骼: 左手 {leftFingerBonesFound} 根 | 右手 {rightFingerBonesFound} 根");
        autoWiggle = GUILayout.Toggle(autoWiggle, " 自动握拳/活动手指 (Auto Wiggle)");
        if (autoWiggle) {
            GUILayout.Label($"挥动速度: {wiggleSpeed:F1}");
            wiggleSpeed = GUILayout.HorizontalSlider(wiggleSpeed, 0.5f, 8f);
            GUILayout.Label($"握拳角度幅度: {wiggleRange:F0}°");
            wiggleRange = GUILayout.HorizontalSlider(wiggleRange, 10f, 80f);
        }
        GUILayout.Label($"全手指整体屈伸 (Curl All): {curlAll:F0}°");
        curlAll = GUILayout.HorizontalSlider(curlAll, -30f, 80f);
        GUILayout.Label($"拇指 (Thumb): {curlThumb:F0}°");
        curlThumb = GUILayout.HorizontalSlider(curlThumb, -45f, 80f);
        GUILayout.Label($"食指 (Index): {curlIndex:F0}°");
        curlIndex = GUILayout.HorizontalSlider(curlIndex, -30f, 80f);
        GUILayout.Label($"中指 (Middle): {curlMiddle:F0}°");
        curlMiddle = GUILayout.HorizontalSlider(curlMiddle, -30f, 80f);
        GUILayout.Label($"无名指 (Ring): {curlRing:F0}°");
        curlRing = GUILayout.HorizontalSlider(curlRing, -30f, 80f);
        GUILayout.Label($"小指 (Pinky): {curlPinky:F0}°");
        curlPinky = GUILayout.HorizontalSlider(curlPinky, -30f, 80f);
        GUILayout.EndScrollView();
        GUI.DragWindow(new Rect(0, 0, 10000, 22));
    }
}
