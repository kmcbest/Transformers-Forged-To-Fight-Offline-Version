with open("tools/latest_device.log", "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        if "payload" in line.lower() or "map_payload" in line:
            print(line.rstrip())
