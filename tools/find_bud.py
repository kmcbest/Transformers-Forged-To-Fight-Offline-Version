with open("Server/gamedata.py", "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if "def build_user_data" in line:
            print(f"{i+1}: {line}")
