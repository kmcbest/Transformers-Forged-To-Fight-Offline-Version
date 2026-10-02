from pathlib import Path

p = Path("toolchain/unity_build_project/setup_scene.log")
if p.exists():
    for l in p.read_text(encoding="utf-8", errors="replace").splitlines()[-35:]:
        print(l)
