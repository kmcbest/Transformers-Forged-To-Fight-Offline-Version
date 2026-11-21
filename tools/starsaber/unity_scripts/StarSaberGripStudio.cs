using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

#if UNITY_EDITOR
using UnityEditor;
#endif

[ExecuteInEditMode]
public class StarSaberGripStudio : MonoBehaviour {
    private const string JETFIRE_BUNDLE_PATH = @"E:\Agent\TFTF\extracted_apk\assets\assetpack\jetfire_gs_leader2014_odr\jetfire_gs_leader2014.assetbundle";

    [Header("Components")]
    public SkinnedMeshRenderer robotSmr;
    public Transform swordTransform;
    public MeshFilter swordMeshFilter;

    [Header("Right Hand Finger Bones (9 Knuckle Joints)")]
    public Transform thumb1;   // Hand_R_1
    public Transform thumb2;   // Hand_R_4
    public Transform thumb3;   // Hand_R_5
    public Transform index1;   // Hand_R_2
    public Transform index2;   // Hand_R_6
    public Transform index3;   // Hand_R_7
    public Transform fingers1; // Hand_R_3 (Middle/Ring/Pinky base)
    public Transform fingers2; // Hand_R_8 (Middle/Ring/Pinky mid)
    public Transform fingers3; // Hand_R_9 (Middle/Ring/Pinky tip)

    [Header("Interactive Finger Curl Controls (0 = Open Rest, 1 = Tight Fist)")]
    [Range(0f, 1.2f)] public float curlAll = 0.0f;
    [Range(-0.5f, 1.2f)] public float thumbCurl = 0.0f;
    [Range(-1f, 1f)] public float thumbSplay = 0.0f;
    [Range(-0.5f, 1.2f)] public float indexCurl = 0.0f;
    [Range(-0.5f, 1.2f)] public float fingersCurl = 0.0f;

    [Header("Sword Transform Controls (Relative to Parent)")]
    public Vector3 swordLocalPosition = Vector3.zero;
    public Vector3 swordLocalEuler = Vector3.zero;
    public float swordScale = 1.0f;

    // Persisted true rest-pose rotations & curl axes so domain reloads never corrupt ResetToOpenHand()
    private const int CURRENT_CURL_AXIS_VERSION = 2;
    [SerializeField, HideInInspector] private bool hasCachedRest = false;
    [SerializeField, HideInInspector] private int curlAxisVersion = 0;
    [SerializeField, HideInInspector] private Quaternion[] cachedRestLocalRots = new Quaternion[9];
    [SerializeField, HideInInspector] private Vector3[] cachedCurlLocalAxes = new Vector3[9];
    [SerializeField, HideInInspector] private Vector3 cachedThumbSplayLocalAxis = Vector3.up;

    private float prevCurlAll = -99f;
    private float prevThumbCurl = -99f;
    private float prevThumbSplay = -99f;
    private float prevIndexCurl = -99f;
    private float prevFingersCurl = -99f;
    private Vector3 prevSwordPos = new Vector3(999f, 999f, 999f);
    private Vector3 prevSwordRot = new Vector3(999f, 999f, 999f);
    private float prevSwordScale = -99f;

    private Transform[] FingerBones => new Transform[] {
        thumb1, thumb2, thumb3,
        index1, index2, index3,
        fingers1, fingers2, fingers3
    };

