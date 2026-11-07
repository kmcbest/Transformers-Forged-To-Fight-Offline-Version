using UnityEngine;
#if UNITY_EDITOR
using UnityEditor;
#endif

public enum DevastatorPoseMode {
    CombineProcess,  // 合体过程 (0%~100%)
    RobotIdle        // 完整合体霸气待机
}

[ExecuteInEditMode]
public class DevastatorStageController : MonoBehaviour {
    [Header("姿态与动作模式")]
    public DevastatorPoseMode mode = DevastatorPoseMode.RobotIdle;

    [Range(0f, 100f)]
    [Tooltip("合体进度百分比：0%各车就位 -> 100%完全合体锁死")]
    public float combineProgress = 100.0f;

    [Header("空间位置与尺寸")]
    [Range(-25f, 25f)] public float posX = 0.0f;
    [Range(-5f, 20f)] public float posY = 1.0f;
    [Range(10f, 60f)] public float posZ = 26.0f;
    [Range(100f, 1000f)] public float scale = 550.0f;
    [Range(0f, 360f)] public float rotY = 180.0f;

    public AnimationClip combineClip;
    public AnimationClip idleClip;

    private void OnEnable() {
        FindClips();
        ApplyTransform();
        SampleCurrentPose();
    }

    public void FindClips() {
#if UNITY_EDITOR
        Object[] assets = AssetDatabase.LoadAllAssetsAtPath("Assets/Devastator/Devastator.fbx");
        foreach (var a in assets) {
            if (a is AnimationClip) {
                if (a.name.Equals("Devastator_Combine", System.StringComparison.OrdinalIgnoreCase)) {
                    combineClip = a as AnimationClip;
                } else if (a.name.Equals("Devastator_Idle", System.StringComparison.OrdinalIgnoreCase)) {
                    idleClip = a as AnimationClip;
                }
            }
        }
#endif
    }

    public void ApplyTransform() {
        transform.position = new Vector3(posX, posY, posZ);
        transform.localScale = new Vector3(scale, scale, scale);
        transform.rotation = Quaternion.Euler(0.0f, rotY, 0.0f);
    }

    public void SampleAnimation() {
        SampleCurrentPose();
    }

    public void SampleCurrentPose() {
        FindClips();
        if (mode == DevastatorPoseMode.RobotIdle) {
            if (idleClip != null) {
                idleClip.SampleAnimation(gameObject, 0.0f);
            } else if (combineClip != null) {
                combineClip.SampleAnimation(gameObject, combineClip.length);
            }
        } else {
            if (combineClip != null) {
                float sampleTime = (combineProgress / 100.0f) * combineClip.length;
                combineClip.SampleAnimation(gameObject, sampleTime);
            }
        }
    }

    public void SetCameraCombat() {
        Camera cam = Camera.main;
        if (cam != null) {
            cam.fieldOfView = 48.0f;
            cam.transform.position = new Vector3(0.0f, 2.7f, -9.0f);
            cam.transform.LookAt(new Vector3(0.0f, 2.2f, 2.5f));
        }
    }

    public void SetCameraColossus() {
        Camera cam = Camera.main;
        if (cam != null) {
            cam.fieldOfView = 65.0f;
            cam.transform.position = new Vector3(0.0f, 1.5f, 5.0f);
            cam.transform.LookAt(new Vector3(posX, posY + 10.0f, posZ));
        }
    }
}
