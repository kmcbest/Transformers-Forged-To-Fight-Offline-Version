import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
from pathlib import Path

cs_code = """using UnityEditor;
using UnityEngine;

public class CheckMeshBounds {
    public static void Run() {
        GameObject fbx = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Strongarm/strongarm_vh_prepared.fbx");
        SkinnedMeshRenderer smr = fbx.GetComponentInChildren<SkinnedMeshRenderer>(true);
        Mesh m = smr.sharedMesh;
        Debug.Log($"[CheckVhMesh] Bounds Center=({m.bounds.center.x:F3}, {m.bounds.center.y:F3}, {m.bounds.center.z:F3}) Size=({m.bounds.size.x:F3}, {m.bounds.size.y:F3}, {m.bounds.size.z:F3})");
    }
}
"""

cs_file = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Editor\CheckMeshBounds.cs")
cs_file.write_text(cs_code, encoding="utf-8")

unity_exe = Path(r"E:\Agent\TFTF-blender\toolchain\Unity_2020.3.31f1\Editor\Unity.exe")
project_dir = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project")
log_file = Path(r"E:\Agent\TFTF-blender\tools\strongarm\mesh_bounds.log")

subprocess.run([str(unity_exe), "-batchmode", "-quit", "-projectPath", str(project_dir), "-executeMethod", "CheckMeshBounds.Run", "-logFile", str(log_file)])
if log_file.exists():
    for l in log_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "[CheckVhMesh]" in l:
            print(l)
