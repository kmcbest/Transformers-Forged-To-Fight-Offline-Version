import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import numpy as np
from scipy.spatial.transform import Rotation as R

# Official fist local rotations from Megatron:
# Left Hand:
q_L_t1 = R.from_quat([0.5221, 0.4741, 0.2509, 0.6631]) # x, y, z, w
q_L_t2 = R.from_quat([-0.0023, -0.3133, 0.3104, 0.8975])
q_L_t3 = R.from_quat([-0.0023, -0.0247, 0.0238, 0.9994])

# Right Hand:
q_R_t1 = R.from_quat([0.5393, -0.5064, 0.2712, -0.6158])
q_R_t2 = R.from_quat([-0.0007, 0.2952, 0.3023, -0.9063])
q_R_t3 = R.from_quat([-0.0232, 0.0003, -0.0003, -0.9997])

# Let's inspect the delta rotation from rest:
# restQ from Megatron bindpose:
# Left Thumb1: (0.2706, 0.6533, -0.2706, 0.6533)
q_L_rest_t1 = R.from_quat([0.2706, 0.6533, -0.2706, 0.6533])
q_L_rest_t2 = R.from_quat([0, 0, 0, 1])
q_L_rest_t3 = R.from_quat([0, 0, 0, 1])

# deltaQ: restQ * deltaQ = fistQ  => deltaQ = inv(restQ) * fistQ
delta_L_t1 = q_L_rest_t1.inv() * q_L_t1
delta_L_t2 = q_L_rest_t2.inv() * q_L_t2
delta_L_t3 = q_L_rest_t3.inv() * q_L_t3

print("=== LEFT THUMB DELTA ROTATIONS FROM REST TO FIST ===")
for i, d_q in enumerate([delta_L_t1, delta_L_t2, delta_L_t3], 1):
    axis = d_q.as_rotvec()
    angle_deg = np.linalg.norm(axis) * 180.0 / np.pi
    axis_norm = axis / np.linalg.norm(axis) if angle_deg > 1e-4 else [0,0,0]
    print(f"Thumb{i}: angle={angle_deg:.1f} deg, axis={np.round(axis_norm, 3)}")
    q = d_q.as_quat()
    print(f"  Quat (x,y,z,w): ({q[0]:.4f}, {q[1]:.4f}, {q[2]:.4f}, {q[3]:.4f})")

# Right Hand delta:
q_R_rest_t1 = R.from_quat([-0.2767, 0.6505, 0.2773, 0.6507])
q_R_rest_t2 = R.from_quat([-0.0018, 0, 0, 1])
q_R_rest_t3 = R.from_quat([0.0209, 0, 0, 0.9998])

delta_R_t1 = q_R_rest_t1.inv() * q_R_t1
delta_R_t2 = q_R_rest_t2.inv() * q_R_t2
delta_R_t3 = q_R_rest_t3.inv() * q_R_t3

print("\n=== RIGHT THUMB DELTA ROTATIONS FROM REST TO FIST ===")
for i, d_q in enumerate([delta_R_t1, delta_R_t2, delta_R_t3], 1):
    axis = d_q.as_rotvec()
    angle_deg = np.linalg.norm(axis) * 180.0 / np.pi
    axis_norm = axis / np.linalg.norm(axis) if angle_deg > 1e-4 else [0,0,0]
    print(f"Thumb{i}: angle={angle_deg:.1f} deg, axis={np.round(axis_norm, 3)}")
    q = d_q.as_quat()
    print(f"  Quat (x,y,z,w): ({q[0]:.4f}, {q[1]:.4f}, {q[2]:.4f}, {q[3]:.4f})")
