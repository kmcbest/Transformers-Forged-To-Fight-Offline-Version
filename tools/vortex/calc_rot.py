import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np

# Quaternion (x, y, z, w) = (-0.5, -0.5, 0.5, 0.5)
x, y, z, w = -0.5, -0.5, 0.5, 0.5

# Rotation matrix:
# R = [
#   1 - 2(y^2 + z^2),     2(xy - zw),       2(xz + yw)
#   2(xy + zw),       1 - 2(x^2 + z^2),     2(yz - xw)
#   2(xz - yw),           2(yz + xw),   1 - 2(x^2 + y^2)
# ]

R = np.array([
    [1 - 2*(y**2 + z**2),     2*(x*y - z*w),       2*(x*z + y*w)],
    [2*(x*y + z*w),       1 - 2*(x**2 + z**2),     2*(y*z - x*w)],
    [2*(x*z - y*w),           2*(y*z + x*w),   1 - 2*(x**2 + y**2)]
])

print("Rotation Matrix:")
print(R)

# Let's see what R maps:
# v_world = R * v_local
print("Local (1, 0, 0) -> World:", R @ np.array([1, 0, 0]))
print("Local (0, 1, 0) -> World:", R @ np.array([0, 1, 0]))
print("Local (0, 0, 1) -> World:", R @ np.array([0, 0, 1]))
