using System;
using System.IO;
using UnityEngine;
using UnityEditor;

public class ProbeCombinerImports {
    public static void Probe() {
        Debug.Log("=== Starting Combiner FBX Probe ===");

        string volcPath = "Assets/Combiners/Volcanicus/Volcanicus_PingPong.fbx";
        string vicPath = "Assets/Combiners/Victorion/Victorion_PingPong.fbx";

        ProbeOne(volcPath, "Volcanicus");
        ProbeOne(vicPath, "Victorion");

        Debug.Log("=== Combiner FBX Probe Complete ===");
    }

    private static void ProbeOne(string fbxPath, string name) {
        Debug.Log($"--- Probing {name} at {fbxPath} ---");
        ModelImporter importer = AssetImporter.GetAtPath(fbxPath) as ModelImporter;
        if (importer != null) {
            Debug.Log($"  Animation Type: {importer.animationType}, ImportAnim: {importer.importAnimation}");
            importer.animationType = ModelImporterAnimationType.Generic;
            importer.importAnimation = true;
            importer.SaveAndReimport();
        }

        GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
        if (prefab == null) {
            Debug.LogError($"  Failed to load prefab at {fbxPath}");
            return;
        }

        GameObject instance = UnityEngine.Object.Instantiate(prefab);
        Bounds b = new Bounds(instance.transform.position, Vector3.zero);
        Renderer[] rends = instance.GetComponentsInChildren<Renderer>();
        Debug.Log($"  Found {rends.Length} renderers in {name}:");
        foreach (var r in rends) {
            b.Encapsulate(r.bounds);
            Debug.Log($"    Renderer: {r.gameObject.name}, bounds={r.bounds.size}, center={r.bounds.center}");
        }
        Debug.Log($"  Combined Total Bounds Size: {b.size}, Center: {b.center}");

        // List AnimationClips
        UnityEngine.Object[] assets = AssetDatabase.LoadAllAssetsAtPath(fbxPath);
        Debug.Log($"  Loaded {assets.Length} sub-assets for {name}:");
        foreach (var a in assets) {
            if (a is AnimationClip && !a.name.StartsWith("__preview__")) {
                AnimationClip clip = a as AnimationClip;
                Debug.Log($"    Clip: '{clip.name}', length={clip.length}s, isLooping={clip.isLooping}");
            }
        }

        UnityEngine.Object.DestroyImmediate(instance);
    }
}