    void OnEnable() {
        FindReferences();
        if (hasCachedRest && curlAxisVersion != CURRENT_CURL_AXIS_VERSION) {
            // Recompute inward curl axes using FromToRotation while preserving swordTransform & slider values!
            Vector3 savedSwordPos = swordTransform != null ? swordTransform.localPosition : Vector3.zero;
            Quaternion savedSwordRot = swordTransform != null ? swordTransform.localRotation : Quaternion.identity;
            Vector3 savedSwordScale = swordTransform != null ? swordTransform.localScale : Vector3.one;

            CaptureRestPose(true);
            ApplySlidersToBones();

            if (swordTransform != null) {
                swordTransform.localPosition = savedSwordPos;
                swordTransform.localRotation = savedSwordRot;
                swordTransform.localScale = savedSwordScale;
            }
        }
        // Preserve manual bone rotations & sword transforms across Unity C# domain reloads
        prevCurlAll = curlAll;
        prevThumbCurl = thumbCurl;
        prevThumbSplay = thumbSplay;
        prevIndexCurl = indexCurl;
        prevFingersCurl = fingersCurl;
        SyncSwordFieldsFromTransform();
    }

    public void FindReferences() {
        if (robotSmr == null) robotSmr = GetComponentInChildren<SkinnedMeshRenderer>(true);

        Transform[] allChildren = GetComponentsInChildren<Transform>(true);
        foreach (var t in allChildren) {
            string n = t.name;
            if (n == "Hand_R_1") thumb1 = t;
            else if (n == "Hand_R_4") thumb2 = t;
            else if (n == "Hand_R_5") thumb3 = t;
            else if (n == "Hand_R_2") index1 = t;
            else if (n == "Hand_R_6") index2 = t;
            else if (n == "Hand_R_7") index3 = t;
            else if (n == "Hand_R_3") fingers1 = t;
            else if (n == "Hand_R_8") fingers2 = t;
            else if (n == "Hand_R_9") fingers3 = t;
            else if (n == "StarSaberSword" || n == "starsaber_hitl_sword") {
                swordTransform = t;
                swordMeshFilter = t.GetComponentInChildren<MeshFilter>(true);
            }
        }
    }

    private static Vector3 ComputeCurlLocalAxis(Transform bone, Vector3 worldFrom, Vector3 worldTo, Vector3 fallbackWorldAxis) {
        Quaternion q = Quaternion.FromToRotation(worldFrom.normalized, worldTo.normalized);
        q.ToAngleAxis(out float ang, out Vector3 worldAxis);
        if (ang < 0f) worldAxis = -worldAxis;
        if (worldAxis.sqrMagnitude < 1e-6f) worldAxis = fallbackWorldAxis;
        return Quaternion.Inverse(bone.rotation) * worldAxis.normalized;
    }

    public void CaptureRestPose(bool forceResetNow = false) {
        FindReferences();
        Transform[] bones = FingerBones;

        if (forceResetNow && hasCachedRest) {
            for (int i = 0; i < bones.Length; i++) {
                if (bones[i] != null) bones[i].localRotation = cachedRestLocalRots[i];
            }
        }

        // Compute world inward direction from RightHand fingers toward torso center
        Transform torsoRef = null;
        foreach (var t in GetComponentsInChildren<Transform>(true)) {
            if (t.name == "Spine1" || t.name == "Hips") { torsoRef = t; break; }
        }
        Vector3 handCenter = (index1 != null && fingers1 != null)
            ? (index1.position + fingers1.position) * 0.5f
            : transform.position;
        Vector3 torsoPos = torsoRef != null ? new Vector3(torsoRef.position.x, handCenter.y, torsoRef.position.z) : transform.position;
        Vector3 worldInward = (torsoPos - new Vector3(handCenter.x, handCenter.y, handCenter.z));
        if (worldInward.sqrMagnitude < 1e-4f) worldInward = -transform.right;
        worldInward.Normalize();

        // Across palm from fingers1 (pinky side) toward index1 (thumb side)
        Vector3 worldForward = (index1 != null && fingers1 != null)
            ? (index1.position - fingers1.position).normalized
            : transform.forward;

        for (int i = 0; i < bones.Length; i++) {
            Transform b = bones[i];
            if (b == null) continue;
            cachedRestLocalRots[i] = b.localRotation;

            if (i < 3) {
                // Thumb curls inward toward palm center + slightly downward/back across fingers
                Vector3 thumbTargetDir = (worldInward * 0.85f - transform.up * 0.35f - worldForward * 0.25f).normalized;
                Vector3 boneAxisDir = (thumb2 != null && thumb1 != null)
                    ? (thumb2.position - thumb1.position).normalized
                    : (worldInward + transform.forward).normalized;
                cachedCurlLocalAxes[i] = ComputeCurlLocalAxis(b, boneAxisDir, thumbTargetDir, worldForward);
            } else {
                // Index & 3-finger block point downward (-up) and curl cleanly INWARD toward palm (worldInward)
                Vector3 fingerDown = (i < 6 && index2 != null && index1 != null)
                    ? (index2.position - index1.position).normalized
                    : ((fingers2 != null && fingers1 != null) ? (fingers2.position - fingers1.position).normalized : -transform.up);
                cachedCurlLocalAxes[i] = ComputeCurlLocalAxis(b, fingerDown, worldInward, worldForward);
            }
        }

        if (thumb1 != null) {
            Vector3 boneAxisDir = (thumb2 != null) ? (thumb2.position - thumb1.position).normalized : transform.forward;
            cachedThumbSplayLocalAxis = ComputeCurlLocalAxis(thumb1, boneAxisDir, transform.up, transform.up);
        }

        if (swordTransform != null) {
            swordLocalPosition = swordTransform.localPosition;
            swordLocalEuler = swordTransform.localEulerAngles;
            swordScale = swordTransform.localScale.x;
        }

        hasCachedRest = true;
        curlAxisVersion = CURRENT_CURL_AXIS_VERSION;
#if UNITY_EDITOR
        EditorUtility.SetDirty(this);
#endif
    }

