using UnityEngine;
using UnityEditor;
using System.IO;
using System.Text;

public static class ExportWindbladePose5Animation {
    public static void Run() {
        string repoRoot = Path.GetFullPath(Path.Combine(Application.dataPath, "..", ".."));
        string fbxPath = "Assets/Mixamo/pose_05_lhip_rdown.fbx";
        ModelImporter mi = AssetImporter.GetAtPath(fbxPath) as ModelImporter;
        if (mi != null && mi.animationType != ModelImporterAnimationType.Human) {
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

        mixAnim.enabled = false;
        clip.SampleAnimation(mixInst, 0f);
        HumanPoseHandler hphMix = new HumanPoseHandler(mixAnim.avatar, mixInst.transform);
        HumanPose baseHp = new HumanPose();
        hphMix.GetHumanPose(ref baseHp);
        Object.DestroyImmediate(mixInst);

        string bundlePath = Path.Combine(repoRoot, "backup", "windblade_gs.assetbundle.orig");
        if (!File.Exists(bundlePath)) {
            bundlePath = Path.Combine(repoRoot, "extracted_apk", "assets", "assetpack", "windblade_gs_odr", "windblade_gs.assetbundle");
        }
        AssetBundle.UnloadAllAssetBundles(true);
        AssetBundle bundle = AssetBundle.LoadFromFile(bundlePath);
        GameObject wPrefab = null;
        foreach (var n in bundle.GetAllAssetNames()) {
            if (n.EndsWith("_lw.prefab")) { wPrefab = bundle.LoadAsset<GameObject>(n); break; }
        }

        GameObject clean = Object.Instantiate(wPrefab);
        clean.transform.position = Vector3.zero;
        clean.transform.rotation = Quaternion.identity;
        Transform tr = clean.transform.Find("transformed");
        if (tr != null) tr.gameObject.SetActive(false);

        Animator wAnim = clean.GetComponent<Animator>();
        wAnim.enabled = false;
        Transform cleanCM = clean.transform.Find("character_model");
        HumanPoseHandler hphClean = new HumanPoseHandler(wAnim.avatar, cleanCM);

        // 1. Right hand authentic sword grip from Frontend_Sword_idle
        baseHp.muscles[75 + 0] = -1.5541633f;
        baseHp.muscles[75 + 1] = -2.1583767f;
        baseHp.muscles[75 + 2] = -0.2255878f;
        baseHp.muscles[75 + 3] = -0.4691082f;
        baseHp.muscles[75 + 4] = -0.5655559f;
        baseHp.muscles[75 + 5] = -0.7321508f;
        baseHp.muscles[75 + 6] = -1.2284926f;
        baseHp.muscles[75 + 7] =  0.8108447f;
        baseHp.muscles[75 + 8] = -0.5706741f;
        baseHp.muscles[75 + 9] = -0.9387131f;
        baseHp.muscles[75 + 10] = -1.2096846f;
        baseHp.muscles[75 + 11] =  0.8109050f;
        baseHp.muscles[75 + 12] = -0.8122700f;
        baseHp.muscles[75 + 13] = -1.1390761f;
        baseHp.muscles[75 + 14] = -1.6857924f;
        baseHp.muscles[75 + 15] =  0.8109150f;
        baseHp.muscles[75 + 16] = -0.6678960f;
        baseHp.muscles[75 + 17] = -0.7445285f;
        baseHp.muscles[75 + 18] = -1.2094172f;
        baseHp.muscles[75 + 19] =  0.8109943f;

        // 2. Fix Left Thumb + fingers, and rotate Left Arm back to rest hand cleanly on hip
        baseHp.muscles[38] =  0.20f; // Left Shoulder Front-Back (subtle natural backward posture)
        baseHp.muscles[39] = -0.32f; // Left Arm Down-Up (brings arm smoothly into hip)
        baseHp.muscles[40] =  0.54f; // Left Arm Front-Back (rotates arm backwards around shoulder so hand rests on waist!)
        baseHp.muscles[42] =  0.10f; // Left Forearm Stretch (gentle natural elbow bend)

        baseHp.muscles[55] = -0.35f; // Left Thumb 1 Stretched
        baseHp.muscles[56] =  0.45f; // Left Thumb Spread (keeps thumb on upper rim, NOT flipped under wrist!)
        baseHp.muscles[57] = -0.25f; // Left Thumb 2 Stretched
        baseHp.muscles[58] = -0.20f; // Left Thumb 3 Stretched

        baseHp.muscles[59] =  0.15f; // Left Index 1 Stretched
        baseHp.muscles[60] = -0.35f; // Left Index Spread
        baseHp.muscles[61] = -0.15f; // Left Index 2 Stretched
        baseHp.muscles[62] =  0.05f; // Left Index 3 Stretched

        // 3. Gently flatten ankles/toes so iKOnFeet=True plants both feet cleanly without plunging underground
        baseHp.muscles[24] = 0.56f; // Left Lower Leg Stretch
        baseHp.muscles[26] = 0.05f; // Left Foot Up-Down
        baseHp.muscles[27] = 0.05f; // Left Foot Twist In-Out
        baseHp.muscles[28] = 0.00f; // Left Toes Up-Down

        baseHp.muscles[34] = 0.04f; // Right Foot Up-Down
        baseHp.muscles[35] = 0.05f; // Right Foot Twist In-Out
        baseHp.muscles[36] = 0.00f; // Right Toes Up-Down

        hphClean.SetHumanPose(ref baseHp);

        float actualHs = wAnim.humanScale > 0.1f ? wAnim.humanScale : 5.8013f;
        float curMinY = GetMinMeshY(clean);
        baseHp.bodyPosition.y -= curMinY / actualHs;
        hphClean.SetHumanPose(ref baseHp);

        Transform lf = FindChild(clean.transform, "LeftFoot");
        Transform rf = FindChild(clean.transform, "RightFoot");
        Transform lh = FindChild(clean.transform, "LeftHand");
        Transform rh = FindChild(clean.transform, "RightHand");

        Quaternion offsetFoot = new Quaternion(0.2421f, 0.6641f, -0.6647f, 0.2419f);
        Quaternion offsetLH = new Quaternion(-0.0976f, -0.0733f, -0.9796f, 0.1601f);
        Quaternion offsetRH = new Quaternion(0.0976f, -0.0733f, 0.9796f, 0.1601f);

        int totalFrames = 77; // 0..76 (0..75 = 2.500s @ 30fps, frame 76 = 2.533s / sample +1 for hermite evaluation)
        float clipDuration = 2.500000f;

        string jsonPath = Path.Combine(repoRoot, "build", "windblade_anim_pose5_export.json");
        Directory.CreateDirectory(Path.GetDirectoryName(jsonPath));

        using (StreamWriter sw = new StreamWriter(jsonPath, false, Encoding.UTF8)) {
            sw.WriteLine("{");
            sw.WriteLine($"  \"duration\": {clipDuration:F6},");
            sw.WriteLine($"  \"sampleRate\": 30.0,");
            sw.WriteLine($"  \"frameCount\": {totalFrames},");
            sw.WriteLine($"  \"humanScale\": {actualHs:F6},");
            sw.WriteLine("  \"frames\": [");

            HumanPose hp = new HumanPose();
            for (int f = 0; f < totalFrames; f++) {
                float evalT = (f == 76) ? (1.0f / 30.0f) : ((float)f / 30.0f);
                float phase = 0.5f * (1.0f - Mathf.Cos(2.0f * Mathf.PI * evalT / clipDuration));
                float sway = Mathf.Sin(2.0f * Mathf.PI * evalT / clipDuration) * phase;

                hp.bodyPosition = baseHp.bodyPosition;
                hp.bodyRotation = baseHp.bodyRotation;
                hp.muscles = (float[])baseHp.muscles.Clone();

                // Subtle seamless living breathing & head poise (both value AND derivative are strictly 0 at seams)
                hp.muscles[0]  -= 0.005f * phase;
                hp.muscles[3]  += 0.022f * phase;
                hp.muscles[6]  += 0.015f * phase;
                hp.muscles[12] += 0.012f * phase;
                hp.muscles[14] += 0.015f * sway;
                hp.muscles[37] += 0.008f * phase;
                hp.muscles[46] += 0.012f * phase;
                hp.muscles[48] -= 0.010f * phase;
                hp.muscles[51] += 0.012f * phase;

                hphClean.SetHumanPose(ref hp);

                Vector3 bodyWorldPos = hp.bodyPosition * actualHs;
                Quaternion invBodyRot = Quaternion.Inverse(hp.bodyRotation);

                // Match official Frontend_Sword_idle grounding (minMeshY ~ -0.15m)
                Vector3 lfGoalWorld = new Vector3(lf.position.x, 0.21f, lf.position.z);
                Vector3 rfGoalWorld = new Vector3(rf.position.x, 0.21f, rf.position.z);

                Vector3 lfT = invBodyRot * ((lfGoalWorld - bodyWorldPos) / actualHs);
                Quaternion lfQ = invBodyRot * (lf.rotation * offsetFoot);
                Vector3 rfT = invBodyRot * ((rfGoalWorld - bodyWorldPos) / actualHs);
                Quaternion rfQ = invBodyRot * (rf.rotation * offsetFoot);

                Vector3 lhT = invBodyRot * ((lh.position - bodyWorldPos) / actualHs);
                Quaternion lhQ = invBodyRot * (lh.rotation * offsetLH);
                Vector3 rhT = invBodyRot * ((rh.position - bodyWorldPos) / actualHs);
                Quaternion rhQ = invBodyRot * (rh.rotation * offsetRH);

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
        AssetBundle.UnloadAllAssetBundles(true);
        EditorApplication.Exit(0);
    }

    private static float GetMinMeshY(GameObject inst) {
        float minY = float.MaxValue;
        foreach (var smr in inst.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
            if (!smr.enabled || !smr.gameObject.activeInHierarchy) continue;
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
