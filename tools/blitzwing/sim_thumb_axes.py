import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np

def quat_mult(q1, q2):
    # Unity quaternion: [x, y, z, w]
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
# LeftHandThumb1: localPos=(-0.2375, -0.1386, 0.4215), localRot=(w=0.6533, x=0.2706, y=0.6533, z=-0.2706)
# LeftHandThumb2: localPos=(-0.4138, 0, 0), localRot=(w=1, x=0, y=0, z=0)
# LeftHandThumb3: localPos=(-0.2090, 0, 0), localRot=(w=1, x=0, y=0, z=0)
# Thumb tip (localPos=(-0.20, 0, 0) relative to Thumb3)

# Palm / Knuckle references in LeftHand local space:
# LeftHandIndex1: localPos=(-0.7540, -0.0125, 0.3980)
# LeftHandMiddle1: localPos=(-0.7540, -0.0125, 0.1086)

p_t1 = np.array([-0.2375, -0.1386, 0.4215])
r_t1_rest = np.array([0.2706, 0.6533, -0.2706, 0.6533]) # [x, y, z, w]

p_t2 = np.array([-0.4138, 0.0, 0.0])
r_t2_rest = np.array([0.0, 0.0, 0.0, 1.0])

p_t3 = np.array([-0.2090, 0.0, 0.0])
r_t3_rest = np.array([0.0, 0.0, 0.0, 1.0])

p_tip = np.array([-0.20, 0.0, 0.0])

def eval_thumb_tip(axis, angle_deg=65.0):
    q_curl = angle_axis(angle_deg, axis)
    
    # Bone 1
    r_t1 = quat_mult(r_t1_rest, q_curl)
    M_t1 = quat_to_matrix(r_t1)
    
    # Bone 2 world in LeftHand
    pos_2 = p_t1 + M_t1 @ p_t2
    r_t2 = quat_mult(r_t2_rest, q_curl)
    M_t2 = quat_to_matrix(quat_mult(r_t1, r_t2))
    
    # Bone 3 world in LeftHand
    pos_3 = pos_2 + M_t2 @ p_t3
    r_t3 = quat_mult(r_t3_rest, q_curl)
    M_t3 = quat_to_matrix(quat_mult(quat_mult(r_t1, r_t2), r_t3))
    
    pos_tip = pos_3 + M_t3 @ p_tip
    return pos_tip

print("Knuckle target area (LeftHandIndex1): [-0.754, -0.012, 0.398]")
print("Rest thumb tip position (angle=0):", eval_thumb_tip([0,0,1], 0.0).round(4))

axes = {
    "+Z (Vector3.forward) [CURRENT]": [0, 0, 1],
    "-Z (Vector3.back)": [0, 0, -1],
    "+Y (Vector3.up)": [0, 1, 0],
    "-Y (Vector3.down)": [0, -1, 0],
    "+X (Vector3.right)": [1, 0, 0],
    "-X (Vector3.left)": [-1, 0, 0],
}

print("\n--- Testing Curl Axes at 65.0 degrees (Left Hand) ---")
for name, ax in axes.items():
    tip = eval_thumb_tip(ax, 65.0)
    print(f"{name:35s}: tip = ({tip[0]:7.4f}, {tip[1]:7.4f}, {tip[2]:7.4f})")
