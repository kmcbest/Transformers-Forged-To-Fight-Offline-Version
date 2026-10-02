import sys
from pathlib import Path

sys.path.insert(0, str(Path("Server").resolve()))
import gamedata

print("Total ROSTER bots:", len(gamedata.ROSTER))
bots_by_class = {}
for bid, (faction, cls, star) in gamedata.ROSTER.items():
    bots_by_class.setdefault(cls, []).append(bid)

for cls, bids in bots_by_class.items():
    print(f"Class {cls}: {len(bids)} bots")
    if "elita_one_gs" in bids:
        print(f"  -> elita_one_gs is in class {cls}")
    if "arcee_gs_deluxe2014" in bids:
        print(f"  -> arcee_gs_deluxe2014 is in class {cls}")

# Let's check how many total bots in user_data:
ud = gamedata.build_user_data()
heroes = ud["updates"]["heroes"]
print("Total heroes in user_data updates:", len(heroes))
bids_in_ud = [h["bid"] for h in heroes]
print("Is elita_one_gs in user_data?", "elita_one_gs" in bids_in_ud)
print("Index of elita_one_gs:", bids_in_ud.index("elita_one_gs") if "elita_one_gs" in bids_in_ud else -1)
print("Index of arcee_gs_deluxe2014:", bids_in_ud.index("arcee_gs_deluxe2014") if "arcee_gs_deluxe2014" in bids_in_ud else -1)
