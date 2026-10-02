from pathlib import Path

lines = Path("toolchain/unity_build_project/debug_scene.log").read_text(encoding="utf-8", errors="replace").splitlines()
print(f"Total lines: {len(lines)}")
for l in lines:
    if any(k in l for k in ["Root:", "Renderer:", "Root GameObjects", "Scene name:"]):
        print(l)
