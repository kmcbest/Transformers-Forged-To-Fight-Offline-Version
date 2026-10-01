import glob

for f in glob.glob("tools/demolishor/*.py"):
    with open(f, "r", encoding="utf-8", errors="ignore") as fp:
        c = fp.read()
        if "demolishor_phase1.blend" in c and ("save_mainfile" in c or "export" in c):
            for l in c.splitlines():
                if "demolishor_phase1.blend" in l and ("save" in l or "out" in l.lower()):
                    print(f"{f}: {l}")
