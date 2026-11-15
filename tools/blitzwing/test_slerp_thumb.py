import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np
from scipy.spatial.transform import Rotation as R, Slerp

# Left Thumb 1..3
q_rest = [
    R.from_quat([0.2706, 0.6533, -0.2706, 0.6533]),
    R.from_quat([0, 0, 0, 1]),
    R.from_quat([0, 0, 0, 1])
]
q_fist = [
    R.from_quat([0.5221, 0.4741, 0.2509, 0.6631]),
    R.from_quat([-0.0023, -0.3133, 0.3104, 0.8975]),
    R.from_quat([-0.0023, -0.0247, 0.0238, 0.9994])
]

# Right Thumb 1..3
q_R_rest = [
    R.from_quat([-0.2767, 0.6505, 0.2773, 0.6507]),
    R.from_quat([-0.0018, 0, 0, 1]),
    R.from_quat([0.0209, 0, 0, 0.9998])
]
q_R_fist = [
    R.from_quat([0.5296, -0.4735, 0.2517, -0.6573]),
    R.from_quat([-0.0007, 0.2952, 0.3023, -0.9063]),
    R.from_quat([-0.0232, 0.0003, -0.0003, -0.9997])
]

print("=== VERIFYING SLERP PROGRESSION FOR LEFT THUMB ===")
for i in range(3):
    key_times = [0, 1]
    key_rots = R.from_quat([q_rest[i].as_quat(), q_fist[i].as_quat()])
    slerp = Slerp(key_times, key_rots)
    print(f"\nThumb{i+1}:")
    for t in [0.0, 0.25, 0.5, 0.75, 1.0, 1.15]:
        interp_r = slerp(min(t, 1.0))
        euler = interp_r.as_euler('xyz', degrees=True)
        print(f"  t={t:.2f}: Euler={np.round(euler, 1)} deg")

print("\n=== VERIFYING SLERP PROGRESSION FOR RIGHT THUMB ===")
for i in range(3):
    key_times = [0, 1]
    key_rots = R.from_quat([q_R_rest[i].as_quat(), q_R_fist[i].as_quat()])
    slerp = Slerp(key_times, key_rots)
    print(f"\nRight Thumb{i+1}:")
    for t in [0.0, 0.25, 0.5, 0.75, 1.0, 1.15]:
        interp_r = slerp(min(t, 1.0))
        euler = interp_r.as_euler('xyz', degrees=True)
        print(f"  t={t:.2f}: Euler={np.round(euler, 1)} deg")
