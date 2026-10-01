with open("tools/nativehook/hook.c", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if "RATEWGT" in l or "GETBP" in l:
        for j in range(max(0, i-5), min(len(lines), i+15)):
            print(f"{j+1}: {lines[j].rstrip()}")
        print("-" * 50)
