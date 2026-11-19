using UnityEngine;
using UnityEditor;
using System.IO;
using System.Text;
using System.Collections.Generic;

public static class ExportSlipstreamDwarfAnimation {
    public static void Run() {
        string fbxPath = "Assets/Mixamo/pose_03_dwarf_nails.fbx";
        ModelImporter mi = AssetImporter.GetAtPath(fbxPath) as ModelImporter;
        if (mi.animationType != ModelImporterAnimationType.Human) {
            mi.animationType = ModelImporterAnimationType.Human;
            mi.SaveAndReimport();
        }

        GameObject mixPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
        GameObject mixInst = Object.Instantiate(mixPrefab);
        Animator mixAnim = mixInst.GetComponent<Animator>();

        AnimationClip clip = null;
        foreach (var a in AssetDatabase.LoadAllAssetsAtPath(fbxPath)) {
            if (a is AnimationClip && !a.name.StartsWith("__preview__")) {
                clip = (AnimationClip)a;
                break;
            }
        }
        if (clip == null) {
            Debug.LogError("[ExportSlipstreamDwarf] AnimationClip not found in FBX!");
            EditorApplication.Exit(1);
            return;
        }

        string bundlePath = @"D:\Agent\tftf\backup\slipstream_gs.assetbundle.orig";
        AssetBundle.UnloadAllAssetBundles(true);
        AssetBundle bundle = AssetBundle.LoadFromFile(bundlePath);
        GameObject sPrefab = null;
        foreach (var n in bundle.GetAllAssetNames()) {
            if (n.EndsWith("_lw.prefab")) { sPrefab = bundle.LoadAsset<GameObject>(n); break; }
        }

        GameObject clean = Object.Instantiate(sPrefab);
        clean.transform.position = Vector3.zero;
        clean.transform.rotation = Quaternion.identity;
        Animator sAnim = clean.GetComponent<Animator>();
        sAnim.enabled = false;
        Transform cleanCM = clean.transform.Find("character_model");

        HumanPoseHandler hphMix = new HumanPoseHandler(mixAnim.avatar, mixInst.transform);
        HumanPoseHandler hphClean = new HumanPoseHandler(sAnim.avatar, cleanCM);
        HumanPose hp = new HumanPose();

        float actualHs = sAnim.humanScale;
        if (actualHs < 0.1f) actualHs = 5.7809f;
        float scaleEst = actualHs;

        Transform lf = FindChild(clean.transform, "LeftFoot");
        Transform rf = FindChild(clean.transform, "RightFoot");
        Transform lh = FindChild(clean.transform, "LeftHand");
        Transform rh = FindChild(clean.transform, "RightHand");

        Quaternion offsetFoot = new Quaternion(0.2421f, 0.6641f, -0.6647f, 0.2419f);
        Quaternion offsetLH = new Quaternion(-0.0976f, -0.0733f, -0.9796f, 0.1601f);
        Quaternion offsetRH = new Quaternion(0.0976f, -0.0733f, 0.9796f, 0.1601f);

        int totalFrames = 134; // 0..133 (4.433333s @ 30fps)
        float clipDuration = 4.433333f;

        Debug.Log($"[ExportSlipstreamDwarf] Starting export of {totalFrames} frames (duration={clipDuration:F3}s)...");

        string jsonPath = @"D:\Agent\tftf\build\slipstream_anim_dwarf_export.json";
        using (StreamWriter sw = new StreamWriter(jsonPath, false, Encoding.UTF8)) {
            sw.WriteLine("{");
            sw.WriteLine($"  \"duration\": {clipDuration:F6},");
            sw.WriteLine($"  \"sampleRate\": 30.0,");
            sw.WriteLine($"  \"frameCount\": {totalFrames},");
            sw.WriteLine($"  \"humanScale\": {actualHs:F6},");
            sw.WriteLine("  \"frames\": [");

            for (int f = 0; f < totalFrames; f++) {
                float t = (float)f / 30.0f;
                if (t > clipDuration) t = clipDuration;

                clip.SampleAnimation(mixInst, t);
                hphMix.GetHumanPose(ref hp);

                // Straighten foot/ankle twist so feet align cleanly without outward eversion
                hp.muscles[27] = 0.00f; // Left Foot Twist In-Out
                hp.muscles[35] = 0.00f; // Right Foot Twist In-Out
                hp.muscles[25] = -0.05f; // Left Lower Leg Twist In-Out
                hp.muscles[33] = +0.05f; // Right Lower Leg Twist In-Out

                hphClean.SetHumanPose(ref hp);

                // Grounding adjustment: make sure feet are grounded at y=0 without sinking
                float curMinY = GetMinMeshY(clean);
                hp.bodyPosition.y -= curMinY / scaleEst;
                hphClean.SetHumanPose(ref hp);

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

                // Write frame JSON object
                sw.Write("    {");
                sw.Write($"\"rootT\":[{hp.bodyPosition.x:F6},{hp.bodyPosition.y:F6},{hp.bodyPosition.z:F6}],");
                sw.Write($"\"rootQ\":[{hp.bodyRotation.x:F6},{hp.bodyRotation.y:F6},{hp.bodyRotation.z:F6},{hp.bodyRotation.w:F6}],");
                sw.Write($"\"leftFootT\":[{lfT.x:F6},{lfT.y:F6},{lfT.z:F6}],");
                sw.Write($"\"leftFootQ\":[{lfQ.x:F6},{lfQ.y:F6},{lfQ.z:F6},{lfQ.w:F6}],");
                sw.Write($"\"rightFootT\":[{rfT.x:F6},{rfT.y:F6},{rfT.z:F6}],");
                sw.Write($"\"rightFootQ\":[{rfQ.x:F6},{rfQ.y:F6},{rfQ.z:F6},{rfQ.w:F6}],");
                sw.Write($"\"leftHandT\":[{lhT.x:F6},{lhT.y:F6},{lhT.z:F6}],");
                sw.Write($"\"leftHandQ\":[{lhQ.x:F6},{lhQ.y:F6},{lhQ.z:F6},{lhQ.w:F6}],");
                sw.Write($"\"rightHandT\":[{rhT.x:F6},{rhT.y:F6},{rhT.z:F6}],");
                sw.Write($"\"rightHandQ\":[{rhQ.x:F6},{rhQ.y:F6},{rhQ.z:F6},{rhQ.w:F6}],");
                sw.Write("\"muscles\":[");
                for (int m = 0; m < hp.muscles.Length; m++) {
                    sw.Write($"{hp.muscles[m]:F6}{(m < hp.muscles.Length - 1 ? "," : "")}");
                }
                sw.Write("]}");
                if (f < totalFrames - 1) sw.WriteLine(",");
                else sw.WriteLine();
            }

            sw.WriteLine("  ]");
            sw.WriteLine("}");
        }

        Debug.Log($"[ExportSlipstreamDwarf] Successfully saved {totalFrames} frames to {jsonPath}");

        Object.DestroyImmediate(clean);
        Object.DestroyImmediate(mixInst);
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
