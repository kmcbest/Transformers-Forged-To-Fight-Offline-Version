using UnityEngine;
using UnityEditor;

[CustomEditor(typeof(DevastatorStageController))]
public class DevastatorStageControllerEditor : Editor {
    public override void OnInspectorGUI() {
        DevastatorStageController ctrl = (DevastatorStageController)target;

        GUILayout.Label("=== 大力神背景观战与合体实时控制器 ===", EditorStyles.boldLabel);
        EditorGUILayout.Space(5);

        EditorGUI.BeginChangeCheck();

        // 1. 模式切换
        EditorGUILayout.LabelField("【当前形态与动作模式】", EditorStyles.boldLabel);
        ctrl.mode = (DevastatorPoseMode)EditorGUILayout.EnumPopup("展示模式", ctrl.mode);

        if (ctrl.mode == DevastatorPoseMode.RobotIdle) {
            EditorGUILayout.HelpBox("当前处于【完整合体待机】模式：大力神 100% 紧密咬合就位，无任何浮空与缝隙！", MessageType.Info);
        } else {
            EditorGUILayout.HelpBox("当前处于【合体过程演绎】模式：拉动下方滑块可自由预览挖地虎变形拼合过程。", MessageType.None);
            ctrl.combineProgress = EditorGUILayout.Slider("合体进度 (0%~100%)", ctrl.combineProgress, 0.0f, 100.0f);
        }

        EditorGUILayout.Space(5);
        EditorGUILayout.BeginHorizontal();
        if (GUILayout.Button("一键 100% 完整合体站姿", GUILayout.Height(30))) {
            ctrl.mode = DevastatorPoseMode.RobotIdle;
            ctrl.combineProgress = 100.0f;
            ctrl.SampleCurrentPose();
        }
        if (GUILayout.Button("合体起始状态 (各车散开)", GUILayout.Height(30))) {
            ctrl.mode = DevastatorPoseMode.CombineProcess;
            ctrl.combineProgress = 0.0f;
            ctrl.SampleCurrentPose();
        }
        EditorGUILayout.EndHorizontal();

        EditorGUILayout.Space(15);
        EditorGUILayout.LabelField("【空间位置与尺寸调整】", EditorStyles.boldLabel);
        ctrl.posX = EditorGUILayout.Slider("左右偏移 (X)", ctrl.posX, -25.0f, 25.0f);
        ctrl.posY = EditorGUILayout.Slider("高度 (Y)", ctrl.posY, -5.0f, 20.0f);
        ctrl.posZ = EditorGUILayout.Slider("景深距离 (Z)", ctrl.posZ, 10.0f, 60.0f);
        ctrl.scale = EditorGUILayout.Slider("体型缩放 (Scale)", ctrl.scale, 100.0f, 1000.0f);
        ctrl.rotY = EditorGUILayout.Slider("水平朝向 (Rot Y)", ctrl.rotY, 0.0f, 360.0f);

        if (EditorGUI.EndChangeCheck()) {
            Undo.RecordObject(ctrl.transform, "Tweak Devastator Stage");
            ctrl.ApplyTransform();
            ctrl.SampleCurrentPose();
            EditorUtility.SetDirty(ctrl);
        }

        EditorGUILayout.Space(15);
        EditorGUILayout.LabelField("【摄像机预设视角切换】", EditorStyles.boldLabel);
        EditorGUILayout.BeginHorizontal();
        if (GUILayout.Button("百炼为战实机视角")) {
            ctrl.SetCameraCombat();
        }
        if (GUILayout.Button("全景仰视巨神兵视角")) {
            ctrl.SetCameraColossus();
        }
        EditorGUILayout.EndHorizontal();
    }
}
