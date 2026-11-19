using UnityEngine;
using UnityEditor;

public static class VerifySlipstreamAnimationPlayback {
    public static void Run() {
        string charBundlePath = @"D:\Agent\tftf\extracted_apk\assets\assetpack\characters\characters.assetbundle";
        string slipstreamBundlePath = @"D:\Agent\tftf\assets_redeco\slipstream_gs.assetbundle";

        AssetBundle.UnloadAllAssetBundles(true);
        AssetBundle charBundle = AssetBundle.LoadFromFile(charBundlePath);
        AssetBundle slipstreamBundle = AssetBundle.LoadFromFile(slipstreamBundlePath);

        GameObject prefab = null;
        foreach (var n in slipstreamBundle.GetAllAssetNames()) {
            if (n.EndsWith("_lw.prefab")) { prefab = slipstreamBundle.LoadAsset<GameObject>(n); break; }
        }

        GameObject inst = Object.Instantiate(prefab);
        inst.transform.position = Vector3.zero;
        inst.transform.rotation = Quaternion.identity;

        Animator anim = inst.GetComponent<Animator>();
        anim.applyRootMotion = false;

        Transform hips = FindChild(inst.transform, "Hips");
        Transform lf = FindChild(inst.transform, "LeftFoot");
        Transform rf = FindChild(inst.transform, "RightFoot");
        Transform lh = FindChild(inst.transform, "LeftHand");

        float minMeshY_overall = float.MaxValue;
        float maxMeshY_overall = float.MinValue;
        bool hasNaN = false;

        // Sample across the 4.433s animation in 0.2s increments (23 steps)
        for (int i = 0; i <= 22; i++) {
            float dt = (i == 0) ? 0.05f : 0.2f;
            anim.Update(dt);

            float minY = GetMinMeshY(inst);
            if (minY < minMeshY_overall) minMeshY_overall = minY;
            if (minY > maxMeshY_overall) maxMeshY_overall = minY;

            if (float.IsNaN(hips.position.y) || float.IsNaN(lf.position.y) || float.IsNaN(rf.position.y) || float.IsNaN(lh.position.y)) {
                hasNaN = true;
                Debug.LogError($"[VerifySlipstream] NaN detected at step {i}!");
                break;
            }

            if (i % 3 == 0) {
                Debug.Log(string.Format("[VerifySlipstream] Step {0} (t~{1:F1}s): HipsY={2:F3}, LF_Y={3:F3}, RF_Y={4:F3}, LH_Pos={5}, minMeshY={6:F4}",
                    i, i * 0.2f, hips.position.y, lf.position.y, rf.position.y, lh.position.ToString("F2"), minY));
            }
        }

        Debug.Log(string.Format("[VerifySlipstream SUMMARY] hasNaN={0}, minMeshY={1:F4}, maxMeshY={2:F4}",
            hasNaN, minMeshY_overall, maxMeshY_overall));

        Object.DestroyImmediate(inst);
        AssetBundle.UnloadAllAssetBundles(true);
        EditorApplication.Exit(hasNaN ? 1 : 0);
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
