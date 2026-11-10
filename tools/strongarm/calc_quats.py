import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np

# Quaternions: [x, y, z, w]
def q_mult(q1, q2):
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    return np.array([
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2,
        w1*w2 - x1*x2 - y1*y2 - z1*z2
    ])

def q_to_euler_deg(q):
    x, y, z, w = q
    # roll (x-axis rotation)
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = np.arctan2(sinr_cosp, cosr_cosp)

    # pitch (y-axis rotation)
    sinp = 2 * (w * y - z * x)
    if np.abs(sinp) >= 1:
        pitch = np.copysign(np.pi / 2, sinp)
    else:
        pitch = np.arcsin(sinp)

    # yaw (z-axis rotation)
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = np.arctan2(siny_cosp, cosy_cosp)

    return np.degrees([roll, pitch, yaw])

q_hips = [0.03084356, 0.03084355, -0.70643377, 0.70643377]
q_trans_orig = [-0.5, -0.5, 0.5, 0.5]
q_world_orig = q_mult(q_hips, q_trans_orig)

print("Hips Euler (deg):", q_to_euler_deg(q_hips))
print("Transformed Orig Euler (deg):", q_to_euler_deg(q_trans_orig))
print("World Orig Euler (deg):", q_to_euler_deg(q_world_orig))

# What if transformed world rotation is set directly?
# In Unity: transform.rotation = ... sets WORLD rotation!
