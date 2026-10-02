import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent.parent
UNITY_EXE = ROOT / "toolchain" / "Unity_2020.3.31f1" / "Editor" / "Unity.exe"
PROJECT_DIR = ROOT / "toolchain" / "unity_build_project"
ARCEE_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "arcee_gs_deluxe2014_odr" / "arcee_gs_deluxe2014.assetbundle"
OUT_DIR = ROOT / "tools" / "elita_one"
OUT_DIR.mkdir(parents=True, exist_ok=True)

cs_script = PROJECT_DIR / "Assets" / "Editor" / "SampleArceeAnimations.cs"
cs_content = f"""using UnityEditor;
using UnityEngine;
using System.IO;
using System.Collections.Generic;

public class SampleArceeAnimations {{
    [System.Serializable]
    public class TransformFrame {{
        public string name;
        public float[] m = new float[16];
    }}

    [System.Serializable]
    public class AnimFrame {{
        public int frameIndex;
        public float time;
        public List<TransformFrame> bones = new List<TransformFrame>();
    }}

    [System.Serializable]
    public class ExportedAnimation {{
        public string clipName;
        public float sampleRate;
        public float length;
        public int totalFrames;
        public List<AnimFrame> frames = new List<AnimFrame>();
    }}

    public static void SampleClip(AssetBundle bundle, GameObject inst, string clipName, string outPath) {{
        AnimationClip clip = null;
        foreach (var c in bundle.LoadAllAssets<AnimationClip>()) {{
            if (c.name == clipName) {{
                clip = c;
                break;
            }}
        }}

        if (clip == null) {{
            Debug.LogError("[SampleArcee] Failed to find clip: " + clipName);
            return;
        }}

        Debug.Log("[SampleArcee] Sampling clip: " + clip.name + " len: " + clip.length + "s fps: " + clip.frameRate);
        Transform[] allTransforms = inst.GetComponentsInChildren<Transform>(true);

        ExportedAnimation exp = new ExportedAnimation();
        exp.clipName = clip.name;
        exp.sampleRate = clip.frameRate > 0 ? clip.frameRate : 30f;
        exp.length = clip.length;

        float dt = 1f / exp.sampleRate;
        int frameCount = Mathf.RoundToInt(clip.length * exp.sampleRate);
        exp.totalFrames = frameCount;

        for (int i = 0; i <= frameCount; i++) {{
            float t = i * dt;
            clip.SampleAnimation(inst, t);

            AnimFrame af = new AnimFrame();
            af.frameIndex = i;
            af.time = t;

            foreach (Transform tr in allTransforms) {{
                TransformFrame tf = new TransformFrame();
                tf.name = tr.name;
                Matrix4x4 localMat = Matrix4x4.TRS(tr.localPosition, tr.localRotation, tr.localScale);
                for (int r = 0; r < 4; r++) {{
                    for (int c = 0; c < 4; c++) {{
                        tf.m[r * 4 + c] = localMat[r, c];
                    }}
                }}
                af.bones.Add(tf);
            }}
            exp.frames.Add(af);
        }}

        string json = JsonUtility.ToJson(exp, true);
        File.WriteAllText(outPath, json);
        Debug.Log("[SampleArcee] Successfully exported " + frameCount + " frames to " + outPath);
    }}

    public static void RunSample() {{
        string bundlePath = @\"{str(ARCEE_BUNDLE).replace('/', chr(92))}\";
        AssetBundle bundle = AssetBundle.LoadFromFile(bundlePath);
        if (bundle == null) {{
            Debug.LogError("[SampleArcee] Failed to load bundle: " + bundlePath);
            return;
        }}

        // Load Prefab
        GameObject prefab = null;
        foreach (var go in bundle.LoadAllAssets<GameObject>()) {{
            if (go.name.Contains(\"Arcee\") || go.name.Contains(\"arcee\")) {{
                prefab = go;
                break;
            }}
        }}

        if (prefab == null) {{
            Debug.LogError("[SampleArcee] Failed to find Arcee prefab in bundle!");
            bundle.Unload(true);
            return;
        }}

        GameObject inst = GameObject.Instantiate(prefab);
        Debug.Log("[SampleArcee] Instantiated prefab: " + inst.name);

        string outDir = @\"{str(OUT_DIR).replace('/', chr(92))}\";
        SampleClip(bundle, inst, \"TeamSelect_Female_idle\", Path.Combine(outDir, \"arcee_team_select_idle.json\"));
        SampleClip(bundle, inst, \"Prefight_Female_idle\", Path.Combine(outDir, \"arcee_prefight_idle.json\"));
        SampleClip(bundle, inst, \"Arcee_Normal_attackSpecial_01\", Path.Combine(outDir, \"arcee_special_01.json\"));

        GameObject.DestroyImmediate(inst);
        bundle.Unload(true);
    }}
}}
"""
cs_script.write_text(cs_content, encoding="utf-8")
print(f"[✓] Created {cs_script.name}")

# Run Unity headless
log_file = PROJECT_DIR / "sample_arcee.log"
print(f"[*] Running Unity Editor headless sample (logging to {log_file.name})...")

cmd = [
    str(UNITY_EXE),
    "-batchmode",
    "-quit",
    "-projectPath", str(PROJECT_DIR),
    "-executeMethod", "SampleArceeAnimations.RunSample",
    "-logFile", str(log_file)
]

res = subprocess.run(cmd)
print(f"[+] Unity process finished with return code: {res.returncode}")

for out_name in ["arcee_team_select_idle.json", "arcee_prefight_idle.json", "arcee_special_01.json"]:
    f = OUT_DIR / out_name
    if f.exists():
        print(f"[✓] SUCCESS: Exported {f.name} ({f.stat().st_size / 1024:.1f} KB)")
    else:
        print(f"[!] Missing: {f.name}")
