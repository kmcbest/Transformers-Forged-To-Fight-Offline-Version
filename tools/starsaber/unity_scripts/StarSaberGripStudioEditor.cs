using UnityEditor;
using UnityEngine;

[CustomEditor(typeof(StarSaberGripStudio))]
public class StarSaberGripStudioEditor : Editor {
    [MenuItem("TFTF/StarSaber - 烘焙当前场景已调好的握剑姿势 (Bake Current Scene Grip)", false, 11)]
    public static void BakeCurrentSceneGripMenu() {
        var studio = Object.FindObjectOfType<StarSaberGripStudio>();
        if (studio == null) {
            EditorUtility.DisplayDialog("未找到组件", "当前打开的场景中未找到挂载 StarSaberGripStudio 的对象（请先打开 StarSaber_Sword_HITL.unity）。", "确定");
            return;
        }
        Selection.activeGameObject = studio.gameObject;
        studio.BakeAndSaveGrip();
        EditorUtility.DisplayDialog("烘焙完成", "已将当前场景中调好的右手握姿与王者之剑烘焙到:\nAssets/StarSaber/cha_jetfire_gs_leader2014_00.asset\n与\nAssets/StarSaber/starsaber_grip_config.json", "太好了");
    }

    private void OnSceneGUI() {
        StarSaberGripStudio studio = (StarSaberGripStudio)target;
        if (studio == null) return;

        DrawChain(new[] { studio.thumb1, studio.thumb2, studio.thumb3 }, Color.cyan);
        DrawChain(new[] { studio.index1, studio.index2, studio.index3 }, Color.yellow);
        DrawChain(new[] { studio.fingers1, studio.fingers2, studio.fingers3 }, Color.green);

        if (studio.swordTransform != null) {
            Handles.color = new Color(1.0f, 0.35f, 0.2f, 0.9f);
            Handles.SphereHandleCap(0, studio.swordTransform.position, Quaternion.identity, 0.08f, EventType.Repaint);
        }
    }

    private void DrawChain(Transform[] chain, Color col) {
        if (chain == null || chain.Length == 0) return;
        Handles.color = col;
        for (int i = 0; i < chain.Length; i++) {
            if (chain[i] == null) continue;
            Handles.SphereHandleCap(0, chain[i].position, Quaternion.identity, 0.045f, EventType.Repaint);
            if (i + 1 < chain.Length && chain[i + 1] != null) {
                Handles.DrawAAPolyLine(3.0f, chain[i].position, chain[i + 1].position);
            }
        }
    }

    public override void OnInspectorGUI() {
        StarSaberGripStudio studio = (StarSaberGripStudio)target;

        EditorGUILayout.Space(8);
        GUIStyle titleStyle = new GUIStyle(EditorStyles.boldLabel) {
            fontSize = 15,
            alignment = TextAnchor.MiddleCenter
        };
        EditorGUILayout.LabelField("=== 史达 (Star Saber) 握剑姿态 HITL 调整台 ===", titleStyle);

        // Put the prominent Bake & Save button right at the TOP so it is always visible without scrolling!
        EditorGUILayout.Space(8);
        GUI.backgroundColor = new Color(0.22f, 0.92f, 0.36f);
        GUIStyle bakeBtnStyle = new GUIStyle(GUI.skin.button) {
            fontSize = 14,
            fontStyle = FontStyle.Bold
        };
        if (GUILayout.Button("💾 烘焙并保存握剑姿势到 54 骨 Mesh 资产 (Bake & Save)", bakeBtnStyle, GUILayout.Height(46))) {
            studio.BakeAndSaveGrip();
        }
        GUI.backgroundColor = Color.white;
        EditorGUILayout.Space(8);

        EditorGUILayout.HelpBox(
            "操作指引：\n" +
            "1. 选中层级最顶层的 StarSaber_Candidate 即可在本面板看到绿色烘焙按钮（也可直接点顶部菜单 TFTF -> StarSaber - 烘焙当前场景已调好的握剑姿势）。\n" +
            "2. 下方滑块可实时屈指；也可点击【一键选中】用 Scene Gizmo (W 移动 / E 旋转) 精调剑或指节。\n" +
            "3. 调好后点击上方绿色按钮即可导出游戏可用的 54 骨标准 Mesh 资产！",
            MessageType.Info);

        EditorGUILayout.Space(6);
        EditorGUILayout.LabelField("【快捷预设】", EditorStyles.boldLabel);
        EditorGUILayout.BeginHorizontal();
        GUI.backgroundColor = new Color(0.4f, 0.85f, 1.0f);
        if (GUILayout.Button("⚔️ 应用英雄握剑预设 (Heroic Grip)", GUILayout.Height(30))) {
            Undo.RecordObject(studio, "Apply Heroic Grip Preset");
            studio.ApplyHeroicGripPreset();
            EditorUtility.SetDirty(studio);
        }
        GUI.backgroundColor = new Color(1.0f, 0.72f, 0.72f);
        if (GUILayout.Button("✋ 重置为张手静止态 (Open Hand)", GUILayout.Height(30))) {
            Undo.RecordObject(studio, "Reset Open Hand");
            studio.ResetToOpenHand();
            EditorUtility.SetDirty(studio);
        }
        EditorGUILayout.EndHorizontal();

        EditorGUILayout.Space(6);
        GUI.backgroundColor = Color.white;
        EditorGUILayout.LabelField("【一键选中与视口聚焦】", EditorStyles.boldLabel);
        EditorGUILayout.BeginHorizontal();
        if (GUILayout.Button("🔍 聚焦右手掌与剑", GUILayout.Height(25))) {
            FocusCameraOnHand(studio);
        }
        if (GUILayout.Button("👤 全身视角", GUILayout.Height(25))) {
            FocusCameraOnBody(studio);
        }
        if (GUILayout.Button("🗡️ 选中王者之剑", GUILayout.Height(25)) && studio.swordTransform != null) {
            Selection.activeTransform = studio.swordTransform;
        }
        EditorGUILayout.EndHorizontal();

        EditorGUILayout.BeginHorizontal();
        if (GUILayout.Button("👍 选中大拇指 (Hand_R_1)") && studio.thumb1 != null) Selection.activeTransform = studio.thumb1;
        if (GUILayout.Button("☝️ 选中食指 (Hand_R_2)") && studio.index1 != null) Selection.activeTransform = studio.index1;
        if (GUILayout.Button("✊ 选中三指 (Hand_R_3)") && studio.fingers1 != null) Selection.activeTransform = studio.fingers1;
        EditorGUILayout.EndHorizontal();

        EditorGUILayout.Space(8);
        DrawDefaultInspector();
    }

    private void FocusCameraOnHand(StarSaberGripStudio studio) {
        Vector3 palm = studio.GetPalmWorldCenter();
        if (SceneView.lastActiveSceneView != null) {
            SceneView.lastActiveSceneView.LookAt(palm, Quaternion.Euler(18f, 145f, 0f), 1.6f);
        }
    }

    private void FocusCameraOnBody(StarSaberGripStudio studio) {
        if (SceneView.lastActiveSceneView != null) {
            SceneView.lastActiveSceneView.LookAt(studio.transform.position + Vector3.up * 6.0f, Quaternion.Euler(12f, 180f, 0f), 14.0f);
        }
    }
}
