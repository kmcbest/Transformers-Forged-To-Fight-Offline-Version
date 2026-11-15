import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import math

# Quaternion (x, y, z, w) = (-0.5, -0.5, 0.5, 0.5)
# Convert to Euler angles
# Or rotation matrix
x, y, z, w = -0.5, -0.5, 0.5, 0.5
R = [
    [1 - 2*(y*y + z*z), 2*(x*y - z*w), 2*(x*z + y*w)],
    [2*(x*y + z*w), 1 - 2*(x*x + z*z), 2*(y*z - x*w)],
    [2*(x*z - y*w), 2*(y*z + x*w), 1 - 2*(x*x + y*y)],
]
for row in R:
    print([round(v, 4) for v in row])
