using UnityEngine;
using UnityEditor;
using System.IO;
using System.Text;
using System.Collections.Generic;

public static class ExportWindbladePose5Animation {
    public static void Run() {
        string fbxPath = "Assets/Mixamo/pose_05_lhip_rdown.fbx";
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
            Debug.LogError("[ExportWindbladePose5] AnimationClip not found in FBX!");
            EditorApplication.Exit(1);
            return;
        }

        string bundlePath = @"D:\Agent\tftf\backup\windblade_gs.assetbundle.orig";
        AssetBundle.UnloadAllAssetBundles(true);
        AssetBundle bundle = AssetBundle.LoadFromFile(bundlePath);
        GameObject wPrefab = null;
        foreach (var n in bundle.GetAllAssetNames()) {
            if (n.EndsWith("_lw.prefab")) { wPrefab = bundle.LoadAsset<GameObject>(n); break; }
        }

        GameObject clean = Object.Instantiate(wPrefab);
        clean.transform.position = Vector3.zero;
        clean.transform.rotation = Quaternion.identity;
        Animator wAnim = clean.GetComponent<Animator>();
        wAnim.enabled = false;
        Transform cleanCM = clean.transform.Find("character_model");

        HumanPoseHandler hphMix = new HumanPoseHandler(mixAnim.avatar, mixInst.transform);
        HumanPoseHandler hphClean = new HumanPoseHandler(wAnim.avatar, cleanCM);
        HumanPose baseHp = new HumanPose();

        clip.SampleAnimation(mixInst, 0f);
        hphMix.GetHumanPose(ref baseHp);

        // 1. Right hand authentic sword grip from Frontend_Sword_idle (wrapping hilt securely)
        baseHp.muscles[75 + 0] = -1.5541633f; // Thumb 1 Stretched
        baseHp.muscles[75 + 1] = -2.1583767f; // Thumb Spread
        baseHp.muscles[75 + 2] = -0.2255878f; // Thumb 2 Stretched
        baseHp.muscles[75 + 3] = -0.4691082f; // Thumb 3 Stretched
        baseHp.muscles[75 + 4] = -0.5655559f; // Index 1 Stretched
        baseHp.muscles[75 + 5] = -0.7321508f; // Index Spread
        baseHp.muscles[75 + 6] = -1.2284926f; // Index 2 Stretched
        baseHp.muscles[75 + 7] =  0.8108447f; // Index 3 Stretched
        baseHp.muscles[75 + 8] = -0.5706741f; // Middle 1 Stretched
        baseHp.muscles[75 + 9] = -0.9387131f; // Middle Spread
        baseHp.muscles[75 + 10] = -1.2096846f; // Middle 2 Stretched
        baseHp.muscles[75 + 11] =  0.8109050f; // Middle 3 Stretched
        baseHp.muscles[75 + 12] = -0.8122700f; // Ring 1 Stretched
        baseHp.muscles[75 + 13] = -1.1390761f; // Ring Spread
        baseHp.muscles[75 + 14] = -1.6857924f; // Ring 2 Stretched
        baseHp.muscles[75 + 15] =  0.8109150f; // Ring 3 Stretched
        baseHp.muscles[75 + 16] = -0.6678960f; // Little 1 Stretched
        baseHp.muscles[75 + 17] = -0.7445285f; // Little Spread
        baseHp.muscles[75 + 18] = -1.2094172f; // Little 2 Stretched
        baseHp.muscles[75 + 19] =  0.8109943f; // Little 3 Stretched

        // 2. Both legs firmly grounded (Problem 3: Left foot floating / awkward stand)
        // Right leg: Straight, supporting leg
        baseHp.muscles[29] = 0.38f;   // Right Upper Leg Front-Back
        baseHp.muscles[30] = -0.15f;  // Right Upper Leg In-Out
        baseHp.muscles[31] = 0.00f;   // Right Upper Leg Twist
        baseHp.muscles[32] = 0.85f;   // Right Lower Leg Stretch
        baseHp.muscles[33] = 0.00f;   // Right Lower Leg Twist
        baseHp.muscles[34] = 0.04f;   // Right Foot Up-Down (flat)
        baseHp.muscles[35] = 0.00f;   // Right Foot Twist
        baseHp.muscles[36] = 0.00f;   // Right Toes Up-Down

        // Left leg: Relaxed, flat on floor, no floating heel
        baseHp.muscles[21] = 0.15f;   // Left Upper Leg Front-Back
        baseHp.muscles[22] = 0.10f;   // Left Upper Leg In-Out
        baseHp.muscles[23] = -0.05f;  // Left Upper Leg Twist
        baseHp.muscles[24] = 0.82f;   // Left Lower Leg Stretch
        baseHp.muscles[25] = 0.00f;   // Left Lower Leg Twist
        baseHp.muscles[26] = 0.04f;   // Left Foot Up-Down (flat on floor, zero float!)
        baseHp.muscles[27] = 0.00f;   // Left Foot Twist
        baseHp.muscles[28] = 0.00f;   // Left Toes Up-Down

