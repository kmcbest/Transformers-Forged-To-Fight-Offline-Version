import sys
sys.path.insert(0, "Server")
import gamedata

print("Testing 50x50 base generation...")
act = gamedata.build_base_active()
mission = act["userBase"]
print("ActiveMission mode:", mission["mode"], "category:", mission["category"])
print("Placements count:", len(mission["placements"]))
print("UserSockets count:", len(act["userSockets"]))
print("UserBuildings count:", len(act["userBuildings"]))
print("AvailableBuildings count:", len(act["userAvailableBuildings"]))
m = mission["map"]
print("Grid dimension:", m["gridDimension"])
print("Paths count:", len(m["pathData"]))
print("Walkable count:", m["walkableCount"])

# Check tile (0, 0)
t00 = m["grid"][0][0]
print("Tile (0, 0) renderTemplate:", t00.get("renderTemplate"))

# Check Shockwave tile (24, 16)
t_sw = m["grid"][24][16]
print("Tile (24, 16) [Shockwave] sockets:", t_sw.get("sockets"), "links:", len(t_sw.get("links", [])))

# Check Galvatron tile (24, 22)
t_gv = m["grid"][24][22]
print("Tile (24, 22) [Galvatron] sockets:", t_gv.get("sockets"), "links:", len(t_gv.get("links", [])))

# Check Relic tile (16, 19)
t_op = m["grid"][16][19]
print("Tile (16, 19) [Relic OP] sockets:", t_op.get("sockets"), "links:", len(t_op.get("links", [])))

# Check Turret tile (24, 25)
t_turret = m["grid"][24][25]
print("Tile (24, 25) [Turret] sockets:", t_turret.get("sockets"), "links:", len(t_turret.get("links", [])))

# Check Placements keys
print("\nSample Placements:")
for k, v in list(mission["placements"].items())[:5]:
    print(f"  {k} -> entity={v['entityType']} key={v['key']} pos={v['position']}")
