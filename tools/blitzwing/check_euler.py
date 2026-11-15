import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import numpy as np

# Euler angles: x=0, y=-90, z=90
# In Unity, rotation order is Z * X * Y
cy = 0.0; sy = -1.0
cz = 0.0; sz = 1.0
cx = 1.0; sx = 0.0

Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])

# Unity ZXY:
R = Rz @ Rx @ Ry
print("R (Unity ZXY):")
print(np.round(R, 4))
