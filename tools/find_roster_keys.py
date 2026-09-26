import sys
sys.path.insert(0, "Server")
import gamedata

names = ["shockwave", "galvatron", "arcee", "megatron"]
for k in sorted(gamedata.ROSTER.keys()):
    for n in names:
        if n in k.lower():
            print(f"{k} -> {gamedata.ROSTER[k]}")
