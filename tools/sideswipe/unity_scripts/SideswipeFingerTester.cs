using System;
using System.Collections.Generic;
using UnityEngine;

[ExecuteAlways]
public class SideswipeFingerTester : MonoBehaviour {
    [Header("Auto Motion (Real-time waving)")]
    public bool autoWiggle = false;
    [Range(0.5f, 10f)] public float wiggleSpeed = 2.5f;
    [Range(10f, 80f)] public float wiggleRange = 50f;

    [Header("Manual Curl Controls (-45 to +85 degrees)")]
    [Range(-45f, 85f)] public float curlAll = 0f;
    [Range(-45f, 85f)] public float curlThumb = 0f;
    [Range(-45f, 85f)] public float curlIndex = 0f;
    [Range(-45f, 85f)] public float curlMiddle = 0f;

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

    [Header("Diagnostics")]
    public int leftFingerBonesFound = 0;

    private readonly Dictionary<Transform, Quaternion> restRotations = new Dictionary<Transform, Quaternion>();
    private readonly List<Transform> leftThumbBones = new List<Transform>();
    private readonly List<Transform> leftIndexBones = new List<Transform>();
    private readonly List<Transform> leftMiddleBones = new List<Transform>();

    private bool initialized = false;
    private bool wasManualOverrideActive = false;

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

        Transform[] allChildren = GetComponentsInChildren<Transform>(true);
        foreach (var t in allChildren) {
            string n = t.name;
            if (!n.StartsWith("LeftHand")) continue;

            if (n.Contains("Thumb")) leftThumbBones.Add(t);
            else if (n.Contains("Index")) leftIndexBones.Add(t);
            else if (n.Contains("Middle")) leftMiddleBones.Add(t);

            if (!restRotations.ContainsKey(t)) restRotations[t] = t.localRotation;
        }

        leftFingerBonesFound = leftThumbBones.Count + leftIndexBones.Count + leftMiddleBones.Count;
        initialized = (leftFingerBonesFound > 0);
        Debug.Log($"[SideswipeFingerTester] Initialized: {leftFingerBonesFound} Left Hand (Thumb, Index, Middle) finger bones found.");
    }

    void LateUpdate() {
        if (!initialized) return;

        bool manualActive = (Mathf.Abs(curlAll) > 0.1f || Mathf.Abs(curlThumb) > 0.1f || Mathf.Abs(curlIndex) > 0.1f || Mathf.Abs(curlMiddle) > 0.1f);

        if (autoWiggle) {
            float phase = Time.time * wiggleSpeed;
            ApplyCurlList(leftThumbBones, Mathf.Sin(phase) * wiggleRange, leftHandAxis);
            ApplyCurlList(leftIndexBones, Mathf.Sin(phase + 0.5f) * wiggleRange, leftHandAxis);
            ApplyCurlList(leftMiddleBones, Mathf.Sin(phase + 1.0f) * wiggleRange, leftHandAxis);
            wasManualOverrideActive = true;
        } else if (manualActive) {
            ApplyCurlList(leftThumbBones, curlAll + curlThumb, leftHandAxis);
            ApplyCurlList(leftIndexBones, curlAll + curlIndex, leftHandAxis);
            ApplyCurlList(leftMiddleBones, curlAll + curlMiddle, leftHandAxis);
            wasManualOverrideActive = true;
        } else if (wasManualOverrideActive) {
            ResetToRest();
            wasManualOverrideActive = false;
        }
    }

    private void ApplyCurlList(List<Transform> bones, float angleDeg, CurlAxis axis) {
        Vector3 axisVec = Vector3.forward;
        switch (axis) {
            case CurlAxis.Forward_Z: axisVec = Vector3.forward; break;
            case CurlAxis.Back_NegZ: axisVec = Vector3.back; break;
            case CurlAxis.Right_X: axisVec = Vector3.right; break;
            case CurlAxis.Left_NegX: axisVec = Vector3.left; break;
            case CurlAxis.Up_Y: axisVec = Vector3.up; break;
            case CurlAxis.Down_NegY: axisVec = Vector3.down; break;
        }

        Quaternion delta = Quaternion.AngleAxis(angleDeg, axisVec);
        foreach (var t in bones) {
            if (t != null && restRotations.TryGetValue(t, out Quaternion r)) {
                t.localRotation = r * delta;
            }
        }
    }

    public void CaptureCurrentAsRest() {
        foreach (var list in new[] { leftThumbBones, leftIndexBones, leftMiddleBones }) {
            foreach (var t in list) {
                if (t != null) restRotations[t] = t.localRotation;
            }
        }
    }

    public void EvaluatePoseNow() {
        if (!initialized) return;
        ApplyCurlList(leftThumbBones, curlAll + curlThumb, leftHandAxis);
        ApplyCurlList(leftIndexBones, curlAll + curlIndex, leftHandAxis);
        ApplyCurlList(leftMiddleBones, curlAll + curlMiddle, leftHandAxis);
        wasManualOverrideActive = true;
    }

    public void ResetAll() {
        curlAll = 0f;
        curlThumb = 0f;
        curlIndex = 0f;
        curlMiddle = 0f;
        autoWiggle = false;
        wasManualOverrideActive = false;
        ResetToRest();
    }

    public void ResetToRest() {
        foreach (var kvp in restRotations) {
            if (kvp.Key != null) kvp.Key.localRotation = kvp.Value;
        }
    }
}
