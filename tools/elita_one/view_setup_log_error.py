from pathlib import Path

lines = Path("toolchain/unity_build_project/setup_scene.log").read_text(encoding="utf-8", errors="replace").splitlines()
print(f"Total lines: {len(lines)}")
for i, l in enumerate(lines[270:340], start=271):
    print(f"{i}: {l}")
