import glob

for f in glob.glob("tools/demolishor/*.py") + glob.glob("tools/*.py"):
    with open(f, "r", encoding="utf-8", errors="ignore") as fp:
        c = fp.read()
        if "blender.exe" in c.lower():
            for line in c.splitlines():
                if "blender.exe" in line.lower():
                    print(f"{f}: {line}")
