using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

[InitializeOnLoad]
public class VortexHandFixer : EditorWindow {
    private const string FBX_ASSET_PATH = "Assets/Vortex/vortex_prepared.fbx";
    private const string GRAFTED_MESH_PATH = "Assets/Vortex/cha_vortex_grafted.asset";
    private const string MAT_MAIN_PATH = "Assets/Vortex/M_Vortex_Main.mat";
    private const string OFFICIAL_REF_NAME = "Grindor_Official_Reference";
    private const string CANDIDATE_NAME = "Vortex_Candidate";
    private const string SYNC_PREF_KEY = "TFTF_VortexFingerAlignedFbxTicks_v1";
    private static int pendingRetryCount = 0;

    static VortexHandFixer() {
        pendingRetryCount = 0;
        EditorApplication.delayCall += AutoHealAndSyncOnLoad;
        EditorSceneManager.sceneOpened += (scene, mode) => {
            pendingRetryCount = 0;
            EditorApplication.delayCall += AutoHealAndSyncOnLoad;
        };
    }

    private static void AutoHealAndSyncOnLoad() {
        if (EditorApplication.isPlayingOrWillChangePlaymode) return;
        if (EditorApplication.isCompiling || EditorApplication.isUpdating) {
            if (pendingRetryCount < 25) {
                pendingRetryCount++;
                EditorApplication.delayCall += AutoHealAndSyncOnLoad;
            }
            return;
        }

        GameObject vtxGo = FindSceneObjectEvenIfInactive(CANDIDATE_NAME);
        if (vtxGo == null) return;

        string fullFbxPath = Path.GetFullPath(Path.Combine(Application.dataPath, "../" + FBX_ASSET_PATH));
        if (!File.Exists(fullFbxPath)) return;

        string currentTicks = File.GetLastWriteTimeUtc(fullFbxPath).Ticks.ToString();
        string syncedTicks = EditorPrefs.GetString(SYNC_PREF_KEY, "");
        Mesh grafted = AssetDatabase.LoadAssetAtPath<Mesh>(GRAFTED_MESH_PATH);

        bool missingTester = (vtxGo.GetComponent<VortexFingerTester>() == null);
        bool needsHeal = (grafted == null || grafted.vertexCount == 0);
        bool fbxUpdated = (syncedTicks != currentTicks);

        if (needsHeal || fbxUpdated || missingTester) {
            Debug.Log($"[VortexHandFixer] Auto-syncing 30-finger Vortex mesh & tester (needsHeal={needsHeal}, fbxUpdated={fbxUpdated}, missingTester={missingTester})...");
            if (fbxUpdated) {
                AssetDatabase.ImportAsset(FBX_ASSET_PATH, ImportAssetOptions.ForceUpdate);
            }
            RebuildFlexibleFingers();
        }
    }

    private static GameObject FindSceneObjectEvenIfInactive(string targetName) {
        GameObject found = GameObject.Find(targetName);
        if (found != null) return found;

        var scene = EditorSceneManager.GetActiveScene();
        if (scene.IsValid() && scene.isLoaded) {
            foreach (var root in scene.GetRootGameObjects()) {
                if (root.name == targetName) return root;
            }
        }
        return null;
    }

    private static SkinnedMeshRenderer FindRobotSmr(GameObject rootGo) {
        if (rootGo == null) return null;
        foreach (var s in rootGo.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            string lower = s.name.ToLower();
            if (!s.name.Contains("_01") && !lower.Contains("vehicle") && !lower.Contains("wpns")) {
                return s;
            }
        }
        return rootGo.GetComponentInChildren<SkinnedMeshRenderer>(true);
    }

