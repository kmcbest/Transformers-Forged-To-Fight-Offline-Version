import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import shutil
import subprocess
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
SCRATCH = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d\scratch")
PACKER = SCRATCH / "unity_ab_packer"
UNITY_EXE = ROOT / "toolchain" / "Unity_2020.3.31f1" / "Editor" / "Unity.exe"

src_dir = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Strongarm"
dst_dir = PACKER / "Assets" / "Strongarm"
dst_dir.mkdir(parents=True, exist_ok=True)

# Copy meshes & metas
for f in ["cha_strongarm_gs_00.asset", "cha_strongarm_gs_00.asset.meta",
          "cha_strongarm_gs_01.asset", "cha_strongarm_gs_01.asset.meta"]:
    src = src_dir / f
    dst = dst_dir / f
    shutil.copy2(src, dst)
    print(f"Copied {f} to packer Assets/Strongarm/")

# Create PackStrongarmMeshBundle.cs
cs_code = """using System.IO;
using UnityEditor;
using UnityEngine;

public static class PackStrongarmMeshBundle {
    public static void Build() {
        string[] paths = new string[] {
            "Assets/Strongarm/cha_strongarm_gs_00.asset",
            "Assets/Strongarm/cha_strongarm_gs_01.asset"
        };
        foreach (string p in paths) {
            Mesh m = AssetDatabase.LoadAssetAtPath<Mesh>(p);
            if (m == null) {
                Debug.LogError("[PackStrongarmMeshBundle] Missing mesh at " + p);
                EditorApplication.Exit(1);
                return;
            }
            Debug.Log("[PackStrongarmMeshBundle] Loaded " + m.name + " verts=" + m.vertexCount + " submeshes=" + m.subMeshCount + " bindposes=" + m.bindposes.Length + " bounds=" + m.bounds);
        }

        string outDir = "E:/Agent/TFTF-blender/toolchain/unity_build_project/AssetBundles";
        if (!Directory.Exists(outDir)) Directory.CreateDirectory(outDir);

        AssetBundleBuild[] builds = new AssetBundleBuild[1];
        builds[0].assetBundleName = "strongarm_mesh.assetbundle";
        builds[0].assetNames = paths;

        var manifest = BuildPipeline.BuildAssetBundles(
            outDir,
            builds,
            BuildAssetBundleOptions.ForceRebuildAssetBundle | BuildAssetBundleOptions.ChunkBasedCompression,
            BuildTarget.Android
        );
        if (manifest == null) {
            Debug.LogError("[PackStrongarmMeshBundle] BuildAssetBundles returned null!");
            EditorApplication.Exit(1);
            return;
        }
        Debug.Log("[PackStrongarmMeshBundle] Successfully built strongarm_mesh.assetbundle to " + outDir);
        EditorApplication.Exit(0);
    }
}
"""

cs_file = PACKER / "Assets" / "Editor" / "PackStrongarmMeshBundle.cs"
cs_file.write_text(cs_code, encoding="utf-8")
print(f"Wrote {cs_file}")

log_file = SCRATCH / "pack_strongarm_mesh_ab.log"
cmd = [
    str(UNITY_EXE),
    "-batchmode",
    "-nographics",
    "-quit",
    "-projectPath", str(PACKER),
    "-buildTarget", "Android",
    "-executeMethod", "PackStrongarmMeshBundle.Build",
    "-logFile", str(log_file),
]

print("[*] Running headless Unity AssetBundle build for strongarm_mesh.assetbundle...")
res = subprocess.run(cmd)
print(f"[*] Unity exited with code {res.returncode}")

if log_file.exists():
    log_text = log_file.read_text(encoding="utf-8", errors="replace")
    for line in log_text.splitlines():
        if "[PackStrongarmMeshBundle]" in line or "Error" in line:
            print(f"  {line}")

ab_out = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "strongarm_mesh.assetbundle"
if ab_out.is_file():
    print(f"[✓] Successfully built {ab_out} ({ab_out.stat().st_size / 1024:.1f} KB)")
else:
    print(f"[X] Failed to find {ab_out}")
    sys.exit(1)
