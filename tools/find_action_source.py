import glob

for f in glob.glob("tools/demolishor/*.py"):
    with open(f, "r", encoding="utf-8", errors="ignore") as fp:
        c = fp.read()
        if "Inspection_Running_Stride" in c:
            print("Found in:", f)
