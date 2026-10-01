with open("tools/demolishor/apply_perfect_stance_v5.py", "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if "head" in line.lower() or "neck" in line.lower():
            print(f"{i+1}: {line.strip()}")
