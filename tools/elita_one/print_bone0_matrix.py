from pathlib import Path

lines = Path("toolchain/unity_build_project/compare_bindposes.log").read_text(encoding="utf-8", errors="replace").splitlines()
found = False
for l in lines:
    if "Bone[0]" in l:
        found = True
    if found:
        if not ("UnityEngine." in l or "(Filename:" in l or "CompareBindposes:Run" in l):
            print(l)
        if "Bone[2]" in l:
            break