    public void InitializeBones() {
        FindReferences();
        if (!hasCachedRest) {
            CaptureRestPose(false);
        }
        SyncSwordFieldsFromTransform();
    }

    public void SyncSwordFieldsFromTransform() {
        if (swordTransform == null) return;
        swordLocalPosition = swordTransform.localPosition;
        swordLocalEuler = swordTransform.localEulerAngles;
        swordScale = swordTransform.localScale.x;
        prevSwordPos = swordLocalPosition;
        prevSwordRot = swordLocalEuler;
        prevSwordScale = swordScale;
    }

    void Update() {
        if (!hasCachedRest) InitializeBones();

        bool fingerSlidersChanged =
            Mathf.Abs(curlAll - prevCurlAll) > 1e-4f ||
            Mathf.Abs(thumbCurl - prevThumbCurl) > 1e-4f ||
            Mathf.Abs(thumbSplay - prevThumbSplay) > 1e-4f ||
            Mathf.Abs(indexCurl - prevIndexCurl) > 1e-4f ||
            Mathf.Abs(fingersCurl - prevFingersCurl) > 1e-4f;

        if (fingerSlidersChanged) {
            ApplySlidersToBones();
        }

        if (swordTransform != null) {
            bool swordFieldsChanged =
                (swordLocalPosition - prevSwordPos).sqrMagnitude > 1e-8f ||
                (swordLocalEuler - prevSwordRot).sqrMagnitude > 1e-5f ||
                Mathf.Abs(swordScale - prevSwordScale) > 1e-4f;

            if (swordFieldsChanged) {
                swordTransform.localPosition = swordLocalPosition;
                swordTransform.localEulerAngles = swordLocalEuler;
                swordTransform.localScale = Vector3.one * Mathf.Max(0.1f, swordScale);
                prevSwordPos = swordLocalPosition;
                prevSwordRot = swordLocalEuler;
                prevSwordScale = swordScale;
            } else {
                // If user moved sword directly in Scene View with Gizmo, reflect into Inspector fields
                if ((swordTransform.localPosition - prevSwordPos).sqrMagnitude > 1e-8f ||
                    (swordTransform.localEulerAngles - prevSwordRot).sqrMagnitude > 1e-5f ||
                    Mathf.Abs(swordTransform.localScale.x - prevSwordScale) > 1e-4f) {
                    SyncSwordFieldsFromTransform();
                }
            }
        }
    }

