import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
from pathlib import Path

cs_code = """using UnityEditor;
using UnityEngine;

public class CheckBonePositions {
    public static void Run() {
        GameObject fbx = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Strongarm/strongarm_prepared.fbx");
        SkinnedMeshRenderer smr = fbx.GetComponentInChildren<SkinnedMeshRenderer>(true);
        for (int i = 0; i < smr.bones.Length; i++) {
            string n = smr.bones[i].name;
            if (n.Contains("Arm") || n.Contains("Shoulder")) {
                Vector3 p = smr.bones[i].position;
                Debug.Log($"FBX Bone {n,-20}: ({p.x:F3}, {p.y:F3}, {p.z:F3})");
            }
        }
    }
}
"""

cs_file = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Editor\CheckBonePositions.cs")
cs_file.write_text(cs_code, encoding="utf-8")

unity_exe = Path(r"E:\Agent\TFTF-blender\toolchain\Unity_2020.3.31f1\Editor\Unity.exe")
project_dir = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project")
log_file = Path(r"E:\Agent\TFTF-blender\tools\strongarm\bone_pos.log")

subprocess.run([str(unity_exe), "-batchmode", "-quit", "-projectPath", str(project_dir), "-executeMethod", "CheckBonePositions.Run", "-logFile", str(log_file)])
if log_file.exists():
    for l in log_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "FBX Bone" in l:
            print(l)
