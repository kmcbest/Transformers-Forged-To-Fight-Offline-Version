using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEditor;
using UnityEditor.Animations;

public class GeneratePingPongAnimation {
    [MenuItem("TFTF/Generate Ping-Pong Animation")]
    public static void Generate() {
        Debug.Log("=== Starting Generation of Devastator Ping-Pong Animation ===");
        
        string fbxPath = "Assets/Devastator/Devastator.fbx";
        Object[] assets = AssetDatabase.LoadAllAssetsAtPath(fbxPath);
        AnimationClip srcClip = null;
        foreach (var obj in assets) {
            if (obj is AnimationClip clip && clip.name == "Devastator_Combine") {
                srcClip = clip;
                break;
            }
        }

        if (srcClip == null) {
            Debug.LogError("Source AnimationClip 'Devastator_Combine' not found in FBX!");
            return;
        }

        Debug.Log($"Found source clip: length={srcClip.length:F4}s, frameRate={srcClip.frameRate}");
        float fwdDuration = srcClip.length; // ~6.3667s (192 frames at 30fps)
        float holdCombined = 1.6667f;       // 50 frames hold at combined Devastator pose
        float revDuration = fwdDuration;    // 6.3667s reverse disassemble back to vehicles
        float holdStart = 0.5000f;          // 15 frames rest at start separated pose
        float totalDuration = fwdDuration + holdCombined + revDuration + holdStart;

        Debug.Log($"Phase 1 (Forward):   0.0000s -> {fwdDuration:F4}s");
        Debug.Log($"Phase 2 (Hold Dev):  {fwdDuration:F4}s -> {fwdDuration + holdCombined:F4}s");
        Debug.Log($"Phase 3 (Reverse):   {fwdDuration + holdCombined:F4}s -> {fwdDuration + holdCombined + revDuration:F4}s");
        Debug.Log($"Phase 4 (Rest Start):{fwdDuration + holdCombined + revDuration:F4}s -> {totalDuration:F4}s");
        Debug.Log($"Total Cycle Time:    {totalDuration:F4}s (~{totalDuration * 30f:F0} frames at 30fps)");

        // Create new AnimationClip
        AnimationClip newClip = new AnimationClip();
        newClip.name = "Devastator_Combine_PingPong";
        newClip.frameRate = srcClip.frameRate;

        EditorCurveBinding[] bindings = AnimationUtility.GetCurveBindings(srcClip);
        Debug.Log($"Processing {bindings.Length} curve bindings...");

        int processedCurves = 0;
        foreach (var binding in bindings) {
            AnimationCurve origCurve = AnimationUtility.GetEditorCurve(srcClip, binding);
            if (origCurve == null || origCurve.keys.Length == 0) continue;

            Keyframe[] origKeys = origCurve.keys;
            int n = origKeys.Length;

            List<Keyframe> pingPongKeys = new List<Keyframe>();

            // Phase 1: Forward
            for (int i = 0; i < n; i++) {
                Keyframe k = origKeys[i];
                if (i == n - 1) {
                    // Smooth transition into hold pose: outTangent = 0
                    k.outTangent = 0f;
                }
                pingPongKeys.Add(k);
            }

            // Phase 2: Hold Combined Pose
            Keyframe holdDevKey = new Keyframe(
                time: fwdDuration + holdCombined,
                value: origKeys[n - 1].value,
                inTangent: 0f,
                outTangent: -origKeys[n - 1].inTangent
            );
            holdDevKey.weightedMode = origKeys[n - 1].weightedMode;
            pingPongKeys.Add(holdDevKey);

            // Phase 3: Reverse
            // Mirror from n-2 down to 0
            for (int j = n - 2; j >= 0; j--) {
                Keyframe origK = origKeys[j];
                float revTime = fwdDuration + holdCombined + (fwdDuration - origK.time);
                float revVal = origK.value;
                float revInTan = -origK.outTangent;
                float revOutTan = -origK.inTangent;

                if (j == 0) {
                    // Transition to rest pose: outTangent = 0
                    revOutTan = 0f;
                }

                Keyframe revKey = new Keyframe(revTime, revVal, revInTan, revOutTan);
                revKey.weightedMode = origK.weightedMode;
                pingPongKeys.Add(revKey);
            }

            // Phase 4: Rest / Pause at Start Pose
            Keyframe restStartKey = new Keyframe(
                time: totalDuration,
                value: origKeys[0].value,
                inTangent: 0f,
                outTangent: origKeys[0].outTangent
            );
            restStartKey.weightedMode = origKeys[0].weightedMode;
            pingPongKeys.Add(restStartKey);

            AnimationCurve newCurve = new AnimationCurve(pingPongKeys.ToArray());
            AnimationUtility.SetEditorCurve(newClip, binding, newCurve);
            processedCurves++;
        }

        Debug.Log($"Successfully built {processedCurves} ping-pong curves!");

        // Clip Settings
        AnimationClipSettings settings = AnimationUtility.GetAnimationClipSettings(newClip);
        settings.loopTime = true;
        settings.keepOriginalOrientation = true;
        settings.keepOriginalPositionY = true;
        settings.keepOriginalPositionXZ = true;
        AnimationUtility.SetAnimationClipSettings(newClip, settings);
        newClip.wrapMode = WrapMode.Loop;

        // Save clip asset
        string outClipPath = "Assets/Devastator/Devastator_Combine_PingPong.anim";
        if (File.Exists(outClipPath)) {
            AssetDatabase.DeleteAsset(outClipPath);
        }
        AssetDatabase.CreateAsset(newClip, outClipPath);
        AssetDatabase.SaveAssets();
        Debug.Log($"[✓] Saved new AnimationClip to: {outClipPath}");

        // Update AnimatorController
        string controllerPath = "Assets/Devastator/Devastator_CombineController.controller";
        AnimatorController ac = AssetDatabase.LoadAssetAtPath<AnimatorController>(controllerPath);
        if (ac != null && ac.layers.Length > 0) {
            var stateMachine = ac.layers[0].stateMachine;
            foreach (var childState in stateMachine.states) {
                if (childState.state.name == "Combining_Loop") {
                    childState.state.motion = newClip;
                    Debug.Log($"[✓] Updated AnimatorController state '{childState.state.name}' motion to Devastator_Combine_PingPong!");
                    break;
                }
            }
            EditorUtility.SetDirty(ac);
            AssetDatabase.SaveAssets();
        } else {
            Debug.LogError($"Failed to load AnimatorController at {controllerPath}");
        }

        Debug.Log("=== Devastator Ping-Pong Animation Generation COMPLETE ===");
    }
}