    public void ApplySlidersToBones() {
        if (!hasCachedRest) CaptureRestPose(false);
        Transform[] bones = FingerBones;

        float effThumb = Mathf.Clamp(thumbCurl + curlAll, -0.3f, 1.3f);
        float effIndex = Mathf.Clamp(indexCurl + curlAll, -0.3f, 1.3f);
        float effFingers = Mathf.Clamp(fingersCurl + curlAll, -0.3f, 1.3f);

        float[] angles = new float[] {
            effThumb * 30f, effThumb * 38f, effThumb * 32f,         // Thumb 1, 2, 3
            effIndex * 34f, effIndex * 66f, effIndex * 54f,         // Index 1, 2, 3
            effFingers * 34f, effFingers * 68f, effFingers * 58f    // Main 3 fingers 1, 2, 3
        };

        for (int i = 0; i < bones.Length; i++) {
            Transform b = bones[i];
            if (b == null) continue;
            Quaternion rotDelta = Quaternion.AngleAxis(angles[i], cachedCurlLocalAxes[i]);
            if (i == 0 && Mathf.Abs(thumbSplay) > 1e-4f) {
                rotDelta = Quaternion.AngleAxis(thumbSplay * 35f, cachedThumbSplayLocalAxis) * rotDelta;
            }
            b.localRotation = cachedRestLocalRots[i] * rotDelta;
        }

        prevCurlAll = curlAll;
        prevThumbCurl = thumbCurl;
        prevThumbSplay = thumbSplay;
        prevIndexCurl = indexCurl;
        prevFingersCurl = fingersCurl;
    }

    public Vector3 GetPalmWorldCenter() {
        FindReferences();
        if (index1 != null && fingers1 != null && index2 != null && fingers2 != null) {
            Vector3 knuckleMid = (index1.position + fingers1.position) * 0.5f;
            Vector3 midJointCenter = (index2.position + fingers2.position) * 0.5f;
            Transform torsoRef = null;
            foreach (var t in GetComponentsInChildren<Transform>(true)) {
                if (t.name == "Spine1" || t.name == "Hips") { torsoRef = t; break; }
            }
            Vector3 inward = torsoRef != null
                ? Vector3.ProjectOnPlane(torsoRef.position - knuckleMid, transform.up).normalized
                : -transform.right;
            return (knuckleMid + midJointCenter) * 0.5f + inward * 0.16f;
        }
        return transform.position + transform.up * 5.8f;
    }

    public void ApplyHeroicGripPreset() {
        InitializeBones();
        curlAll = 0.92f;
        thumbCurl = 0.05f;
        thumbSplay = 0.15f;
        indexCurl = 0.0f;
        fingersCurl = 0.05f;
        ApplySlidersToBones();

        if (swordTransform != null) {
            // Position hilt directly inside the palm pocket computed from actual knuckle positions
            Vector3 palmPocket = GetPalmWorldCenter();
            swordTransform.position = palmPocket;

            // Detect actual blade axis from mesh bounds so we never suffer from Blender -90 deg FBX offsets
            Vector3 localBladeAxis = Vector3.up;
            if (swordMeshFilter != null && swordMeshFilter.sharedMesh != null) {
                Vector3 sz = swordMeshFilter.sharedMesh.bounds.size;
                if (sz.z >= sz.y && sz.z >= sz.x) localBladeAxis = Vector3.forward;
                else if (sz.x >= sz.y && sz.x >= sz.z) localBladeAxis = Vector3.right;
            }
            Vector3 desiredWorldBladeDir = (transform.forward * 0.82f + transform.up * 0.57f + transform.right * 0.08f).normalized;
            swordTransform.rotation = Quaternion.FromToRotation(localBladeAxis, desiredWorldBladeDir);
            swordTransform.localScale = Vector3.one;
            SyncSwordFieldsFromTransform();
        }
        Debug.Log("[StarSaber Grip Studio] Applied Heroic Sword Grip Preset (knuckle-anchored)!");
    }

