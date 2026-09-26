import sys
sys.path.insert(0, "Server")
import gamedata

bids = [
    "shockwave_gs",
    "megatron_gs_leader2015",
    "galvatron_gs_voyager2016",
    "megatron_cin_rotf",
    "blaster_gs_leader2016",
    "arcee_gs_deluxe2014",
    "optimusprime_cin_tf",
]

for bid in bids:
    assert bid in gamedata.ROSTER, f"Missing: {bid}"
    print(f"OK: {bid} -> {gamedata.ROSTER[bid]}")
print("ALL BIDS OK!")
