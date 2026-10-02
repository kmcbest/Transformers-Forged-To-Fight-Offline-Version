from pathlib import Path

lines = Path("toolchain/unity_build_project/debug_scene.log").read_text(encoding="utf-8", errors="replace").splitlines()
for l in lines:
    if any(k in l for k in ["=== Building", "Root GameObjects", "Renderer:", "Shader", "Material", "Exception", "Error", "error", "matArcee", "M_Arcee"]):
        print(l)
