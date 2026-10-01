with open("tools/latest_device.log", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

keywords = ["getLoginData", "getBaseHeroData", "getUserData", "hero", "bumblebee", "sideswipe", "breakdown", "Sharkticon"]

for kw in ["getLoginData", "getBaseHeroData", "getUserData", "sideswipe"]:
    matched = [line.strip() for line in lines if kw in line]
    print(f"=== Keyword: {kw} (count: {len(matched)}) ===")
    for m in matched[:10]:
        print(m[:120])
