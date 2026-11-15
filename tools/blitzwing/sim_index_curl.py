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

# Left Hand Index Finger in LeftHand space:
# LeftHandIndex1: localPos=(-0.7540, -0.0125, 0.3980), localRot=(w=1, x=0, y=0, z=-0.0097)
# LeftHandIndex2: localPos=(-0.3835, 0, 0), localRot=(w=1, x=0, y=0, z=0.0046)
# LeftHandIndex3: localPos=(-0.3091, 0, 0), localRot=(w=1, x=0, y=0, z=0)
# Index tip: localPos=(-0.25, 0, 0)

p_i1 = np.array([-0.7540, -0.0125, 0.3980])
r_i1 = np.array([0, 0, -0.0097, 1.0])
p_i2 = np.array([-0.3835, 0, 0])
r_i2 = np.array([0, 0, 0.0046, 1.0])
p_i3 = np.array([-0.3091, 0, 0])
r_i3 = np.array([0, 0, 0, 1.0])
p_itip = np.array([-0.25, 0, 0])

def eval_index_tip(angle_deg=0.0):
    q_curl = angle_axis(angle_deg, [0, 0, 1]) # Vector3.forward
    
    r1 = quat_mult(r_i1, q_curl)
    M1 = quat_to_matrix(r1)
    
    pos2 = p_i1 + M1 @ p_i2
    r2 = quat_mult(quat_mult(r1, r_i2), q_curl)
    M2 = quat_to_matrix(r2)
    
    pos3 = pos2 + M2 @ p_i3
    r3 = quat_mult(quat_mult(r2, r_i3), q_curl)
    M3 = quat_to_matrix(r3)
    
    tip = pos3 + M3 @ p_itip
    return pos3, tip

rest_i3, rest_itip = eval_index_tip(0.0)
curled_i3, curled_itip = eval_index_tip(65.0)

print("Index tip at rest (angle=0):", rest_itip.round(4))
print("Index tip at curl (angle=65):", curled_itip.round(4))
print("Index tip delta when curled:", (curled_itip - rest_itip).round(4))
