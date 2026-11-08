using System;
using System.Collections.Generic;
using UnityEngine;

[ExecuteAlways]
public class VortexFingerTester : MonoBehaviour {
    [Header("Auto Motion (Real-time waving)")]
    public bool autoWiggle = false;
    [Range(0.5f, 10f)] public float wiggleSpeed = 2.5f;
    [Range(10f, 80f)] public float wiggleRange = 45f;

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

    [Header("Rotation Axis (Maya Left=+Z, Right=-Z)")]
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

        initialized = true;
    }

    void RecordRest(Transform t) {
        if (!restRotations.ContainsKey(t)) {
            restRotations[t] = t.localRotation;
        }
    }

    public void ResetToRest() {
        foreach (var kvp in restRotations) {
            if (kvp.Key != null) {
                kvp.Key.localRotation = kvp.Value;
            }
        }
        curlAll = 0f;
        curlThumb = 0f;
        curlIndex = 0f;
        curlMiddle = 0f;
        curlRing = 0f;
        curlPinky = 0f;
        autoWiggle = false;
        wasManualOverrideActive = false;
    }

    public void DiagnoseBindposes() {
        SkinnedMeshRenderer smr = GetComponentInChildren<SkinnedMeshRenderer>(true);
        if (smr == null || smr.sharedMesh == null) {
            Debug.LogWarning("[VortexFingerTester] No SkinnedMeshRenderer found for diagnosis.");
            return;
        }
        Matrix4x4[] bps = smr.sharedMesh.bindposes;
        Transform[] bones = smr.bones;
        Debug.Log($"[VortexFingerTester Diagnosis] Mesh={smr.sharedMesh.name}, Verts={smr.sharedMesh.vertexCount}, BindPoses={bps.Length}, Bones={bones.Length}");
        
        int missingBones = 0;
        for (int i = 0; i < bones.Length; i++) {
            if (bones[i] == null) {
                missingBones++;
            }
        }
        Debug.Log($"[VortexFingerTester] LeftFingerBones={leftFingerBonesFound}/15, RightFingerBones={rightFingerBonesFound}/15, NullBones={missingBones}");
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
        if (!initialized) InitializeBones();

        bool hasManualInput = Mathf.Abs(curlAll) > 0.01f ||
                              Mathf.Abs(curlThumb) > 0.01f ||
                              Mathf.Abs(curlIndex) > 0.01f ||
                              Mathf.Abs(curlMiddle) > 0.01f ||
                              Mathf.Abs(curlRing) > 0.01f ||
                              Mathf.Abs(curlPinky) > 0.01f;

        if (!autoWiggle && !hasManualInput) {
            if (wasManualOverrideActive) {
                ResetToRest();
            }
            return;
        }

        wasManualOverrideActive = true;

        float effectiveThumb = curlAll + curlThumb;
        float effectiveIndex = curlAll + curlIndex;
        float effectiveMiddle = curlAll + curlMiddle;
        float effectiveRing = curlAll + curlRing;
        float effectivePinky = curlAll + curlPinky;

        if (autoWiggle) {
            float t = Time.time * wiggleSpeed;
            effectiveIndex += Mathf.Sin(t) * wiggleRange;
            effectiveMiddle += Mathf.Sin(t + 0.3f) * wiggleRange;
            effectiveRing += Mathf.Sin(t + 0.6f) * wiggleRange;
            effectivePinky += Mathf.Sin(t + 0.9f) * wiggleRange;
            effectiveThumb += Mathf.Sin(t + 0.4f) * (wiggleRange * 0.7f);
        }

        Vector3 leftAxis = GetAxisVector(leftHandAxis);
        Vector3 rightAxis = GetAxisVector(rightHandAxis);

        ApplyCurl(leftThumbBones, effectiveThumb, leftAxis);
        ApplyCurl(leftIndexBones, effectiveIndex, leftAxis);
        ApplyCurl(leftMiddleBones, effectiveMiddle, leftAxis);
        ApplyCurl(leftRingBones, effectiveRing, leftAxis);
        ApplyCurl(leftPinkyBones, effectivePinky, leftAxis);

        ApplyCurl(rightThumbBones, effectiveThumb, rightAxis);
        ApplyCurl(rightIndexBones, effectiveIndex, rightAxis);
        ApplyCurl(rightMiddleBones, effectiveMiddle, rightAxis);
        ApplyCurl(rightRingBones, effectiveRing, rightAxis);
        ApplyCurl(rightPinkyBones, effectivePinky, rightAxis);
    }

    void ApplyCurl(List<Transform> bones, float angle, Vector3 localAxis) {
        Quaternion rotOffset = Quaternion.AngleAxis(angle, localAxis);
        foreach (var b in bones) {
            if (b != null) {
                Quaternion rest = restRotations.ContainsKey(b) ? restRotations[b] : b.localRotation;
                b.localRotation = rest * rotOffset;
            }
        }
    }

    void OnGUI() {
        GUILayout.BeginArea(new Rect(Screen.width - 290, 10, 280, 480), "旋风 (Vortex) 30 指节测试台", GUI.skin.window);
        scrollPos = GUILayout.BeginScrollView(scrollPos);

        GUI.backgroundColor = new Color(0.3f, 0.9f, 0.4f);
        if (GUILayout.Button("★ 1:1 对齐电影眩晕 Authoritative BindPose", GUILayout.Height(32))) {
            var fixerType = System.Type.GetType("VortexHandFixer, Assembly-CSharp-Editor");
            if (fixerType != null) {
                var method = fixerType.GetMethod("RebuildFlexibleFingers");
                if (method != null) method.Invoke(null, null);
            }
        }
        GUI.backgroundColor = Color.white;

        GUILayout.BeginHorizontal();
        if (GUILayout.Button("诊断 BindPoses")) DiagnoseBindposes();
        if (GUILayout.Button("重置姿态")) ResetToRest();
        GUILayout.EndHorizontal();

        GUILayout.Label($"左手指骨: {leftFingerBonesFound} | 右手指骨: {rightFingerBonesFound}");
        autoWiggle = GUILayout.Toggle(autoWiggle, " 自动摆动活动手指数 (Auto Wiggle)");

        GUILayout.Space(6);
        GUILayout.Label($"全手整体卷曲 (Curl All): {curlAll:F1}°");
        curlAll = GUILayout.HorizontalSlider(curlAll, -45f, 85f);

        GUILayout.Label($"拇指 (Thumb): {curlThumb:F1}°");
        curlThumb = GUILayout.HorizontalSlider(curlThumb, -45f, 85f);

        GUILayout.Label($"食指 (Index): {curlIndex:F1}°");
        curlIndex = GUILayout.HorizontalSlider(curlIndex, -45f, 85f);

        GUILayout.Label($"中指 (Middle): {curlMiddle:F1}°");
        curlMiddle = GUILayout.HorizontalSlider(curlMiddle, -45f, 85f);

        GUILayout.Label($"无名指 (Ring): {curlRing:F1}°");
        curlRing = GUILayout.HorizontalSlider(curlRing, -45f, 85f);

        GUILayout.Label($"小指 (Pinky): {curlPinky:F1}°");
        curlPinky = GUILayout.HorizontalSlider(curlPinky, -45f, 85f);

        GUILayout.EndScrollView();
        GUILayout.EndArea();
    }
}
