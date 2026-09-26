import sys

# Test the coordinates and layout for 50x50 base
BASE_DIM = 50

# Center coordinates
CENTER_X = 24
CENTER_Y = 19

def tile_to_world(x, y, dim=50):
    half_tile = 10.0
    tile_size = 20.0
    map_center = -dim / 2.0 * tile_size # -500
    wx = x * tile_size + half_tile + map_center
    wz = (dim - 1 - y) * tile_size + half_tile + map_center
    return wx, wz

# Define layout matching media_1790396156745.png
DEFENDERS = {
    (24, 16): {"bid": "shockwave_gs_kabam", "rank": 5, "level": 50, "sig": 60, "name": "Shockwave (Core Boss)"},
    (24, 13): {"bid": "megatron_gs_leader", "rank": 5, "level": 50, "sig": 60, "name": "Megatron (Top Boss)"},
    (24, 22): {"bid": "galvatron_cin", "rank": 5, "level": 50, "sig": 40, "name": "Galvatron (Front Guard)"},
    (21, 16): {"bid": "megatron_cin_rotf", "rank": 5, "level": 50, "sig": 30, "name": "Megatron ROTF (Top Left)"},
    (27, 16): {"bid": "blaster_gs_leader2016", "rank": 5, "level": 50, "sig": 30, "name": "Blaster (Top Right)"},
    (20, 19): {"bid": "arcee_gs", "rank": 5, "level": 50, "sig": 40, "name": "Arcee (Left Guard)"},
    (28, 19): {"bid": "optimusprime_cin_tf", "rank": 5, "level": 50, "sig": 40, "name": "Optimus Prime (Right Guard)"},
}

RELICS = {
    (16, 19): {"id": "relic_statue_op", "model": "rlc11", "name": "Optimus Prime Monument"},
    (32, 19): {"id": "relic_matrix_of_leadership", "model": "rlc14", "name": "Matrix of Leadership"},
}

TOWERS = {
    (24, 25): "mods_laserguidance_01",       # Bottom turret
    (22, 21): "mods_harmaccelerator_01",     # Galvatron - Arcee turret
    (26, 21): "mods_strangerefractor_01",    # Galvatron - Optimus turret
    (20, 17): "mods_primemodule_01",         # Left module
    (28, 17): "mods_superconductor_01",      # Right module
    (24, 14): "mods_tacticianstrick_02",     # Upper center module
    (19, 14): "mods_immobilizer_01",         # Upper left tower
    (29, 14): "mods_brawlersfury_01",        # Upper right tower
}

WAYPOINTS = [
    (24, 19), # Center golden waypoint
    (24, 15), # Between Shockwave and Top module
    (21, 18), # Near Megatron/Arcee
    (27, 18), # Near Blaster/Optimus
    (24, 24), # In front of bottom turret
]

print("=== Base Layout 50x50 Summary ===")
all_active_tiles = set(DEFENDERS.keys()) | set(RELICS.keys()) | set(TOWERS.keys()) | set(WAYPOINTS)
print(f"Total active tiles: {len(all_active_tiles)}")

for (x, y) in sorted(all_active_tiles, key=lambda p: (p[1], p[0])):
    wx, wz = tile_to_world(x, y)
    tags = []
    if (x, y) in DEFENDERS: tags.append(f"Defender: {DEFENDERS[(x, y)]['name']}")
    if (x, y) in RELICS: tags.append(f"Relic: {RELICS[(x, y)]['name']}")
    if (x, y) in TOWERS: tags.append(f"Tower: {TOWERS[(x, y)]}")
    if (x, y) in WAYPOINTS: tags.append("Waypoint")
    print(f"Tile ({x:2d}, {y:2d}) -> World ({wx:6.1f}, {wz:6.1f}) : {', '.join(tags)}")
