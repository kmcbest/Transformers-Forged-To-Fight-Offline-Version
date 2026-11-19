using UnityEngine;
using UnityEditor;

public static class VerifyPatchedAnimationPlayback {
    public static void Run() {
        string charBundlePath = @"D:\Agent\tftf\extracted_apk\assets\assetpack\characters\characters.assetbundle";
        string chromiaBundlePath = @"D:\Agent\tftf\assets_redeco\chromia_gs_kabam.assetbundle";

        AssetBundle.UnloadAllAssetBundles(true);
        AssetBundle charBundle = AssetBundle.LoadFromFile(charBundlePath);
        AssetBundle chromiaBundle = AssetBundle.LoadFromFile(chromiaBundlePath);

        GameObject prefab = null;
        foreach (var n in chromiaBundle.GetAllAssetNames()) {
            if (n.EndsWith("_lw.prefab")) { prefab = chromiaBundle.LoadAsset<GameObject>(n); break; }
        }

        GameObject inst = Object.Instantiate(prefab);
        inst.transform.position = Vector3.zero;
        inst.transform.rotation = Quaternion.identity;

        Animator anim = inst.GetComponent<Animator>();
        anim.applyRootMotion = false;

        Transform hips = FindChild(inst.transform, "Hips");
        Transform lf = FindChild(inst.transform, "LeftFoot");
        Transform rf = FindChild(inst.transform, "RightFoot");

        float minMeshY_overall = float.MaxValue;
        float maxMeshY_overall = float.MinValue;
        bool hasNaN = false;

        // Sample across the 19.167s animation in 0.5s increments (38 steps)
        for (int i = 0; i <= 38; i++) {
            float dt = (i == 0) ? 0.05f : 0.5f;
            anim.Update(dt);

            float minY = GetMinMeshY(inst);
            if (minY < minMeshY_overall) minMeshY_overall = minY;
            if (minY > maxMeshY_overall) maxMeshY_overall = minY;

            if (float.IsNaN(hips.position.y) || float.IsNaN(lf.position.y) || float.IsNaN(rf.position.y)) {
                hasNaN = true;
                Debug.LogError($"[VerifyPlayback] NaN detected at step {i}!");
                break;
            }

            if (i % 5 == 0) {
                Debug.Log(string.Format("[VerifyPlayback] Step {0} (t~{1:F1}s): HipsY={2:F3}, LF_Y={3:F3}, RF_Y={4:F3}, minMeshY={5:F4}",
                    i, i * 0.5f, hips.position.y, lf.position.y, rf.position.y, minY));
            }
        }

        Debug.Log(string.Format("[VerifyPlayback SUMMARY] hasNaN={0}, minMeshY={1:F4}, maxMeshY={2:F4}",
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
