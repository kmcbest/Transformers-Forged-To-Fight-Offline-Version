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

# Calculate bone-to-parent rest local rotation:
# In Unity bind pose: M_b2w = inv(M_w2b)
# Local transform of bone B relative to parent P:
# M_local = inv(M_parent_b2w) @ M_bone_b2w
for side in ['Left', 'Right']:
    print(f"\n=== {side} Hand Rest Local Rotations ===")
    p_names = [f'{side}Hand', f'{side}HandThumb1', f'{side}HandThumb2']
    b_names = [f'{side}HandThumb1', f'{side}HandThumb2', f'{side}HandThumb3']
    for p_name, b_name in zip(p_names, b_names):
        m_p = np.array([[d['bones'][p_name]['bind_pose_matrix'][f'e{r}{c}'] for c in range(4)] for r in range(4)])
        m_b = np.array([[d['bones'][b_name]['bind_pose_matrix'][f'e{r}{c}'] for c in range(4)] for r in range(4)])
        
        b2w_p = np.linalg.inv(m_p)
        b2w_b = np.linalg.inv(m_b)
        
        m_local = np.linalg.inv(b2w_p) @ b2w_b
        rot_local = R.from_matrix(m_local[:3, :3])
        q = rot_local.as_quat() # x, y, z, w
        euler = rot_local.as_euler('xyz', degrees=True)
        print(f"  {b_name} (parent={p_name}):")
        print(f"    Rest LocalEuler: {np.round(euler, 2)} deg")
        print(f"    Rest LocalRotQ:  ({q[0]:.4f}, {q[1]:.4f}, {q[2]:.4f}, {q[3]:.4f})")