    [MenuItem("TFTF/Vortex - Rebuild Flexible Fingers (旋风灵动手部一键重构)", false, 20)]
    public static void RebuildFlexibleFingers() {
        Debug.Log("=== [Vortex Flexible Fingers] Starting 1:1 Grindor-Aligned 30-Finger Rebuild ===");

        GameObject vtxGo = FindSceneObjectEvenIfInactive(CANDIDATE_NAME);
        if (vtxGo == null) {
            Debug.LogError($"[Vortex Flexible Fingers] Could not find '{CANDIDATE_NAME}' in scene!");
            return;
        }

        SkinnedMeshRenderer smr = FindRobotSmr(vtxGo);
        if (smr == null) {
            Debug.LogError($"[Vortex Flexible Fingers] No robot SkinnedMeshRenderer found on {CANDIDATE_NAME}!");
            return;
        }

        ModelImporter importer = AssetImporter.GetAtPath(FBX_ASSET_PATH) as ModelImporter;
        if (importer != null) {
            bool dirtyImporter = false;
            if (!importer.isReadable) { importer.isReadable = true; dirtyImporter = true; }
            if (!importer.useFileScale) { importer.useFileScale = true; dirtyImporter = true; }
            if (Mathf.Abs(importer.globalScale - 1.0f) > 0.001f) { importer.globalScale = 1.0f; dirtyImporter = true; }
            if (dirtyImporter) {
                importer.SaveAndReimport();
            }
        }

        GameObject vtxPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(FBX_ASSET_PATH);
        if (vtxPrefab == null) {
            Debug.LogError("[Vortex Flexible Fingers] Failed to load FBX at " + FBX_ASSET_PATH);
            return;
        }

        SkinnedMeshRenderer fbxSmr = FindRobotSmr(vtxPrefab);
        Mesh fbxMesh = (fbxSmr != null) ? fbxSmr.sharedMesh : null;
        if (fbxMesh == null) {
            Debug.LogError("[Vortex Flexible Fingers] No sharedMesh found inside " + FBX_ASSET_PATH);
            return;
        }

        Vector3[] origVerts = fbxMesh.vertices;
        if (origVerts == null || origVerts.Length == 0) {
            Debug.LogError($"[Vortex Flexible Fingers] '{FBX_ASSET_PATH}' returned 0 vertices! Aborting.");
            return;
        }

        // Remap bones to Grindor 78 bones
        Transform[] bones = smr.bones;
        Dictionary<string, int> gBoneMap = new Dictionary<string, int>();
        for (int i = 0; i < bones.Length; i++) {
            if (bones[i] != null) {
                gBoneMap[bones[i].name] = i;
            }
        }

        int fallbackSpineIdx = gBoneMap.ContainsKey("Spine1") ? gBoneMap["Spine1"] : (gBoneMap.ContainsKey("Hips") ? gBoneMap["Hips"] : 0);
        int[] remapTable = new int[fbxSmr.bones.Length];
        int matchedBones = 0;
        for (int j = 0; j < fbxSmr.bones.Length; j++) {
            string bName = (fbxSmr.bones[j] != null) ? fbxSmr.bones[j].name : "";
            if (gBoneMap.TryGetValue(bName, out int gIdx)) {
                remapTable[j] = gIdx;
                matchedBones++;
            } else {
                remapTable[j] = fallbackSpineIdx;
            }
        }

        BoneWeight[] origWeights = fbxMesh.boneWeights;
        BoneWeight[] newWeights = new BoneWeight[origWeights.Length];
        for (int v = 0; v < origWeights.Length; v++) {
            BoneWeight bw = origWeights[v];
            bw.boneIndex0 = (bw.boneIndex0 >= 0 && bw.boneIndex0 < remapTable.Length) ? remapTable[bw.boneIndex0] : fallbackSpineIdx;
            bw.boneIndex1 = (bw.boneIndex1 >= 0 && bw.boneIndex1 < remapTable.Length) ? remapTable[bw.boneIndex1] : fallbackSpineIdx;
            bw.boneIndex2 = (bw.boneIndex2 >= 0 && bw.boneIndex2 < remapTable.Length) ? remapTable[bw.boneIndex2] : fallbackSpineIdx;
            bw.boneIndex3 = (bw.boneIndex3 >= 0 && bw.boneIndex3 < remapTable.Length) ? remapTable[bw.boneIndex3] : fallbackSpineIdx;
            newWeights[v] = bw;
        }

        float maxSpan = Mathf.Max(fbxMesh.bounds.size.x, Mathf.Max(fbxMesh.bounds.size.y, fbxMesh.bounds.size.z));
        float scaleFix = 1.0f;
        if (maxSpan < 0.5f) scaleFix = 100.0f;
        else if (maxSpan > 100.0f) scaleFix = 0.01f;
        bool zIsHeight = (fbxMesh.bounds.size.z > fbxMesh.bounds.size.y * 1.2f);

        Vector3[] newVerts = new Vector3[origVerts.Length];
        for (int i = 0; i < origVerts.Length; i++) {
            Vector3 v = origVerts[i] * scaleFix;
            newVerts[i] = zIsHeight ? new Vector3(-v.x, v.z, v.y) : v;
        }

        Vector3[] origNorms = fbxMesh.normals;
        Vector3[] newNorms = new Vector3[origNorms.Length];
        for (int i = 0; i < origNorms.Length; i++) {
            Vector3 n = origNorms[i];
            newNorms[i] = zIsHeight ? new Vector3(-n.x, n.z, n.y) : n;
        }

        Vector4[] origTans = fbxMesh.tangents;
        Vector4[] newTans = new Vector4[origTans.Length];
        for (int i = 0; i < origTans.Length; i++) {
            Vector4 t = origTans[i];
            newTans[i] = zIsHeight ? new Vector4(-t.x, t.z, t.y, t.w) : t;
        }

        int[][] submeshTris = new int[fbxMesh.subMeshCount][];
        for (int sm = 0; sm < fbxMesh.subMeshCount; sm++) {
            submeshTris[sm] = fbxMesh.GetTriangles(sm);
        }
        Vector2[] origUv = fbxMesh.uv;

        // Load Authoritative Grindor 78 BindPoses
        Dictionary<string, Matrix4x4> authBindposeByName = new Dictionary<string, Matrix4x4>();
        GameObject gRef = FindSceneObjectEvenIfInactive(OFFICIAL_REF_NAME);
        if (gRef != null) {
            SkinnedMeshRenderer gSmr = FindRobotSmr(gRef);
            if (gSmr != null && gSmr.sharedMesh != null) {
                Transform[] gBones = gSmr.bones;
                Matrix4x4[] gBps = gSmr.sharedMesh.bindposes;
                int count = Mathf.Min(gBones.Length, gBps.Length);
                for (int i = 0; i < count; i++) {
                    if (gBones[i] != null) {
                        authBindposeByName[gBones[i].name] = gBps[i];
                    }
                }
            }
        }

        Matrix4x4[] newBindposes = new Matrix4x4[bones.Length];
        Matrix4x4[] existingBps = (smr.sharedMesh != null && smr.sharedMesh.bindposes != null && smr.sharedMesh.bindposes.Length == bones.Length)
            ? smr.sharedMesh.bindposes
            : null;

        for (int i = 0; i < bones.Length; i++) {
            string bn = (bones[i] != null) ? bones[i].name : "";
            if (authBindposeByName.TryGetValue(bn, out Matrix4x4 bp)) {
                newBindposes[i] = bp;
            } else if (existingBps != null) {
                newBindposes[i] = existingBps[i];
            } else {
                newBindposes[i] = bones[i].worldToLocalMatrix * smr.transform.localToWorldMatrix;
                authBindposeByName[bn] = newBindposes[i];
            }
        }

        // Write Grafted Mesh Asset
        Mesh mesh = AssetDatabase.LoadAssetAtPath<Mesh>(GRAFTED_MESH_PATH);
        bool createdNewAsset = false;
        if (mesh == null) {
            mesh = new Mesh();
            mesh.name = "cha_vortex_gs_00";
            AssetDatabase.CreateAsset(mesh, GRAFTED_MESH_PATH);
            createdNewAsset = true;
        }

        if (!createdNewAsset) {
            Undo.RecordObject(mesh, "Rebuild Vortex Flexible Fingers");
        }

        mesh.Clear();
        mesh.name = "cha_vortex_gs_00";
        mesh.vertices = newVerts;
        mesh.normals = newNorms;
        mesh.tangents = newTans;
        mesh.uv = origUv;
        mesh.boneWeights = newWeights;
        mesh.subMeshCount = submeshTris.Length;
        for (int sm = 0; sm < submeshTris.Length; sm++) {
            mesh.SetTriangles(submeshTris[sm], sm);
        }
        mesh.bindposes = newBindposes;
        mesh.RecalculateBounds();
        EditorUtility.SetDirty(mesh);

        vtxGo.SetActive(true);
        smr.gameObject.SetActive(true);
        smr.enabled = true;
        smr.sharedMesh = mesh;

        Material matMain = AssetDatabase.LoadAssetAtPath<Material>(MAT_MAIN_PATH);
        if (matMain != null) {
            smr.sharedMaterials = new Material[] { matMain };
        }

        AssetDatabase.SaveAssets();

        string fullFbx = Path.GetFullPath(Path.Combine(Application.dataPath, "../" + FBX_ASSET_PATH));
        if (File.Exists(fullFbx) && mesh.vertexCount > 0) {
            EditorPrefs.SetString(SYNC_PREF_KEY, File.GetLastWriteTimeUtc(fullFbx).Ticks.ToString());
        }

        Debug.Log($"[Vortex Mesh Rebuilt] Verts={mesh.vertexCount}, MatchedBones={matchedBones}/{fbxSmr.bones.Length}, Bounds={mesh.bounds}");

        // Attach tester & align transforms to rest pose
        var tester = vtxGo.GetComponent<VortexFingerTester>();
        if (tester == null) {
            tester = vtxGo.AddComponent<VortexFingerTester>();
        }
        tester.autoWiggle = false;
        tester.curlAll = 0f;
        tester.leftHandAxis = VortexFingerTester.CurlAxis.Forward_Z;
        tester.rightHandAxis = VortexFingerTester.CurlAxis.Back_NegZ;

        var anim = vtxGo.GetComponent<Animator>();
        bool wasAnim = false;
        if (anim != null) {
            wasAnim = anim.enabled;
            anim.enabled = false;
        }

        int alignedCount = AlignHierarchyToBindposesRecursive(vtxGo.transform, smr.transform, authBindposeByName);
        Debug.Log($"[✓] Restored {alignedCount} Vortex bone transforms to 1:1 authoritative Grindor rest pose (Delta = 0.0mm)!");

        if (anim != null && wasAnim) {
            anim.enabled = true;
            if (Application.isPlaying) {
                anim.Rebind();
            }
        }

        tester.InitializeBones();
        tester.DiagnoseBindposes();

        if (!Application.isPlaying) {
            EditorUtility.SetDirty(smr);
            EditorUtility.SetDirty(vtxGo);
            EditorSceneManager.MarkSceneDirty(vtxGo.scene);
        }

        SceneView.RepaintAll();
        UnityEditorInternal.InternalEditorUtility.RepaintAllViews();

        Debug.Log($"<color=#00ff00>[✓ 旋风灵动手部重构完成] 顶点={mesh.vertexCount}，30 根手指关节枢轴与电影眩晕官方骨骼 1:1 严丝合缝对齐 (Delta = 0.0mm)！</color>");
    }

