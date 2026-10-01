import glob

for pattern in ["tools/nativehook/*.c", "Server/*.py", "tools/*.py"]:
    for fpath in glob.glob(pattern):
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            if "tftf_offline_payload" in content:
                print(f"Found in {fpath}")
