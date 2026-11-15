import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np

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

p_t1 = np.array([-0.2375, -0.1386, 0.4215])
r_t1_rest = np.array([0.2706, 0.6533, -0.2706, 0.6533])

p_t2 = np.array([-0.4138, 0.0, 0.0])
r_t2_rest = np.array([0.0, 0.0, 0.0, 1.0])

p_t3 = np.array([-0.2090, 0.0, 0.0])
r_t3_rest = np.array([0.0, 0.0, 0.0, 1.0])

p_tip = np.array([-0.20, 0.0, 0.0])

def eval_thumb_graduated(a1, a2, a3, axis=[0,0,1]):
    q1 = angle_axis(a1, axis)
    q2 = angle_axis(a2, axis)
    q3 = angle_axis(a3, axis)
    
    r_t1 = quat_mult(r_t1_rest, q1)
    M_t1 = quat_to_matrix(r_t1)
    
    pos_2 = p_t1 + M_t1 @ p_t2
    r_t2 = quat_mult(r_t2_rest, q2)
    M_t2 = quat_to_matrix(quat_mult(r_t1, r_t2))
    
    pos_3 = pos_2 + M_t2 @ p_t3
    r_t3 = quat_mult(r_t3_rest, q3)
    M_t3 = quat_to_matrix(quat_mult(quat_mult(r_t1, r_t2), r_t3))
    
    pos_tip = pos_3 + M_t3 @ p_tip
    return pos_2, pos_3, pos_tip

print("--- Comparing Uniform vs Graduated Thumb Curl at curlAll = 70° ---")
p2_u, p3_u, tip_u = eval_thumb_graduated(70, 70, 70)
print(f"Uniform (70, 70, 70):     Thumb2={p2_u.round(3)}, Thumb3={p3_u.round(3)}, Tip={tip_u.round(3)}")

p2_g, p3_g, tip_g = eval_thumb_graduated(40, 70, 80)
print(f"Graduated (40, 70, 80):   Thumb2={p2_g.round(3)}, Thumb3={p3_g.round(3)}, Tip={tip_g.round(3)}")
