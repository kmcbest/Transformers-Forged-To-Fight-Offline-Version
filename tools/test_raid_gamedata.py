import sys
import os
sys.path.insert(0, os.path.abspath("Server"))

import gamedata

print("Testing gamedata for RAID...")
print("RAID_QID:", gamedata.RAID_QID)
walkable = gamedata.quest_walkable_tiles(gamedata.RAID_QID)
print("Walkable tiles:", len(walkable), walkable)
start = gamedata.quest_start(gamedata.RAID_QID)
print("Start tile:", start)
boss = gamedata.quest_boss_tiles(gamedata.RAID_QID)
print("Boss tiles:", boss)

# Test legal moves
assert gamedata.is_quest_legal_move(gamedata.RAID_QID, (25, 44), (25, 42)) == True
assert gamedata.is_quest_legal_move(gamedata.RAID_QID, (25, 42), (22, 39)) == True
assert gamedata.is_quest_legal_move(gamedata.RAID_QID, (25, 42), (28, 39)) == True
assert gamedata.is_quest_legal_move(gamedata.RAID_QID, (22, 39), (25, 36)) == True
assert gamedata.is_quest_legal_move(gamedata.RAID_QID, (28, 39), (25, 36)) == True
assert gamedata.is_quest_legal_move(gamedata.RAID_QID, (25, 36), (22, 33)) == True
assert gamedata.is_quest_legal_move(gamedata.RAID_QID, (25, 36), (28, 33)) == True
assert gamedata.is_quest_legal_move(gamedata.RAID_QID, (22, 33), (25, 30)) == True
assert gamedata.is_quest_legal_move(gamedata.RAID_QID, (28, 33), (25, 30)) == True

# Test illegal moves
assert gamedata.is_quest_legal_move(gamedata.RAID_QID, (25, 44), (25, 30)) == False
assert gamedata.is_quest_legal_move(gamedata.RAID_QID, (25, 42), (25, 36)) == False
print("Legal and illegal moves verified!")

# Test summary & map
summary = gamedata.build_raid_summary()
print("Summary friendlyName:", summary["friendlyName"])
qmap = gamedata.build_raid_map()
print("Map grid dim:", qmap["gridDimension"], "walkableCount:", qmap["walkableCount"])

# Test active quest & activate match response
resp = gamedata.build_raid_activate_match_response()
assert "activeQuests" in resp
assert "raid_base" in resp["activeQuests"]
aq = resp["activeQuests"]["raid_base"]
print("Active quest qid:", aq["qid"], "instances:", len(aq["instances"]))
assert aq["expiry"] == 2000000000
assert aq["expiryTime"] == 2000000000
assert aq["instances"][0]["expiryTime"] == 2000000000
print("Expiry assertions passed!")

# Test quest movedir
movedir = gamedata.build_quest_movedir("raid_base", 0, -1, start=(25, 44))
actions = movedir["results"]
print("Move to Node 1 actions count:", len(actions))
assert len(actions) == 2
assert "battle" in actions[1]["action"]
print("Node 1 battle enemy:", actions[1]["action"]["battle"]["battleEnemy"]["key"])
assert actions[1]["action"]["battle"]["battleEnemy"]["key"] == "arcee_gs_deluxe2014"

# Test move to Node 7 (boss)
movedir_boss = gamedata.build_quest_movedir("raid_base", 1, -1, start=(22, 33))
actions_boss = movedir_boss["results"]
print("Move to Node 7 battle enemy:", actions_boss[1]["action"]["battle"]["battleEnemy"]["key"])
assert actions_boss[1]["action"]["battle"]["battleEnemy"]["key"] == "megatron_gs_leader2015"
assert actions_boss[1]["action"]["battle"]["isFinalBoss"] == True
print("Node 7 final boss verified!")

print("ALL RAID GAMEDATA TESTS PASSED SUCCESSFULLY!")
