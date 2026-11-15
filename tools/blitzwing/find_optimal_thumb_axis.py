import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np

# Let's test Unity rotation of LeftHandThumb1, 2, 3
# In Unity space, for LeftHandThumb1:
# The bone direction is along local -X or -Z
# Let's see what happens to the thumb tip when rotated around various axes in bone local space

def quat_mult(q1, q2):
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    return np.array([
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2,
        w1*w2 - x1*x2 - y1*y2 - z1*z2
    ])

def quat_to_matrix(q):
    x, y, z, w = q
    return np.array([
        [1 - 2*y*y - 2*z*z, 2*x*y - 2*w*z, 2*x*z + 2*w*y],
        [2*x*y + 2*w*z, 1 - 2*x*x - 2*z*z, 2*y*z - 2*w*x],
        [2*x*z - 2*w*y, 2*y*z + 2*w*x, 1 - 2*x*x - 2*y*y]
    ])

def angle_axis(angle_deg, axis):
    rad = np.radians(angle_deg) * 0.5
    s = np.sin(rad)
    ax = np.array(axis) / np.linalg.norm(axis)
    return np.array([ax[0]*s, ax[1]*s, ax[2]*s, np.cos(rad)])

# Left Hand Bindposes (in LeftHand local space)
p_t1 = np.array([-0.2375, -0.1386, 0.4215])
r_t1_rest = np.array([0.2706, 0.6533, -0.2706, 0.6533]) # [x, y, z, w]

p_t2 = np.array([-0.4138, 0.0, 0.0])
r_t2_rest = np.array([0.0, 0.0, 0.0, 1.0])

p_t3 = np.array([-0.2090, 0.0, 0.0])
r_t3_rest = np.array([0.0, 0.0, 0.0, 1.0])

p_tip = np.array([-0.20, 0.0, 0.0])

# Fingers curled fist target:
# Curled Index knuckle is around [-0.5, -0.5, 0.35]
# Curled Middle knuckle is around [-0.5, -0.5, 0.10]
# Ideal thumb tip should be around [-0.4 to -0.6, -0.4 to -0.6, 0.15 to 0.25] (covering index and middle!)

candidate_axes = [
    ("Vector3.forward (0,0,1)", [0, 0, 1]),
    ("Vector3.back (0,0,-1)", [0, 0, -1]),
    ("Vector3.up (0,1,0)", [0, 1, 0]),
    ("Vector3.down (0,-1,0)", [0, -1, 0]),
    ("Vector3(0, 0.707, 0.707)", [0, 0.707, 0.707]),
    ("Vector3(0, -0.707, 0.707)", [0, -0.707, 0.707]),
    ("Vector3(0, 0.707, -0.707)", [0, 0.707, -0.707]),
    ("Vector3(0, -0.707, -0.707)", [0, -0.707, -0.707]),
]

def eval_thumb(axis, angle_deg=75.0):
    q_curl = angle_axis(angle_deg, axis)
    r_t1 = quat_mult(r_t1_rest, q_curl)
    M_t1 = quat_to_matrix(r_t1)
    
    pos_2 = p_t1 + M_t1 @ p_t2
    r_t2 = quat_mult(r_t2_rest, q_curl)
    M_t2 = quat_to_matrix(quat_mult(r_t1, r_t2))
    
    pos_3 = pos_2 + M_t2 @ p_t3
    r_t3 = quat_mult(r_t3_rest, q_curl)
    M_t3 = quat_to_matrix(quat_mult(quat_mult(r_t1, r_t2), r_t3))
    
    pos_tip = pos_3 + M_t3 @ p_tip
    return pos_tip

print("=== Candidate Curl Axes at 75° (Left Thumb) ===")
print("Ideal target: X ~ -0.50, Y ~ -0.50 (in front of palm), Z ~ 0.20 (covering index/middle)")
for label, ax in candidate_axes:
    tip = eval_thumb(ax, 75.0)
    print(f"{label:30s}: tip = ({tip[0]:7.4f}, {tip[1]:7.4f}, {tip[2]:7.4f})")
