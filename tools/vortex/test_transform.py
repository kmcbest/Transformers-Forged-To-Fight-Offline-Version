import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np

# Grindor bounds
g_x = [-8.721, 8.721]
g_y = [0.307, 7.365]
g_z = [-13.713, 8.873]
g_center = [0.0, 3.836, -2.420]

# Current Vortex bounds
v_x = [-7.056, 6.999]
v_y = [-7.840, 7.188]
v_z = [-0.311, 4.656]

# Transformed Vortex bounds: x' = -x, y' = z + dy, z' = y + dz
# Let's find best dy, dz
# We want min y' >= 0.25 (clear ground)
# and center z' close to -2.0
dy = 0.60
dz = -1.50

v_x_prime = [-v_x[1], -v_x[0]]
v_y_prime = [v_z[0] + dy, v_z[1] + dy]
v_z_prime = [v_y[0] + dz, v_y[1] + dz]

print(f"Grindor X: {g_x}, center={g_center[0]}")
print(f"Grindor Y: {g_y}, center={g_center[1]}")
print(f"Grindor Z: {g_z}, center={g_center[2]}")
print("--- Transformed Vortex ---")
print(f"Vortex X': {v_x_prime}, center={(v_x_prime[0]+v_x_prime[1])/2:.3f}, span={v_x_prime[1]-v_x_prime[0]:.3f}")
print(f"Vortex Y': {v_y_prime}, center={(v_y_prime[0]+v_y_prime[1])/2:.3f}, span={v_y_prime[1]-v_y_prime[0]:.3f}")
print(f"Vortex Z': {v_z_prime}, center={(v_z_prime[0]+v_z_prime[1])/2:.3f}, span={v_z_prime[1]-v_z_prime[0]:.3f}")
