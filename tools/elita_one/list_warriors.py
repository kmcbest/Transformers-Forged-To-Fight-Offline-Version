import sys
from pathlib import Path

sys.path.insert(0, str(Path("Server").resolve()))
import gamedata

warrs = [bid for bid, (f, c, s) in gamedata.ROSTER.items() if c == "warr"]
print(f"Total warriors in ROSTER: {len(warrs)}")
for w in warrs:
    print(w, gamedata.ROSTER[w], gamedata._BOT_NAMES.get(w, w))
