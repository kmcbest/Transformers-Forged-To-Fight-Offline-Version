import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np

def quat_to_matrix(w, x, y, z):
    # Unity quaternion
    return np.array([
        [1 - 2*y*y - 2*z*z, 2*x*y - 2*w*z, 2*x*z + 2*w*y],
        [2*x*y + 2*w*z, 1 - 2*x*x - 2*z*z, 2*y*z - 2*w*x],
        [2*x*z - 2*w*y, 2*y*z + 2*w*x, 1 - 2*x*x - 2*y*y]
    ])

# LeftHandThumb1: w=0.6533, x=0.2706, y=0.6533, z=-0.2706
R_L = quat_to_matrix(0.6533, 0.2706, 0.6533, -0.2706)
print("LeftHandThumb1 rotation matrix:")
print(R_L.round(4))

# Local X, Y, Z axes of Thumb1 in LeftHand space:
print("Local X (bone direction):", R_L[:, 0].round(4))
print("Local Y:", R_L[:, 1].round(4))
print("Local Z:", R_L[:, 2].round(4))

# RightHandThumb1: w=0.6506, x=-0.2770, y=0.6506, z=0.2770
R_R = quat_to_matrix(0.6506, -0.2770, 0.6506, 0.2770)
print("\nRightHandThumb1 rotation matrix:")
print(R_R.round(4))
print("Local X (bone direction):", R_R[:, 0].round(4))
print("Local Y:", R_R[:, 1].round(4))
print("Local Z:", R_R[:, 2].round(4))