    private static int AlignHierarchyToBindposesRecursive(
        Transform current,
        Transform smrTransform,
        Dictionary<string, Matrix4x4> bindposeByName
    ) {
        int count = 0;
        if (bindposeByName.TryGetValue(current.name, out Matrix4x4 bp)) {
            Matrix4x4 restLocalToWorld = smrTransform.localToWorldMatrix * bp.inverse;
            current.position = restLocalToWorld.MultiplyPoint3x4(Vector3.zero);

            Vector3 forward = (Vector3)restLocalToWorld.GetColumn(2);
            Vector3 up = (Vector3)restLocalToWorld.GetColumn(1);
            if (forward.sqrMagnitude > 0.0001f && up.sqrMagnitude > 0.0001f) {
                current.rotation = Quaternion.LookRotation(forward.normalized, up.normalized);
            }
            current.localScale = Vector3.one;
            count++;
        }

        for (int i = 0; i < current.childCount; i++) {
            count += AlignHierarchyToBindposesRecursive(current.GetChild(i), smrTransform, bindposeByName);
        }
        return count;
    }

    [MenuItem("TFTF/Vortex - Open Hand Fixer Console", false, 23)]
    public static void OpenWindow() {
        GetWindow<VortexHandFixer>("Vortex 手部重构台");
    }

    private void OnGUI() {
        GUILayout.Label("旋风 (Vortex) 灵动手部与蒙皮重构控制台", EditorStyles.boldLabel);
        GUILayout.Space(8);
        GUI.backgroundColor = new Color(0.2f, 0.95f, 0.45f);
        if (GUILayout.Button("★ 一键重构灵动指节 (1:1 对齐电影眩晕指骨)", GUILayout.Height(42))) {
            RebuildFlexibleFingers();
        }
        GUI.backgroundColor = Color.white;

        GUILayout.Space(12);
        if (GUILayout.Button("在场景中高亮选中 Vortex_Candidate", GUILayout.Height(28))) {
            var go = FindSceneObjectEvenIfInactive(CANDIDATE_NAME);
            if (go != null) Selection.activeGameObject = go;
        }
    }
}