    public void ResetToOpenHand() {
        InitializeBones();
        curlAll = thumbCurl = thumbSplay = indexCurl = fingersCurl = 0.0f;
        Transform[] bones = FingerBones;
        for (int i = 0; i < bones.Length; i++) {
            if (bones[i] != null) bones[i].localRotation = cachedRestLocalRots[i];
        }
        prevCurlAll = prevThumbCurl = prevThumbSplay = prevIndexCurl = prevFingersCurl = 0.0f;

        if (swordTransform != null) {
            swordTransform.position = GetPalmWorldCenter();
            swordTransform.localScale = Vector3.one;
            SyncSwordFieldsFromTransform();
        }
        Debug.Log("[StarSaber Grip Studio] Reset to Open Hand Rest Pose.");
    }

#if UNITY_EDITOR
    public void BakeAndSaveGrip() {
        Debug.Log("=== [StarSaber Grip Studio] Baking Posed Grip & Sword into Game-Ready 54-Bone Mesh Asset ===");
        FindReferences();

        if (robotSmr == null || robotSmr.sharedMesh == null) {
            Debug.LogError("[StarSaber Grip Studio] Missing robot SkinnedMeshRenderer or sharedMesh!");
            return;
        }
        if (swordTransform == null || swordMeshFilter == null || swordMeshFilter.sharedMesh == null) {
            Debug.LogError("[StarSaber Grip Studio] Missing swordTransform or sword Mesh!");
            return;
        }

        // 1. Load official Jetfire donor prefab (_00 SMR with exact 54 bones & bindposes)
        AssetBundle jetBundle = AssetBundle.LoadFromFile(JETFIRE_BUNDLE_PATH);
        if (jetBundle == null) {
            Debug.LogError("[StarSaber Grip Studio] Failed to load Jetfire donor bundle: " + JETFIRE_BUNDLE_PATH);
            return;
        }

        try {
            GameObject jetPrefab = null;
            foreach (var n in jetBundle.GetAllAssetNames()) {
                if (n.EndsWith("_lw.prefab")) { jetPrefab = jetBundle.LoadAsset<GameObject>(n); break; }
            }
            if (jetPrefab == null) {
                foreach (var g in jetBundle.LoadAllAssets<GameObject>()) {
                    if (g.name.ToLower().Contains("jetfire")) { jetPrefab = g; break; }
                }
            }
            if (jetPrefab == null) {
                Debug.LogError("[StarSaber Grip Studio] Missing Jetfire prefab inside donor bundle!");
                return;
            }

            SkinnedMeshRenderer donorSmr00 = null;
            foreach (var smr in jetPrefab.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
                if (smr.name.Contains("_00")) { donorSmr00 = smr; break; }
            }
            if (donorSmr00 == null) {
                Debug.LogError("[StarSaber Grip Studio] Missing _00 SMR on Jetfire donor prefab!");
                return;
            }

            // Build donor bone name -> index map
            Transform[] donorBones = donorSmr00.bones;
            var donorMap = new Dictionary<string, int>();
            for (int i = 0; i < donorBones.Length; i++) {
                if (donorBones[i] != null) donorMap[donorBones[i].name] = i;
            }
            int hipsIdx = donorMap.ContainsKey("Hips") ? donorMap["Hips"] : 0;
            int rightHandIdx = donorMap.ContainsKey("RightHand") ? donorMap["RightHand"] : hipsIdx;

            // Map HITL SMR bones -> Jetfire 54 donor bones (Hand_R_* fold rigidly into RightHand!)
            Transform[] srcBones = robotSmr.bones;
            int[] boneRemap = new int[srcBones.Length];
            for (int j = 0; j < srcBones.Length; j++) {
                string bn = srcBones[j] != null ? srcBones[j].name : "";
                if (bn.StartsWith("Hand_R_")) {
                    boneRemap[j] = rightHandIdx;
                } else if (donorMap.TryGetValue(bn, out int idx)) {
                    boneRemap[j] = idx;
                } else {
                    boneRemap[j] = hipsIdx;
                }
            }

            // 2. Bake deformed robot mesh & transform vertices into StarSaber_Candidate root local space
            // Note: BakeMesh(mesh, false) bakes vertices in robotSmr.transform unscaled local space (or with lossyScale if true in 2020.2+).
            Mesh bakedRobot = new Mesh();
            robotSmr.BakeMesh(bakedRobot);

            // Check whether BakeMesh baked lossyScale or not: transform position+rotation carefully
            Vector3 lossy = robotSmr.transform.lossyScale;
            Matrix4x4 smrPosRot = Matrix4x4.TRS(robotSmr.transform.position, robotSmr.transform.rotation, Vector3.one);
            // If BakeMesh already includes lossyScale (standard Unity BakeMesh behavior), do NOT scale again!
            bool scaleAlreadyBaked = (bakedRobot.bounds.size.y > 5.0f && Mathf.Abs(lossy.y - 1f) > 0.05f);
            Matrix4x4 robotToRoot = transform.worldToLocalMatrix * (scaleAlreadyBaked ? smrPosRot : robotSmr.transform.localToWorldMatrix);

            Vector3[] rVertsRaw = bakedRobot.vertices;
            Vector3[] rNormalsRaw = bakedRobot.normals;
            Vector4[] rTangentsRaw = bakedRobot.tangents;
            Vector2[] rUvs = robotSmr.sharedMesh.uv;
            BoneWeight[] rWeightsRaw = robotSmr.sharedMesh.boneWeights;

            int rCount = rVertsRaw.Length;
            Vector3[] rVerts = new Vector3[rCount];
            Vector3[] rNormals = new Vector3[rCount];
            Vector4[] rTangents = (rTangentsRaw != null && rTangentsRaw.Length == rCount) ? new Vector4[rCount] : null;
            BoneWeight[] rWeights = new BoneWeight[rCount];

            for (int i = 0; i < rCount; i++) {
                rVerts[i] = robotToRoot.MultiplyPoint3x4(rVertsRaw[i]);
                rNormals[i] = robotToRoot.MultiplyVector(rNormalsRaw[i]).normalized;
                if (rTangents != null) {
                    Vector3 tv = robotToRoot.MultiplyVector(new Vector3(rTangentsRaw[i].x, rTangentsRaw[i].y, rTangentsRaw[i].z)).normalized;
                    rTangents[i] = new Vector4(tv.x, tv.y, tv.z, rTangentsRaw[i].w);
                }
                BoneWeight bw = rWeightsRaw[i];
                bw.boneIndex0 = (bw.boneIndex0 >= 0 && bw.boneIndex0 < boneRemap.Length) ? boneRemap[bw.boneIndex0] : hipsIdx;
                bw.boneIndex1 = (bw.boneIndex1 >= 0 && bw.boneIndex1 < boneRemap.Length) ? boneRemap[bw.boneIndex1] : hipsIdx;
                bw.boneIndex2 = (bw.boneIndex2 >= 0 && bw.boneIndex2 < boneRemap.Length) ? boneRemap[bw.boneIndex2] : hipsIdx;
                bw.boneIndex3 = (bw.boneIndex3 >= 0 && bw.boneIndex3 < boneRemap.Length) ? boneRemap[bw.boneIndex3] : hipsIdx;
                rWeights[i] = bw;
            }

            // 3. Transform sword mesh vertices into StarSaber_Candidate root local space (bound 100% to RightHand)
            Mesh swordMesh = swordMeshFilter.sharedMesh;
            Matrix4x4 swordToRoot = transform.worldToLocalMatrix * swordMeshFilter.transform.localToWorldMatrix;
            Vector3[] sVertsRaw = swordMesh.vertices;
            Vector3[] sNormalsRaw = swordMesh.normals;
            Vector4[] sTangentsRaw = swordMesh.tangents;
            Vector2[] sUvs = swordMesh.uv;

            int sCount = sVertsRaw.Length;
            Vector3[] sVerts = new Vector3[sCount];
            Vector3[] sNormals = new Vector3[sCount];
            Vector4[] sTangents = (sTangentsRaw != null && sTangentsRaw.Length == sCount) ? new Vector4[sCount] : null;
            BoneWeight[] sWeights = new BoneWeight[sCount];

            for (int i = 0; i < sCount; i++) {
                sVerts[i] = swordToRoot.MultiplyPoint3x4(sVertsRaw[i]);
                sNormals[i] = swordToRoot.MultiplyVector(sNormalsRaw[i]).normalized;
                if (sTangents != null) {
                    Vector3 tv = swordToRoot.MultiplyVector(new Vector3(sTangentsRaw[i].x, sTangentsRaw[i].y, sTangentsRaw[i].z)).normalized;
                    sTangents[i] = new Vector4(tv.x, tv.y, tv.z, sTangentsRaw[i].w);
                }
                sWeights[i] = new BoneWeight { boneIndex0 = rightHandIdx, weight0 = 1.0f };
            }

            // 4. Combine into game-ready 54-bone mesh with Submesh 0 (Body) & Submesh 1 (Sword)
            int totalVerts = rCount + sCount;
            Vector3[] combinedVerts = new Vector3[totalVerts];
            Vector3[] combinedNormals = new Vector3[totalVerts];
            Vector4[] combinedTangents = (rTangents != null && sTangents != null) ? new Vector4[totalVerts] : null;
            Vector2[] combinedUvs = new Vector2[totalVerts];
            BoneWeight[] combinedWeights = new BoneWeight[totalVerts];

            Array.Copy(rVerts, 0, combinedVerts, 0, rCount);
            Array.Copy(sVerts, 0, combinedVerts, rCount, sCount);
            Array.Copy(rNormals, 0, combinedNormals, 0, rCount);
            Array.Copy(sNormals, 0, combinedNormals, rCount, sCount);
            if (combinedTangents != null) {
                Array.Copy(rTangents, 0, combinedTangents, 0, rCount);
                Array.Copy(sTangents, 0, combinedTangents, rCount, sCount);
            }
            Array.Copy(rUvs, 0, combinedUvs, 0, rCount);
            Array.Copy(sUvs, 0, combinedUvs, rCount, sCount);
            Array.Copy(rWeights, 0, combinedWeights, 0, rCount);
            Array.Copy(sWeights, 0, combinedWeights, rCount, sCount);

            int[] robotTris = robotSmr.sharedMesh.GetTriangles(0);
            int[] swordTris = swordMesh.GetTriangles(0);
            int[] offsetSwordTris = new int[swordTris.Length];
            for (int i = 0; i < swordTris.Length; i++) offsetSwordTris[i] = swordTris[i] + rCount;

            // Verify winding against normals for both submeshes
            FixWinding(combinedVerts, combinedNormals, robotTris);
            FixWinding(combinedVerts, combinedNormals, offsetSwordTris);

            Mesh combinedMesh = new Mesh { name = "cha_jetfire_gs_leader2014_00" };
            if (totalVerts > 65535) combinedMesh.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;
            combinedMesh.vertices = combinedVerts;
            combinedMesh.normals = combinedNormals;
            if (combinedTangents != null) combinedMesh.tangents = combinedTangents;
            combinedMesh.uv = combinedUvs;
            combinedMesh.boneWeights = combinedWeights;
            combinedMesh.bindposes = donorSmr00.sharedMesh.bindposes;

            combinedMesh.subMeshCount = 2;
            combinedMesh.SetTriangles(robotTris, 0);
            combinedMesh.SetTriangles(offsetSwordTris, 1);
            combinedMesh.RecalculateBounds();

            string assetPath = "Assets/StarSaber/cha_jetfire_gs_leader2014_00.asset";
            if (AssetDatabase.LoadAssetAtPath<Mesh>(assetPath) != null) {
                AssetDatabase.DeleteAsset(assetPath);
            }
            AssetDatabase.CreateAsset(combinedMesh, assetPath);
            AssetDatabase.SaveAssets();

            // 5. Save HITL JSON config
            var config = new GripConfig {
                swordLocalPosition = swordTransform.localPosition,
                swordLocalRotationEuler = swordTransform.localEulerAngles,
                swordScale = swordTransform.localScale.x,
                curlAll = curlAll,
                thumbCurl = thumbCurl,
                thumbSplay = thumbSplay,
                indexCurl = indexCurl,
                fingersCurl = fingersCurl,
                thumb1Rot = thumb1 ? thumb1.localEulerAngles : Vector3.zero,
                thumb2Rot = thumb2 ? thumb2.localEulerAngles : Vector3.zero,
                thumb3Rot = thumb3 ? thumb3.localEulerAngles : Vector3.zero,
                index1Rot = index1 ? index1.localEulerAngles : Vector3.zero,
                index2Rot = index2 ? index2.localEulerAngles : Vector3.zero,
                index3Rot = index3 ? index3.localEulerAngles : Vector3.zero,
                fingers1Rot = fingers1 ? fingers1.localEulerAngles : Vector3.zero,
                fingers2Rot = fingers2 ? fingers2.localEulerAngles : Vector3.zero,
                fingers3Rot = fingers3 ? fingers3.localEulerAngles : Vector3.zero,
                bakedTimestamp = DateTime.UtcNow.ToString("o")
            };
            string jsonPath = Path.Combine(Application.dataPath, "StarSaber/starsaber_grip_config.json");
            File.WriteAllText(jsonPath, JsonUtility.ToJson(config, true));
            AssetDatabase.Refresh();

            UnityEngine.Object.DestroyImmediate(bakedRobot);
            Debug.Log($"[🎉 HITL SUCCESS] Baked 54-bone Star Saber Mesh (bounds={combinedMesh.bounds.size:F2}) -> {assetPath} & {jsonPath}");
        } finally {
            jetBundle.Unload(false);
        }
    }