        // 3. Left Thumb (Problem 2: Fix flipped thumb)
        baseHp.muscles[55] = -0.40f;  // Thumb 1 Stretched
        baseHp.muscles[56] = -0.85f;  // Thumb Spread (tuck inward along upper hip)
        baseHp.muscles[57] = -0.20f;  // Thumb 2 Stretched
        baseHp.muscles[58] = -0.10f;  // Thumb 3 Stretched

        // 4. Left Arm & Hand on Hip (Problem 1: Hand touching waist)
        baseHp.muscles[38] = -0.10f; // Shoulder Front-Back
        baseHp.muscles[39] = -0.28f; // Arm Down-Up
        baseHp.muscles[40] = 0.35f;  // Arm Front-Back (pull arm back towards body)
        baseHp.muscles[41] = -0.40f; // Arm Twist
        baseHp.muscles[42] = -0.15f; // Forearm stretch
        baseHp.muscles[43] = -0.25f; // Forearm twist
        baseHp.muscles[44] = -0.30f; // Hand Down-Up
        baseHp.muscles[45] = 0.15f;  // Hand In-Out

        // Left Fingers: Naturally draped along front hip
        baseHp.muscles[59] = 0.40f; baseHp.muscles[60] = -0.10f; baseHp.muscles[61] = 0.30f; baseHp.muscles[62] = 0.20f;
        baseHp.muscles[63] = 0.45f; baseHp.muscles[64] = 0.00f;  baseHp.muscles[65] = 0.35f; baseHp.muscles[66] = 0.20f;
        baseHp.muscles[67] = 0.50f; baseHp.muscles[68] = 0.05f;  baseHp.muscles[69] = 0.40f; baseHp.muscles[70] = 0.20f;
        baseHp.muscles[71] = 0.55f; baseHp.muscles[72] = 0.10f;  baseHp.muscles[73] = 0.45f; baseHp.muscles[74] = 0.20f;

        hphClean.SetHumanPose(ref baseHp);

        // Grounding adjustment
        float actualHs = wAnim.humanScale > 0.1f ? wAnim.humanScale : 5.8013f;
        float scaleEst = actualHs;
        float curMinY = GetMinMeshY(clean);
        baseHp.bodyPosition.y -= curMinY / scaleEst;
        hphClean.SetHumanPose(ref baseHp);

        Transform lf = FindChild(clean.transform, "LeftFoot");
        Transform rf = FindChild(clean.transform, "RightFoot");
        Transform lh = FindChild(clean.transform, "LeftHand");
        Transform rh = FindChild(clean.transform, "RightHand");

        Quaternion offsetFoot = new Quaternion(0.2421f, 0.6641f, -0.6647f, 0.2419f);
        Quaternion offsetLH = new Quaternion(-0.0976f, -0.0733f, -0.9796f, 0.1601f);
        Quaternion offsetRH = new Quaternion(0.0976f, -0.0733f, 0.9796f, 0.1601f);

        int totalFrames = 76; // 0..75 (2.500s @ 30fps)
        float clipDuration = 2.500000f;

        Debug.Log($"[ExportWindbladePose5] Starting export of {totalFrames} frames (duration={clipDuration:F3}s)...");

        string jsonPath = @"D:\Agent\tftf\build\windblade_anim_pose5_export.json";
        using (StreamWriter sw = new StreamWriter(jsonPath, false, Encoding.UTF8)) {
            sw.WriteLine("{");
            sw.WriteLine($"  \"duration\": {clipDuration:F6},");
            sw.WriteLine($"  \"sampleRate\": 30.0,");
            sw.WriteLine($"  \"frameCount\": {totalFrames},");
            sw.WriteLine($"  \"humanScale\": {actualHs:F6},");
            sw.WriteLine("  \"frames\": [");

            HumanPose hp = new HumanPose();

            for (int f = 0; f < totalFrames; f++) {
                float t = (float)f / 30.0f;
                float phase = 0.5f * (1.0f - Mathf.Cos(2.0f * Mathf.PI * t / clipDuration));

                // Clone base pose
                hp.bodyPosition = baseHp.bodyPosition;
                hp.bodyRotation = baseHp.bodyRotation;
                hp.muscles = (float[])baseHp.muscles.Clone();

                // Breathing modulation (subtle chest and shoulder rise)
                hp.muscles[0]  -= 0.004f * phase; // Spine Front-Back (attr 42)
                hp.muscles[3]  += 0.020f * phase; // Chest Front-Back (attr 45)
                hp.muscles[37] += 0.006f * phase; // Left Shoulder Down-Up (attr 79)
                hp.muscles[46] += 0.010f * phase; // Right Shoulder Down-Up (attr 88)

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

        Debug.Log($"[ExportWindbladePose5] Successfully saved {totalFrames} frames to {jsonPath}");

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
