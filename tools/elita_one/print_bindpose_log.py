from pathlib import Path

lines = Path("toolchain/unity_build_project/compare_bindposes.log").read_text(encoding="utf-8", errors="replace").splitlines()
for i, l in enumerate(lines):
    if "Bone[" in l or "=== Comparing" in l:
        for k in range(i, min(len(lines), i + 15)):
            print(lines[k])
        print("------------------")
        break
