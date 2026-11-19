using UnityEngine;
using UnityEditor;
using System.IO;
using System.Text;
using System.Collections.Generic;

public static class ExportChromiaAngryPose {
    public static void Run() {
        string fbxPath = "Assets/Mixamo/pose_01_angry_chromia.fbx";
        ModelImporter mi = AssetImporter.GetAtPath(fbxPath) as ModelImporter;
        if (mi.animationType != ModelImporterAnimationType.Human) {
            mi.animationType = ModelImporterAnimationType.Human;
            mi.SaveAndReimport();
        }

        GameObject mixPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
        GameObject mixInst = Object.Instantiate(mixPrefab);
        Animator mixAnim = mixInst.GetComponent<Animator>();

        foreach (var a in AssetDatabase.LoadAllAssetsAtPath(fbxPath)) {
            if (a is AnimationClip && !a.name.StartsWith("__preview__")) {
                ((AnimationClip)a).SampleAnimation(mixInst, 0.702f);
                break;
            }
        }

        HumanPoseHandler hphMix = new HumanPoseHandler(mixAnim.avatar, mixInst.transform);
        HumanPose hp = new HumanPose();
        hphMix.GetHumanPose(ref hp);
        Object.DestroyImmediate(mixInst);

        // Graceful finger wrap for crossed arms
        // Left hand fingers (resting on right upper arm/shoulder):
        hp.muscles[55 + 0] = -0.15f; hp.muscles[55 + 1] = -0.15f; hp.muscles[55 + 2] = -0.20f; hp.muscles[55 + 3] = -0.15f; // Thumb
        hp.muscles[55 + 4] = -0.25f; hp.muscles[55 + 5] = -0.10f; hp.muscles[55 + 6] = -0.45f; hp.muscles[55 + 7] = -0.25f; // Index
        hp.muscles[55 + 8] = -0.35f; hp.muscles[55 + 9] = -0.05f; hp.muscles[55 + 10] = -0.55f; hp.muscles[55 + 11] = -0.30f; // Middle
        hp.muscles[55 + 12] = -0.45f; hp.muscles[55 + 13] = -0.05f; hp.muscles[55 + 14] = -0.65f; hp.muscles[55 + 15] = -0.35f; // Ring
        hp.muscles[55 + 16] = -0.50f; hp.muscles[55 + 17] = -0.10f; hp.muscles[55 + 18] = -0.70f; hp.muscles[55 + 19] = -0.40f; // Pinky

        // Right hand fingers (resting on left upper arm):
        hp.muscles[75 + 0] = -0.15f; hp.muscles[75 + 1] = -0.15f; hp.muscles[75 + 2] = -0.20f; hp.muscles[75 + 3] = -0.15f;
        hp.muscles[75 + 4] = -0.25f; hp.muscles[75 + 5] = -0.10f; hp.muscles[75 + 6] = -0.45f; hp.muscles[75 + 7] = -0.25f;
        hp.muscles[75 + 8] = -0.35f; hp.muscles[75 + 9] = -0.05f; hp.muscles[75 + 10] = -0.55f; hp.muscles[75 + 11] = -0.30f;
        hp.muscles[75 + 12] = -0.45f; hp.muscles[75 + 13] = -0.05f; hp.muscles[75 + 14] = -0.65f; hp.muscles[75 + 15] = -0.35f;
        hp.muscles[75 + 16] = -0.50f; hp.muscles[75 + 17] = -0.10f; hp.muscles[75 + 18] = -0.70f; hp.muscles[75 + 19] = -0.40f;

        // Straighten foot/ankle twist so feet align cleanly without outward eversion
        hp.muscles[27] = 0.00f; // Left Foot Twist In-Out
        hp.muscles[35] = 0.00f; // Right Foot Twist In-Out
        hp.muscles[25] = -0.05f; // Left Lower Leg Twist In-Out
        hp.muscles[33] = +0.05f; // Right Lower Leg Twist In-Out

        string bundlePath = @"D:\Agent\tftf\backup\chromia_gs_kabam.assetbundle.orig";
        AssetBundle.UnloadAllAssetBundles(true);
        AssetBundle bundle = AssetBundle.LoadFromFile(bundlePath);
        GameObject cPrefab = null;
        foreach (var n in bundle.GetAllAssetNames()) {
            if (n.EndsWith("_lw.prefab")) { cPrefab = bundle.LoadAsset<GameObject>(n); break; }
        }

        GameObject clean = Object.Instantiate(cPrefab);
        clean.transform.position = Vector3.zero;
        clean.transform.rotation = Quaternion.identity;
        Animator cAnim = clean.GetComponent<Animator>();
        cAnim.enabled = false;
        Transform cleanCM = clean.transform.Find("character_model");

        HumanPoseHandler hphClean = new HumanPoseHandler(cAnim.avatar, cleanCM);
        hphClean.SetHumanPose(ref hp);

        // Grounding adjustment
        float minY = GetMinMeshY(clean);
        float hipsY = FindChild(clean.transform, "Hips").position.y;
        float scaleEst = hipsY / Mathf.Max(hp.bodyPosition.y, 0.01f);
        hp.bodyPosition.y -= minY / scaleEst;
        hphClean.SetHumanPose(ref hp);

        float newMinY = GetMinMeshY(clean);
        float actualHs = cAnim.humanScale;
        if (actualHs < 0.1f) actualHs = scaleEst;

        Transform lf = FindChild(clean.transform, "LeftFoot");
        Transform rf = FindChild(clean.transform, "RightFoot");
        Transform lh = FindChild(clean.transform, "LeftHand");
        Transform rh = FindChild(clean.transform, "RightHand");

        Quaternion offsetFoot = new Quaternion(0.2421f, 0.6641f, -0.6647f, 0.2419f);
        Quaternion offsetLH = new Quaternion(-0.0976f, -0.0733f, -0.9796f, 0.1601f);
        Quaternion offsetRH = new Quaternion(0.0976f, -0.0733f, 0.9796f, 0.1601f);

        Vector3 bodyWorldPos = hp.bodyPosition * actualHs;
        Quaternion invBodyRot = Quaternion.Inverse(hp.bodyRotation);

        Vector3 lfSoleWorld = new Vector3(lf.position.x, 0f, lf.position.z);
        Vector3 rfSoleWorld = new Vector3(rf.position.x, 0f, rf.position.z);

        Vector3 lfT = invBodyRot * ((lfSoleWorld - bodyWorldPos) / actualHs);
        Quaternion lfQ = invBodyRot * (lf.rotation * offsetFoot);
        Vector3 rfT = invBodyRot * ((rfSoleWorld - bodyWorldPos) / actualHs);
        Quaternion rfQ = invBodyRot * (rf.rotation * offsetFoot);

        Vector3 lhT = invBodyRot * ((lh.position - bodyWorldPos) / actualHs);
        Quaternion lhQ = invBodyRot * (lh.rotation * offsetLH);
        Vector3 rhT = invBodyRot * ((rh.position - bodyWorldPos) / actualHs);
        Quaternion rhQ = invBodyRot * (rh.rotation * offsetRH);

        Debug.Log(string.Format("[ExportChromiaAngry] actualHs={0:F4}, newMinY={1:F4}, bodyPos={2}, lfT={3}, rfT={4}",
            actualHs, newMinY, hp.bodyPosition.ToString("F4"), lfT.ToString("F4"), rfT.ToString("F4")));

        // Write JSON
        StringBuilder sb = new StringBuilder();
        sb.AppendLine("{");
        sb.AppendFormat("  \"humanScale\": {0:F6},\n", actualHs);
        sb.AppendFormat("  \"rootT\": [{0:F6}, {1:F6}, {2:F6}],\n", hp.bodyPosition.x, hp.bodyPosition.y, hp.bodyPosition.z);
        sb.AppendFormat("  \"rootQ\": [{0:F6}, {1:F6}, {2:F6}, {3:F6}],\n", hp.bodyRotation.x, hp.bodyRotation.y, hp.bodyRotation.z, hp.bodyRotation.w);
        sb.AppendFormat("  \"leftFootT\": [{0:F6}, {1:F6}, {2:F6}],\n", lfT.x, lfT.y, lfT.z);
        sb.AppendFormat("  \"leftFootQ\": [{0:F6}, {1:F6}, {2:F6}, {3:F6}],\n", lfQ.x, lfQ.y, lfQ.z, lfQ.w);
        sb.AppendFormat("  \"rightFootT\": [{0:F6}, {1:F6}, {2:F6}],\n", rfT.x, rfT.y, rfT.z);
        sb.AppendFormat("  \"rightFootQ\": [{0:F6}, {1:F6}, {2:F6}, {3:F6}],\n", rfQ.x, rfQ.y, rfQ.z, rfQ.w);
        sb.AppendFormat("  \"leftHandT\": [{0:F6}, {1:F6}, {2:F6}],\n", lhT.x, lhT.y, lhT.z);
        sb.AppendFormat("  \"leftHandQ\": [{0:F6}, {1:F6}, {2:F6}, {3:F6}],\n", lhQ.x, lhQ.y, lhQ.z, lhQ.w);
        sb.AppendFormat("  \"rightHandT\": [{0:F6}, {1:F6}, {2:F6}],\n", rhT.x, rhT.y, rhT.z);
        sb.AppendFormat("  \"rightHandQ\": [{0:F6}, {1:F6}, {2:F6}, {3:F6}],\n", rhQ.x, rhQ.y, rhQ.z, rhQ.w);
        sb.Append("  \"muscles\": [");
        for (int i = 0; i < hp.muscles.Length; i++) {
            sb.AppendFormat("{0:F6}{1}", hp.muscles[i], (i < hp.muscles.Length - 1) ? ", " : "");
        }
        sb.AppendLine("]");
        sb.AppendLine("}");

        string jsonPath = @"D:\Agent\tftf\build\chromia_pose_angry_export.json";
        File.WriteAllText(jsonPath, sb.ToString(), Encoding.UTF8);
        Debug.Log($"[ExportChromiaAngry] Saved: {jsonPath}");

        Object.DestroyImmediate(clean);
        AssetBundle.UnloadAllAssetBundles(true);
        EditorApplication.Exit(0);
    }

    private static float GetMinMeshY(GameObject inst) {
        float minY = float.MaxValue;
        foreach (var smr in inst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (!smr.enabled) continue;
            Mesh m = new Mesh();
            smr.BakeMesh(m);
            foreach (var v in m.vertices) {
                Vector3 wp = smr.transform.TransformPoint(v);
                if (wp.y < minY) minY = wp.y;
            }
            Object.DestroyImmediate(m);
        }
        return minY;
    }

    private static Transform FindChild(Transform root, string name) {
        if (root.name == name) return root;
        foreach (Transform c in root) {
            Transform r = FindChild(c, name);
            if (r != null) return r;
        }
        return null;
    }
}
