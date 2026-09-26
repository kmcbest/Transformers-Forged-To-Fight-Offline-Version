def tile_to_world(x, y, dim=50):
    half_tile = 10.0
    tile_size = 20.0
    map_center_x = -dim / 2.0 * tile_size
    map_center_z = -dim / 2.0 * tile_size
    wx = x * tile_size + half_tile + map_center_x
    wz = (dim - 1 - y) * tile_size + half_tile + map_center_z
    return wx, wz

print("Testing node positions:")
nodes = {
    "center (Shockwave)": (24, 18),
    "top (Megatron)": (24, 14),
    "bottom": (24, 22),
    "left": (20, 18),
    "right": (28, 18),
    "top-left": (21, 15),
    "top-right": (27, 15),
    "relic-left (Optimus statue)": (16, 18),
    "relic-right (Matrix)": (32, 18),
}

for name, (x, y) in nodes.items():
    wx, wz = tile_to_world(x, y)
    print(f"{name:25s}: tile=({x:2d}, {y:2d}) -> world=({wx:6.1f}, {wz:6.1f})")
