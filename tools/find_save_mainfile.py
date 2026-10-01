import glob

for f in glob.glob("tools/demolishor/*.py"):
    with open(f, "r", encoding="utf-8", errors="ignore") as fp:
        c = fp.read()
        if "save_mainfile" in c:
            for l in c.splitlines():
                if "save_mainfile" in l:
                    print(f"{f}: {l}")