    private static void FixWinding(Vector3[] verts, Vector3[] normals, int[] tris) {
        double dotSum = 0.0;
        for (int t = 0; t + 2 < tris.Length; t += 3) {
            Vector3 c = Vector3.Cross(verts[tris[t + 1]] - verts[tris[t]], verts[tris[t + 2]] - verts[tris[t]]);
            if (c.sqrMagnitude > 1e-12f) dotSum += Vector3.Dot(c.normalized, normals[tris[t]]);
        }
        if (dotSum < 0.0) {
            for (int t = 0; t + 2 < tris.Length; t += 3) {
                int tmp = tris[t + 1]; tris[t + 1] = tris[t + 2]; tris[t + 2] = tmp;
            }
        }
    }

    [System.Serializable]
    public class GripConfig {
        public Vector3 swordLocalPosition;
        public Vector3 swordLocalRotationEuler;
        public float swordScale;
        public float curlAll;
        public float thumbCurl;
        public float thumbSplay;
        public float indexCurl;
        public float fingersCurl;
        public Vector3 thumb1Rot;
        public Vector3 thumb2Rot;
        public Vector3 thumb3Rot;
        public Vector3 index1Rot;
        public Vector3 index2Rot;
        public Vector3 index3Rot;
        public Vector3 fingers1Rot;
        public Vector3 fingers2Rot;
        public Vector3 fingers3Rot;
        public string bakedTimestamp;
    }
#endif
}
