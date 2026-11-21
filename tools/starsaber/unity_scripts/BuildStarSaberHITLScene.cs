using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class BuildStarSaberHITLScene {
    private const string ROBOT_FBX = "Assets/StarSaber/starsaber_hitl_robot.fbx";
    private const string SWORD_FBX = "Assets/StarSaber/starsaber_hitl_sword.fbx";
    private const string SCENE_PATH = "Assets/Scenes/StarSaber_Sword_HITL.unity";
    private const string MAT_MAIN_PATH = "Assets/StarSaber/cha_starsaber_main.mat";
    private const string MAT_WPNS_PATH = "Assets/StarSaber/cha_starsaber_wpns.mat";

    [MenuItem("TFTF/StarSaber - Build & Open Sword HITL Tuning Scene (打开史达握剑调优场景)", false, 10)]
    public static void BuildScene() {
        Debug.Log("=== [StarSaber] Building HITL Sword & Grip Tuning Scene (v2 Fixed Knuckle Pivots) ===");

        var robotMi = AssetImporter.GetAtPath(ROBOT_FBX) as ModelImporter;
        if (robotMi != null) {
            robotMi.isReadable = true;
            robotMi.useFileScale = true;
            robotMi.globalScale = 1.0f;
            robotMi.animationType = ModelImporterAnimationType.Generic;
            robotMi.importNormals = ModelImporterNormals.Import;
            robotMi.importTangents = ModelImporterTangents.CalculateMikk;
            robotMi.SaveAndReimport();
        }

        var swordMi = AssetImporter.GetAtPath(SWORD_FBX) as ModelImporter;
        if (swordMi != null) {
            swordMi.isReadable = true;
            swordMi.useFileScale = true;
            swordMi.globalScale = 1.0f;
            swordMi.animationType = ModelImporterAnimationType.None;
            swordMi.importNormals = ModelImporterNormals.Import;
            swordMi.importTangents = ModelImporterTangents.CalculateMikk;
            swordMi.SaveAndReimport();
        }

        AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);

        Material matMain = AssetDatabase.LoadAssetAtPath<Material>(MAT_MAIN_PATH);
        Material matWpns = AssetDatabase.LoadAssetAtPath<Material>(MAT_WPNS_PATH);

        Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        // Stage Floor
        GameObject floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
        floor.name = "Stage Floor";
        floor.transform.position = Vector3.zero;
        floor.transform.localScale = new Vector3(3f, 1f, 3f);
        Material floorMat = new Material(Shader.Find("Standard"));
        floorMat.color = new Color(0.18f, 0.20f, 0.24f);
        floorMat.SetFloat("_Glossiness", 0.4f);
        floor.GetComponent<Renderer>().sharedMaterial = floorMat;

        // 3-Point Studio Lighting
        GameObject keyLightGo = new GameObject("Key Light (Front)");
        Light keyLight = keyLightGo.AddComponent<Light>();
        keyLight.type = LightType.Directional;
        keyLight.intensity = 1.3f;
        keyLight.color = new Color(1.0f, 0.96f, 0.90f);
        keyLightGo.transform.rotation = Quaternion.Euler(35f, 140f, 0f);

        GameObject fillLightGo = new GameObject("Fill Light (Right)");
        Light fillLight = fillLightGo.AddComponent<Light>();
        fillLight.type = LightType.Directional;
        fillLight.intensity = 0.8f;
        fillLight.color = new Color(0.85f, 0.90f, 1.0f);
        fillLightGo.transform.rotation = Quaternion.Euler(20f, -40f, 0f);

        GameObject rimLightGo = new GameObject("Rim Light (Back)");
        Light rimLight = rimLightGo.AddComponent<Light>();
        rimLight.type = LightType.Directional;
        rimLight.intensity = 1.1f;
        rimLight.color = new Color(0.9f, 0.95f, 1.0f);
        rimLightGo.transform.rotation = Quaternion.Euler(15f, 0f, 0f);

        // Instantiate Robot
        GameObject robotPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(ROBOT_FBX);
        if (robotPrefab == null) {
            Debug.LogError("[StarSaber] Failed to load " + ROBOT_FBX);
            return;
        }
        GameObject robotInst = Object.Instantiate(robotPrefab);
        robotInst.name = "StarSaber_Candidate";
        robotInst.transform.position = Vector3.zero;
        robotInst.transform.rotation = Quaternion.identity;

        SkinnedMeshRenderer robotSmr = robotInst.GetComponentInChildren<SkinnedMeshRenderer>(true);
        if (robotSmr != null && matMain != null) {
            robotSmr.sharedMaterial = matMain;
            robotSmr.updateWhenOffscreen = true;
        }

        // Instantiate Sword under RightHand
        GameObject swordPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(SWORD_FBX);
        if (swordPrefab == null) {
            Debug.LogError("[StarSaber] Failed to load " + SWORD_FBX);
            return;
        }

        Transform rightHand = null;
        foreach (var t in robotInst.GetComponentsInChildren<Transform>(true)) {
            if (t.name == "RightHand") {
                rightHand = t;
                break;
            }
        }

        GameObject swordInst = Object.Instantiate(swordPrefab);
        swordInst.name = "StarSaberSword";
        if (rightHand != null) {
            swordInst.transform.SetParent(rightHand, false);
        } else {
            swordInst.transform.SetParent(robotInst.transform, false);
        }

        MeshRenderer swordMr = swordInst.GetComponentInChildren<MeshRenderer>(true);
        if (swordMr != null && matWpns != null) {
            swordMr.sharedMaterial = matWpns;
        }

        // Attach StarSaberGripStudio & capture clean open rest pose before applying initial grip
        var studio = robotInst.AddComponent<StarSaberGripStudio>();
        studio.robotSmr = robotSmr;
        studio.swordTransform = swordInst.transform;
        studio.swordMeshFilter = swordInst.GetComponentInChildren<MeshFilter>(true);
        studio.CaptureRestPose(false);
        studio.ApplyHeroicGripPreset();

        // Setup Grip Camera focused directly on the palm center
        GameObject camGo = new GameObject("Grip Camera");
        Camera cam = camGo.AddComponent<Camera>();
        cam.tag = "MainCamera";
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color(0.12f, 0.14f, 0.18f);

        Vector3 palmPos = studio.GetPalmWorldCenter();
        camGo.transform.position = palmPos + new Vector3(1.1f, 0.35f, 1.5f);
        camGo.transform.LookAt(palmPos);

        EditorSceneManager.SaveScene(scene, SCENE_PATH);
        Debug.Log("[✓] HITL Scene built and saved to " + SCENE_PATH);

        Selection.activeGameObject = robotInst;
        if (SceneView.lastActiveSceneView != null) {
            SceneView.lastActiveSceneView.LookAt(palmPos, Quaternion.Euler(18f, 145f, 0f), 1.8f);
        }
    }
}
