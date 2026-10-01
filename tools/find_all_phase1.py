import glob

for f in glob.glob("**/*.py", recursive=True):
    with open(f, "r", encoding="utf-8", errors="ignore") as fp:
        c = fp.read()
        if "demolishor_phase1.blend" in c:
            for l in c.splitlines():
                if "demolishor_phase1.blend" in l:
                    print(f"{f}: {l}")
