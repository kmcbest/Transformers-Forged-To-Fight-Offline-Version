with open("tools/nativehook/inapk_server.c", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if "tftf_offline_payload" in l:
        for j in range(max(0, i-5), min(len(lines), i+25)):
            print(f"{j+1}: {lines[j].rstrip()}")
        print("="*60)
