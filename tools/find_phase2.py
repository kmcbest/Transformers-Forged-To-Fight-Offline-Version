import glob

for f in glob.glob("tools/demolishor/*.py"):
    with open(f, "r", encoding="utf-8", errors="ignore") as fp:
        c = fp.read()
        if "demolishor_phase2_inspect.blend" in c or "phase2" in c:
            print("Found in:", f)
