with open("tools/demolishor/ironhide_80_bones.json", "r", encoding="utf-8") as f:
    import json
    data = json.load(f)
    print("Shoulder bones in Ironhide 80 bones:")
    for b in data["bone_order"]:
        if "shoulder" in b.lower() or "pad" in b.lower():
            print(" ", b)
