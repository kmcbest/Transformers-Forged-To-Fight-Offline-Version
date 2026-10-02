from pathlib import Path

p = Path("toolchain/unity_build_project/sample_arcee.log")
if p.exists():
    for l in p.read_text(encoding="utf-8", errors="replace").splitlines()[-30:]:
        print(l)
