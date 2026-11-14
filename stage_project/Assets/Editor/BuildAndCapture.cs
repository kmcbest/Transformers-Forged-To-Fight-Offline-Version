using UnityEditor;

public class BuildAndCapture {
    public static void Run() {
        BuildStagePreviewScene.Build();
        CaptureStageScreenshot.Capture();
    }
}
