import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import numpy as np
from scipy.spatial.transform import Rotation as R

with open(r'E:\Agent\TFTF-blender\tools\blitzwing\megatron_51_authoritative_bindposes.json', encoding='utf-8') as f:
    d = json.load(f)

# Let's inspect LeftHandThumb1, 2, 3
for bname in ['LeftHandThumb1', 'LeftHandThumb2', 'LeftHandThumb3']:
    m_data = d['bones'][bname]['bind_pose_matrix']
    m = np.array([[m_data[f'e{r}{c}'] for c in range(4)] for r in range(4)])
    # m is world-to-bone in Unity. Inverse is bone-to-world
    b2w = np.linalg.inv(m)
    rot_b2w = R.from_matrix(b2w[:3, :3])
    print(f"{bname} bind-pose bone-to-world rotation:")
    print("  Euler (degrees, XYZ):", np.round(rot_b2w.as_euler('xyz', degrees=True), 2))
    print("  Local X in world:", np.round(b2w[:3, 0], 4))
    print("  Local Y in world:", np.round(b2w[:3, 1], 4))
    print("  Local Z in world:", np.round(b2w[:3, 2], 4))

# Let's check rest local rotations from hierarchy
# In Unity: bone.localRotation = restRotation * rot
# What is restRotation in Unity?
