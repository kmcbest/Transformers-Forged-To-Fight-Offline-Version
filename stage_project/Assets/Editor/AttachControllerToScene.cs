using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;

public class AttachControllerToScene {
    [MenuItem("TFTF/Attach Controller")]
    public static void Attach() {
        string scenePath = "Assets/Scenes/RustSea_Devastator_Stage.unity";
        EditorSceneManager.OpenScene(scenePath);

        GameObject dev = GameObject.Find("Devastator_Colossus");
        if (dev != null) {
            DevastatorStageController ctrl = dev.GetComponent<DevastatorStageController>();
            if (ctrl == null) ctrl = dev.AddComponent<DevastatorStageController>();
            ctrl.posX = 0.0f;
            ctrl.posY = 1.0f;
            ctrl.posZ = 26.0f;
            ctrl.scale = 550.0f;
            ctrl.rotY = 180.0f;
            ctrl.mode = DevastatorPoseMode.RobotIdle;
            ctrl.combineProgress = 100.0f;

            ctrl.ApplyTransform();
            ctrl.SampleCurrentPose();
            EditorUtility.SetDirty(dev);
        }

        EditorSceneManager.SaveOpenScenes();
        Debug.Log("[✓] Attached DevastatorStageController and saved scene!");
    }
}
